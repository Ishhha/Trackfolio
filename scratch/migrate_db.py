import sqlite3
import uuid
from datetime import datetime

DB_PATH = "c:/Users/us/OneDrive/Desktop/projects/stock_tracker/stock_tracker/stock_tracker.db"

def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Starting migration...")
    
    # 1. Create users table if not exists
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        hashed_password TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    """)
    print("Ensured 'users' table exists.")
    
    # 2. Check if user_id column exists in portfolios
    cursor.execute("PRAGMA table_info(portfolios)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "user_id" not in columns:
        print("Adding 'user_id' column to 'portfolios'...")
        cursor.execute("ALTER TABLE portfolios ADD COLUMN user_id TEXT")
        conn.commit()
    else:
        print("'user_id' column already exists in 'portfolios'.")
        
    # 3. All portfolios must have a user_id
    # We ensure the column exists and link orphan portfolios to a default user.
    
    # 4. If there are portfolios without a user, create a default user and assign them
    cursor.execute("SELECT COUNT(*) FROM portfolios WHERE user_id IS NULL")
    orphan_count = cursor.fetchone()[0]
    
    if orphan_count > 0:
        print(f"Found {orphan_count} orphan portfolios. Assigning to 'admin' user...")
        
        # Create admin user if not exists
        admin_id = str(uuid.uuid4())
        # Default password is 'admin123' (hashed)
        # Using a dummy hash for now, user should change it or register properly
        dummy_hash = "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGGa31lW" 
        
        try:
            cursor.execute("INSERT INTO users (id, username, hashed_password) VALUES (?, ?, ?)", 
                          (admin_id, "admin", dummy_hash))
        except sqlite3.IntegrityError:
            # Admin already exists, get their ID
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            admin_id = cursor.fetchone()[0]
            
        cursor.execute("UPDATE portfolios SET user_id = ? WHERE user_id IS NULL", (admin_id,))
        print(f"Assigned {orphan_count} portfolios to user 'admin'.")
        
    conn.commit()
    conn.close()
    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
