from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

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
# ORM imports (models will be created in Step 3)
# ------------------------------------------------------------
from data_models import db, Author, Book

# ------------------------------------------------------------
# Bind SQLAlchemy to the Flask app
# ------------------------------------------------------------
db.init_app(app)
