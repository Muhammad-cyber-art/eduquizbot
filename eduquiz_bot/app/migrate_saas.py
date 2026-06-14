import sqlite3
import os

def migrate():
    # Database is located at eduquiz_bot/eduquiz.db relative to the workspace root,
    # or just eduquiz.db inside the eduquiz_bot folder. Let's check both paths.
    db_paths = ["eduquiz.db", "eduquiz_bot/eduquiz.db", "../eduquiz.db"]
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break

    if db_path:
        print(f"Migrating SQLite database at {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Add org_id to access_requests
        try:
            cursor.execute("ALTER TABLE access_requests ADD COLUMN org_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL")
            print("Successfully added org_id column to access_requests table.")
        except sqlite3.OperationalError as e:
            print("access_requests org_id column already exists or table issue:", e)
            
        # Add org_id to teacher_invite_codes
        try:
            cursor.execute("ALTER TABLE teacher_invite_codes ADD COLUMN org_id INTEGER REFERENCES organizations(id) ON DELETE SET NULL")
            print("Successfully added org_id column to teacher_invite_codes table.")
        except sqlite3.OperationalError as e:
            print("teacher_invite_codes org_id column already exists or table issue:", e)
            
        conn.commit()
        conn.close()
        print("Database migration completed.")
    else:
        print("Warning: Database file not found. Skipping migration (will be created automatically on startup).")

if __name__ == "__main__":
    migrate()
