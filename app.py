"""
Flask Library Application
-------------------------

This application manages a small digital library using Flask + SQLAlchemy.
It supports:

• Adding authors
• Adding books with ISBN/title validation via OpenLibrary
• Displaying all books with sorting and cover images
• Keyword search across titles, authors, and ISBNs
• Deleting books (with optional author deletion if last book)
• Deleting authors (with cascading deletion of their books)
• Safe seeding of 8 authors + 8 books
• ACID‑safe commit/rollback behavior
• Duplicate prevention at DB and application layers (Step 8)
• Full SQLite foreign key enforcement (Step 9)

All features from Steps 1–9 are implemented.
"""

from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, date
import requests
import sqlite3
from sqlalchemy import event
from sqlalchemy.engine import Engine

from data_models import db, Author, Book  # noqa: E402


# ---------------------------------------------------------------------------
# Enforce SQLite Foreign Keys (ACID requirement)
# ---------------------------------------------------------------------------
@event.listens_for(Engine, "connect")
def enforce_foreign_keys(dbapi_connection, connection_record):
    """
    Ensures SQLite enforces foreign key constraints.

    Required for:
        • ON DELETE CASCADE
        • Referential integrity
        • ACID-safe deletes
    """
    if isinstance(dbapi_connection, sqlite3.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


# ---------------------------------------------------------------------------
# Application Setup
# ---------------------------------------------------------------------------
app = Flask(__name__)

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "data", "library.sqlite")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def parse_date(value):
    """
    Convert a YYYY-MM-DD string from HTML <input type="date"> into a Python date.

    Args:
        value (str): Date string or None.

    Returns:
        datetime.date or None: Parsed date or None if empty.
    """
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def fetch_cover_image(isbn):
    """
    Construct the OpenLibrary cover image URL for a given ISBN.

    Args:
        isbn (str): ISBN-10 or ISBN-13.

    Returns:
        str: URL to the medium-sized cover image.
    """
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"


def validate_isbn_title(isbn, title):
    """
    Validate that an ISBN corresponds to the expected title using OpenLibrary.

    PATCHED BEHAVIOR:
    -----------------
    OpenLibrary does NOT index all legitimate ISBNs.
    Many valid commercial editions return 404 even though the ISBN is real.

    New behavior:
        • If OpenLibrary returns a valid record → enforce strict title match.
        • If OpenLibrary returns 404 → ALLOW the ISBN and trust user input.
        • If OpenLibrary is unreachable → ALLOW the ISBN.
    """
    url = f"https://openlibrary.org/isbn/{isbn}.json"

    try:
        response = requests.get(url, timeout=5)
    except requests.RequestException:
        return True, None

    if response.status_code != 200:
        return True, None

    data = response.json()
    ol_title = data.get("title", "")

    if not ol_title:
        return True, None

    if ol_title.strip().lower() != title.strip().lower():
        return False, (
            f"Title '{title}' does not match OpenLibrary title '{ol_title}' "
            f"for this ISBN."
        )

    return True, None


# ---------------------------------------------------------------------------
# Route: Add Author
# ---------------------------------------------------------------------------
@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    """
    Display a form to add a new author and handle form submission.

    GET:
        Render the add_author.html form.

    POST:
        • Validate required fields.
        • Application-level duplicate check (case-insensitive name).
        • Create an Author row and commit to DB.
        • Show a success or duplicate-warning message.
    """
    message = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        birth_date_raw = request.form.get("birthdate")
        date_of_death_raw = request.form.get("date_of_death")

        if not name or not birth_date_raw:
            message = "Name and birthdate are required."
        else:
            existing = Author.query.filter(
                db.func.lower(Author.name) == name.lower()
            ).first()

            if existing:
                message = f"Author '{name}' already exists."
            else:
                birth_date = parse_date(birth_date_raw)
                date_of_death = parse_date(date_of_death_raw)

                new_author = Author(
                    name=name,
                    birth_date=birth_date,
                    date_of_death=date_of_death,
                )

                db.session.add(new_author)
                db.session.commit()

                message = f"Author '{name}' added successfully."

    return render_template("add_author.html", message=message)


