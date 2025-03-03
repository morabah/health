import sqlite3
import os

# Path to the database file
db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'instance', 'health_app.db')

def migrate():
    """Add missing columns to the doctors table."""
    print(f"Migrating database at: {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns exist before adding them
    cursor.execute("PRAGMA table_info(doctors)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Add missing columns if they don't exist
    if 'location' not in columns:
        print("Adding 'location' column to doctors table")
        cursor.execute("ALTER TABLE doctors ADD COLUMN location TEXT")
    
    if 'languages' not in columns:
        print("Adding 'languages' column to doctors table")
        cursor.execute("ALTER TABLE doctors ADD COLUMN languages TEXT")
    
    if 'consultation_fee' not in columns:
        print("Adding 'consultation_fee' column to doctors table")
        cursor.execute("ALTER TABLE doctors ADD COLUMN consultation_fee REAL")
    
    if 'profile_picture' not in columns:
        print("Adding 'profile_picture' column to doctors table")
        cursor.execute("ALTER TABLE doctors ADD COLUMN profile_picture TEXT")
    
    # Commit the changes
    conn.commit()
    conn.close()
    
    print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
