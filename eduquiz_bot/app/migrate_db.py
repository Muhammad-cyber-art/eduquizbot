import os
import shutil
import sqlite3

def run_migration():
    db_path = os.path.join(os.path.dirname(__file__), "eduquiz.db")
    if not os.path.exists(db_path):
        # Fallback to current directory or parent directory
        db_path = "eduquiz.db"
        if not os.path.exists(db_path):
            db_path = "../eduquiz.db"
            if not os.path.exists(db_path):
                print("Database file eduquiz.db not found!")
                return

    db_path = os.path.abspath(db_path)
    backup_path = db_path + ".bak"
    
    print(f"Database path: {db_path}")
    print(f"Creating backup at: {backup_path}")
    shutil.copy2(db_path, backup_path)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Disable foreign key checks temporarily
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # Start transaction
        cursor.execute("BEGIN TRANSACTION;")
        
        # 1. Migrate options table
        print("Migrating options table...")
        cursor.execute("ALTER TABLE options RENAME TO options_old;")
        
        cursor.execute("""
            CREATE TABLE options (
                id INTEGER NOT NULL, 
                question_id INTEGER NOT NULL, 
                label VARCHAR(1) NOT NULL, 
                text TEXT NOT NULL, 
                is_correct BOOLEAN NOT NULL, 
                PRIMARY KEY (id), 
                UNIQUE (question_id, label), 
                CONSTRAINT ck_option_label CHECK (label IN ('A','B','C','D','E','F','G','H','I','J')), 
                FOREIGN KEY(question_id) REFERENCES questions (id) ON DELETE CASCADE
            );
        """)
        
        cursor.execute("""
            INSERT INTO options (id, question_id, label, text, is_correct)
            SELECT id, question_id, label, text, is_correct FROM options_old;
        """)
        
        cursor.execute("DROP TABLE options_old;")
        
        # 2. Migrate answers table
        print("Migrating answers table...")
        cursor.execute("ALTER TABLE answers RENAME TO answers_old;")
        
        cursor.execute("""
            CREATE TABLE answers (
                id INTEGER NOT NULL, 
                attempt_id INTEGER NOT NULL, 
                question_id INTEGER NOT NULL, 
                selected_label VARCHAR(1) NOT NULL, 
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
                PRIMARY KEY (id), 
                UNIQUE (attempt_id, question_id), 
                CONSTRAINT ck_answer_label CHECK (selected_label IN ('A','B','C','D','E','F','G','H','I','J')), 
                FOREIGN KEY(attempt_id) REFERENCES attempts (id) ON DELETE CASCADE, 
                FOREIGN KEY(question_id) REFERENCES questions (id) ON DELETE CASCADE
            );
        """)
        
        cursor.execute("""
            INSERT INTO answers (id, attempt_id, question_id, selected_label, created_at)
            SELECT id, attempt_id, question_id, selected_label, created_at FROM answers_old;
        """)
        
        cursor.execute("DROP TABLE answers_old;")
        
        # Commit transaction
        conn.commit()
        print("Migration transaction committed successfully.")
        
        # Run foreign key check
        fk_violations = cursor.execute("PRAGMA foreign_key_check;").fetchall()
        if fk_violations:
            print(f"WARNING: Foreign key violations detected! {fk_violations}")
        else:
            print("Foreign key check passed.")
            
    except Exception as e:
        conn.rollback()
        print(f"An error occurred during migration: {e}")
        print("Transaction rolled back. Restoring database from backup...")
        conn.close()
        shutil.copy2(backup_path, db_path)
        print("Database restored.")
        return
        
    finally:
        # Re-enable foreign key checks
        try:
            cursor.execute("PRAGMA foreign_keys = ON;")
            conn.close()
        except Exception:
            pass

    print("Migration completed successfully!")

if __name__ == "__main__":
    run_migration()