# ---------------------------------------------------------------------------
# Route: Add Book
# ---------------------------------------------------------------------------
@app.route("/add_book", methods=["GET", "POST"])
def add_book():
    """
    Display a form to add a new book and handle form submission.

    GET:
        Render the add_book.html form with author dropdown.

    POST:
        • Validate fields.
        • Duplicate ISBN check.
        • Duplicate title per author check.
        • Validate ISBN/title via OpenLibrary.
        • Insert new Book row and commit.
    """
    message = None
    authors = Author.query.order_by(Author.name).all()

    if request.method == "POST":
        isbn = request.form.get("isbn", "").strip()
        title = request.form.get("title", "").strip()
        publication_year_raw = request.form.get("publication_year")
        author_id_raw = request.form.get("author_id")

        if not (isbn and title and publication_year_raw and author_id_raw):
            message = "All fields are required."
        else:
            try:
                publication_year = int(publication_year_raw)
                author_id = int(author_id_raw)
            except ValueError:
                message = "Publication year and author must be valid."
            else:
                existing_isbn = Book.query.filter_by(isbn=isbn).first()
                if existing_isbn:
                    message = f"A book with ISBN {isbn} already exists."
                else:
                    existing_title = Book.query.filter(
                        db.func.lower(Book.title) == title.lower(),
                        Book.author_id == author_id,
                    ).first()

                    if existing_title:
                        message = (
                            f"The author already has a book titled '{title}'."
                        )
                    else:
                        ok, error_msg = validate_isbn_title(isbn, title)
                        if not ok:
                            message = error_msg
                        else:
                            new_book = Book(
                                isbn=isbn,
                                title=title,
                                publication_year=publication_year,
                                author_id=author_id,
                            )
                            db.session.add(new_book)
                            db.session.commit()
                            message = f"Book '{title}' added successfully."

    return render_template("add_book.html", authors=authors, message=message)


# ---------------------------------------------------------------------------
# Route: Home (Search + Sorting + Messages)
# ---------------------------------------------------------------------------
@app.route("/")
def home():
    """
    Display the library homepage with:

    • Keyword search across title, author, and ISBN
    • Sorting by title, author, or year
    • Success/error messages from delete operations
    • Book list with cover images
    """
    search = request.args.get("search", "").strip()
    sort = request.args.get("sort", "title")
    message = request.args.get("message", "")

    query = Book.query.join(Author)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(
            db.or_(
                Book.title.ilike(like_pattern),
                Author.name.ilike(like_pattern),
                Book.isbn.ilike(like_pattern),
            )
        )

    if sort == "author":
        query = query.order_by(Author.name)
    elif sort == "year":
        query = query.order_by(Book.publication_year)
    else:
        query = query.order_by(Book.title)

    books = query.all()
    no_results = bool(search and not books)

    return render_template(
        "home.html",
        books=books,
        sort=sort,
        search=search,
        no_results=no_results,
        message=message,
    )


# ---------------------------------------------------------------------------
# Route: Delete Book
# ---------------------------------------------------------------------------
@app.route("/book/<int:book_id>/delete", methods=["POST"])
def delete_book(book_id):
    """
    Delete a specific book in one of two modes:

    Modes:
        • mode=book
            Delete only the selected book.

        • mode=book_and_author
            Delete the selected book AND delete the author if this is the
            author's last remaining book.

    Behavior:
        • Uses a single ACID-safe transaction with commit/rollback.
        • Redirects back to the homepage with a status message.
    """
    mode = request.args.get("mode", "book")

    book = Book.query.get_or_404(book_id)
    author = book.author
    author_book_count = Book.query.filter_by(author_id=author.id).count()

    try:
        if mode == "book":
            db.session.delete(book)
            msg = f"Book '{book.title}' deleted."

        elif mode == "book_and_author":
            db.session.delete(book)

            if author_book_count == 1:
                db.session.delete(author)
                msg = (
                    f"Book '{book.title}' and author '{author.name}' deleted."
                )
            else:
                msg = (
                    f"Book '{book.title}' deleted, but author "
                    f"'{author.name}' has other books."
                )

        db.session.commit()

    except Exception:
        db.session.rollback()
        msg = "An error occurred while deleting the book."

    return redirect(url_for("home", message=msg))


