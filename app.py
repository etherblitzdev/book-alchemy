from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, date
import requests

# ------------------------------------------------------------
# Flask application initialization
# ------------------------------------------------------------
app = Flask(__name__)

# ------------------------------------------------------------
# Absolute SQLite path resolution
# ------------------------------------------------------------
basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, "data", "library.sqlite")

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ------------------------------------------------------------
# ORM imports
# ------------------------------------------------------------
from data_models import db, Author, Book  # noqa: E402

# ------------------------------------------------------------
# Bind SQLAlchemy to the Flask app
# ------------------------------------------------------------
db.init_app(app)


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def fetch_cover_image(isbn):
    return f"https://covers.openlibrary.org/b/isbn/{isbn}-M.jpg"


def validate_isbn_title(isbn, title):
    """
    Validate ISBN → title using OpenLibrary.
    """
    url = f"https://openlibrary.org/isbn/{isbn}.json"
    try:
        response = requests.get(url, timeout=5)
    except requests.RequestException:
        return False, "Could not reach OpenLibrary to validate ISBN."

    if response.status_code != 200:
        return False, "No book found for the given ISBN."

    data = response.json()
    ol_title = data.get("title", "")

    if not ol_title:
        return False, "OpenLibrary did not return a title for this ISBN."

    if ol_title.strip().lower() != title.strip().lower():
        return False, (
            f"Title '{title}' does not match OpenLibrary title '{ol_title}' "
            f"for this ISBN."
        )

    return True, None


# ------------------------------------------------------------
# Route: Add Author
# ------------------------------------------------------------
@app.route("/add_author", methods=["GET", "POST"])
def add_author():
    message = None

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        birth_date_raw = request.form.get("birthdate")
        date_of_death_raw = request.form.get("date_of_death")

        if not name or not birth_date_raw:
            message = "Name and birthdate are required."
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


# ------------------------------------------------------------
# Route: Add Book
# ------------------------------------------------------------
@app.route("/add_book", methods=["GET", "POST"])
def add_book():
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


# ------------------------------------------------------------
# Route: Home Page
# ------------------------------------------------------------
@app.route("/")
def home():
    sort = request.args.get("sort", "title")

    if sort == "author":
        books = Book.query.join(Author).order_by(Author.name).all()
    elif sort == "year":
        books = Book.query.order_by(Book.publication_year).all()
    else:
        books = Book.query.order_by(Book.title).all()

    return render_template("home.html", books=books, sort=sort)


# ------------------------------------------------------------
# Route: Seed Data (8 authors + 8 books)
# Works whether DB is empty OR already contains the first 4 rows
# ------------------------------------------------------------
@app.route("/seed")
def seed():
    # ---------- AUTHORS ----------
    authors_to_seed = [
        # Existing 4 (IDs 1–4)
        ("Isaac Asimov", date(1920, 1, 2), date(1992, 4, 6)),
        ("Frank Herbert", date(1920, 10, 8), date(1986, 2, 11)),
        ("Alex Haley", date(1921, 8, 11), date(1965, 2, 21)),
        ("Mary Shelley", date(1797, 8, 30), date(1851, 2, 1)),

        # New 4 (IDs 5–8) — Jane Austen removed
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

    # ---------- BOOKS ----------
    books_to_seed = [
        # Existing 4
        ("9780553293357", "Foundation", 1951, "Isaac Asimov"),
        ("9780441172719", "Dune", 1965, "Frank Herbert"),
        ("9780345350688", "The Autobiography of Malcolm X: As Told to Alex Haley", 1992, "Alex Haley"),
        ("9780486282114", "Frankenstein", 1818, "Mary Shelley"),

        # New 4 — Pride and Prejudice removed
        ("9780547928227", "The Hobbit: Or, There and Back Again", 1937, "J.R.R. Tolkien"),
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


# ------------------------------------------------------------
# Application entrypoint
# ------------------------------------------------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5002, debug=True)
