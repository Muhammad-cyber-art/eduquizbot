import sqlite3
import os

def migrate():
    # Database path check
    db_paths = ["eduquiz.db", "eduquiz_bot/eduquiz.db", "../eduquiz.db"]
    db_path = None
    for path in db_paths:
        if os.path.exists(path):
            db_path = path
            break

    if not db_path:
        db_path = "eduquiz_bot/eduquiz.db"

    print(f"Migrating SQLite database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop organizations table
    try:
        cursor.execute("DROP TABLE IF EXISTS organizations")
        print("Dropped organizations table.")
    except Exception as e:
        print("Error dropping organizations table:", e)

    # Helper function to add column if not exists
    def add_column(table_name, column_def):
        col_name = column_def.split()[0]
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_def}")
            print(f"Added column '{col_name}' to table '{table_name}'.")
        except sqlite3.OperationalError as e:
            # OperationalError is raised if column already exists in SQLite
            if "duplicate column name" in str(e).lower() or "already exists" in str(e).lower():
                print(f"Column '{col_name}' already exists in table '{table_name}'.")
            else:
                print(f"Error adding '{col_name}' to '{table_name}': {e}")

    # Add columns to users
    add_column("users", "max_tests INTEGER DEFAULT 5 NOT NULL")
    add_column("users", "max_students INTEGER DEFAULT 50 NOT NULL")
    add_column("users", "is_active INTEGER DEFAULT 1 NOT NULL")
    add_column("users", "expires_at DATETIME")

    # Add columns to access_requests
    add_column("access_requests", "max_tests INTEGER DEFAULT 5 NOT NULL")
    add_column("access_requests", "max_students INTEGER DEFAULT 50 NOT NULL")
    add_column("access_requests", "expires_at DATETIME")

    # Add columns to teacher_invite_codes
    add_column("teacher_invite_codes", "max_tests INTEGER DEFAULT 5 NOT NULL")
    add_column("teacher_invite_codes", "max_students INTEGER DEFAULT 50 NOT NULL")
    add_column("teacher_invite_codes", "expires_at DATETIME")

    conn.commit()
    conn.close()
    print("Database Plan B migration completed.")

if __name__ == "__main__":
    migrate()