# ---------------------------------------------------------------------------
# Route: Delete Author
# ---------------------------------------------------------------------------
@app.route("/author/<int:author_id>/delete", methods=["POST"])
def delete_author(author_id):
    """
    Delete an author and all their books.

    Behavior:
        • Uses SQLAlchemy cascade='all, delete-orphan'
        • ACID-safe commit/rollback
        • Redirects back to the homepage with a status message
    """
    author = Author.query.get_or_404(author_id)

    try:
        db.session.delete(author)
        db.session.commit()
        msg = f"Author '{author.name}' and all their books deleted."
    except Exception:
        db.session.rollback()
        msg = "An error occurred while deleting the author."

    return redirect(url_for("home", message=msg))


# ---------------------------------------------------------------------------
# Route: Seed Data
# ---------------------------------------------------------------------------
@app.route("/seed")
def seed():
    """
    Seed the database with 8 authors and 8 books.

    Behavior:
        • Safe insert: does not duplicate existing rows
        • Ensures all authors exist before inserting books
        • Supports reseeding after partial deletions
    """
    authors_to_seed = [
        ("Isaac Asimov", date(1920, 1, 2), date(1992, 4, 6)),
        ("Frank Herbert", date(1920, 10, 8), date(1986, 2, 11)),
        ("Alex Haley", date(1921, 8, 11), date(1965, 2, 21)),
        ("Mary Shelley", date(1797, 8, 30), date(1851, 2, 1)),
        ("J.R.R. Tolkien", date(1892, 1, 3), date(1973, 9, 2)),
        ("George Orwell", date(1903, 6, 25), date(1950, 1, 21)),
        ("Harper Lee", date(1926, 4, 28), date(2016, 2, 19)),
        ("J. D. Salinger", date(1919, 1, 1), date(2010, 1, 27)),
    ]

    for name, birth, death in authors_to_seed:
        existing = Author.query.filter_by(name=name).first()
        if not existing:
            db.session.add(Author(name=name, birth_date=birth, date_of_death=death))

    db.session.commit()

    authors_by_name = {a.name: a for a in Author.query.all()}

    books_to_seed = [
        ("9780553293357", "Foundation", 1951, "Isaac Asimov"),
        ("9780441172719", "Dune", 1965, "Frank Herbert"),
        (
            "9780345350688",
            "The Autobiography of Malcolm X: As Told to Alex Haley",
            1992,
            "Alex Haley",
        ),
        ("9780486282114", "Frankenstein", 1818, "Mary Shelley"),
        (
            "9780547928227",
            "The Hobbit: Or, There and Back Again",
            1937,
            "J.R.R. Tolkien",
        ),
        ("9780141036144", "1984", 1949, "George Orwell"),
        ("9780061120084", "To Kill a Mockingbird", 1960, "Harper Lee"),
        ("9780241950432", "The Catcher in the Rye", 1951, "J. D. Salinger"),
    ]

    for isbn, title, year, author_name in books_to_seed:
        existing = Book.query.filter_by(isbn=isbn).first()
        if not existing:
            db.session.add(
                Book(
                    isbn=isbn,
                    title=title,
                    publication_year=year,
                    author_id=authors_by_name[author_name].id,
                )
            )

    db.session.commit()

    return "Seed data inserted. Go back to / to see the library."


# ---------------------------------------------------------------------------
# Application Entrypoint
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    """
    Application entrypoint.

    Behavior:
        • Ensures all tables exist (db.create_all)
        • Runs Flask development server on port 5002
    """
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5002, debug=True)
