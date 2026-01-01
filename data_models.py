from flask_sqlalchemy import SQLAlchemy

# SQLAlchemy instance (bound in app.py via db.init_app(app))
db = SQLAlchemy()

# Placeholder model classes (implemented in Step 3)
class Author(db.Model):
    pass

class Book(db.Model):
    pass
