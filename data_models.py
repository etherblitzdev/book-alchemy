from flask_sqlalchemy import SQLAlchemy

# ------------------------------------------------------------
# SQLAlchemy instance (bound to Flask app in app.py)
# ------------------------------------------------------------
db = SQLAlchemy()


# ------------------------------------------------------------
# Author model
# ------------------------------------------------------------
class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    date_of_death = db.Column(db.Date, nullable=True)

    # Relationship: one author -> many books
    books = db.relationship("Book", backref="author", lazy=True)

    def __repr__(self):
        return (
            f"<Author id={self.id} name='{self.name}' "
            f"birth_date={self.birth_date} "
            f"date_of_death={self.date_of_death}>"
        )

    def __str__(self):
        return f"{self.name} (born {self.birth_date})"


# ------------------------------------------------------------
# Book model
# ------------------------------------------------------------
class Book(db.Model):
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20), nullable=False, unique=True)
    title = db.Column(db.String(200), nullable=False)
    publication_year = db.Column(db.Integer, nullable=False)

    # Foreign key to Author
    author_id = db.Column(db.Integer, db.ForeignKey("authors.id"), nullable=False)

    def __repr__(self):
        return (
            f"<Book id={self.id} isbn='{self.isbn}' "
            f"title='{self.title}' year={self.publication_year} "
            f"author_id={self.author_id}>"
        )

    def __str__(self):
        return f"{self.title} ({self.publication_year})"


# ------------------------------------------------------------
# Table creation (run once, then comment out)
# ------------------------------------------------------------
# from app import app
# with app.app_context():
#     db.create_all()
