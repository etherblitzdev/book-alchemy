#!/bin/bash

set -e

DB_PATH="book-alchemy/data/library.sqlite"

echo "Resetting SQLite database..."

if [ -f "$DB_PATH" ]; then
  rm "$DB_PATH"
  echo "Deleted existing database."
else
  echo "No existing database found."
fi

echo "Recreating database schema..."
python3 - << 'EOF'
from app import app, db
with app.app_context():
    db.create_all()
EOF

echo "Database reset complete. Visit /seed to repopulate baseline data."
