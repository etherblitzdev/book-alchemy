"""
Data Models for Library Application
-----------------------------------

Defines the SQLAlchemy ORM models for Authors and Books.

ACID constraints:
• Author.name is UNIQUE (prevents duplicate authors)
• Book.isbn is UNIQUE (prevents duplicate editions)
• (Book.title, Book.author_id) is UNIQUE (prevents duplicate titles per author)
• ON DELETE CASCADE ensures deleting an author removes all their books
• delete-orphan ensures no orphaned Book rows remain
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint, ForeignKey
from sqlalchemy.orm import relationship

db = SQLAlchemy()


# ---------------------------------------------------------------------------
# Model: Author
# ---------------------------------------------------------------------------
class Author(db.Model):
    """
    Author model.

    Constraints:
        • name is UNIQUE to prevent duplicate authors
        • cascade='all, delete-orphan' ensures deleting an author removes all books
        • passive_deletes=True enables ON DELETE CASCADE in SQLite
    """
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    birth_date = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date, nullable=True)

    books = relationship(
        "Book",
        backref="author",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<Author id={self.id} name='{self.name}'>"


# ---------------------------------------------------------------------------
# Model: Book
# ---------------------------------------------------------------------------
class Book(db.Model):
    """
    Book model.

    Constraints:
        • isbn is UNIQUE (each edition is unique)
        • (title, author_id) is UNIQUE (prevents duplicate titles for same author)
        • author_id uses ON DELETE CASCADE to enforce referential integrity
    """
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20), nullable=False, unique=True)
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)

    author_id = db.Column(
        db.Integer,
        ForeignKey("authors.id", ondelete="CASCADE"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("title", "author_id", name="uq_title_author"),
    )

    def __repr__(self):
        return f"<Book id={self.id} title='{self.title}'>"
