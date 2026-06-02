import sys
import os

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine
from sqlmodel import text

def migrate():
    print("Migrating stock_entries table to add state column...")
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE stock_entries ADD COLUMN state VARCHAR DEFAULT 'ready' NOT NULL"))
            print("Successfully added 'state' column.")
        except Exception as e:
            if "duplicate column name" in str(e).lower():
                print("Column 'state' already exists.")
            else:
                print(f"Error migrating: {e}")

if __name__ == "__main__":
    migrate()
