import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Path to SQLite database file
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "expenses.db")
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Setup engine with thread-safe sqlite settings
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Create session maker
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Declarative base class for models
Base = declarative_base()

def migrate_database():
    """Migrate the database from the old schema format to the new consolidated format."""
    # Recover from expenses_old.db if expenses.db is missing
    if not os.path.exists(DB_PATH):
        old_db_path = os.path.join(os.path.dirname(DB_PATH), "expenses_old.db")
        if os.path.exists(old_db_path):
            import shutil
            try:
                shutil.copy(old_db_path, DB_PATH)
                print("Copied expenses_old.db to expenses.db for migration.")
            except Exception as e:
                print(f"Error copying database: {e}")
                
    if not os.path.exists(DB_PATH):
        return
        
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Migrate users table
    try:
        cursor.execute("PRAGMA table_info(users)")
        columns = {col[1] for col in cursor.fetchall()}
    except sqlite3.OperationalError:
        columns = set()
        
    if columns and "username" not in columns:
        print("Migrating users table...")
        if "name" in columns:
            cursor.execute("ALTER TABLE users RENAME COLUMN name TO username")
        else:
            cursor.execute("ALTER TABLE users ADD COLUMN username VARCHAR UNIQUE")
            
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN password_hash VARCHAR DEFAULT ''")
        except sqlite3.OperationalError:
            pass
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN created_at DATETIME")
        except sqlite3.OperationalError:
            pass
        
        # Check if auth_users exists to copy credentials
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='auth_users'")
            if cursor.fetchone():
                print("Migrating accounts from auth_users to users...")
                cursor.execute("SELECT full_name, email, password_hash, created_at FROM auth_users")
                auth_rows = cursor.fetchall()
                for full_name, email, password_hash, created_at in auth_rows:
                    username = full_name.strip().title()
                    # Check if this username already exists in users
                    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
                    user_exists = cursor.fetchone()
                    if user_exists:
                        cursor.execute("UPDATE users SET password_hash = ?, created_at = ? WHERE username = ?", (password_hash, created_at, username))
                    else:
                        cursor.execute("INSERT INTO users (username, password_hash, created_at) VALUES (?, ?, ?)", (username, password_hash, created_at))
        except sqlite3.OperationalError as e:
            print(f"Error migrating auth_users: {e}")
                    
    # 2. Migrate groups table
    try:
        cursor.execute("PRAGMA table_info(groups)")
        columns = {col[1] for col in cursor.fetchall()}
        if "group_name" in columns:
            cursor.execute("ALTER TABLE groups RENAME COLUMN group_name TO name")
    except sqlite3.OperationalError:
        pass

    # 3. Migrate group_members table
    try:
        cursor.execute("PRAGMA table_info(group_members)")
        columns = {col[1] for col in cursor.fetchall()}
        if "join_date" in columns:
            cursor.execute("ALTER TABLE group_members RENAME COLUMN join_date TO joined_on")
        if "leave_date" in columns:
            cursor.execute("ALTER TABLE group_members RENAME COLUMN leave_date TO left_on")
        if "is_active" in columns:
            if "status" not in columns:
                cursor.execute("ALTER TABLE group_members ADD COLUMN status VARCHAR DEFAULT 'ACTIVE'")
            cursor.execute("UPDATE group_members SET status = 'ACTIVE' WHERE is_active = 1")
            cursor.execute("UPDATE group_members SET status = 'LEFT' WHERE is_active = 0")
            cursor.execute("ALTER TABLE group_members DROP COLUMN is_active")
    except sqlite3.OperationalError:
        pass

    # 4. Migrate expenses table
    try:
        cursor.execute("PRAGMA table_info(expenses)")
        columns = {col[1] for col in cursor.fetchall()}
        if "payer_id" in columns:
            cursor.execute("ALTER TABLE expenses RENAME COLUMN payer_id TO paid_by")
        if "expense_date" in columns:
            cursor.execute("ALTER TABLE expenses RENAME COLUMN expense_date TO date")
        if "notes" not in columns:
            cursor.execute("ALTER TABLE expenses ADD COLUMN notes VARCHAR DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    # 5. Migrate expense_participants table to expense_splits
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='expense_participants'")
        if cursor.fetchone():
            cursor.execute("ALTER TABLE expense_participants RENAME TO expense_splits")
    except sqlite3.OperationalError:
        pass

    # 6. Migrate settlements table
    try:
        cursor.execute("PRAGMA table_info(settlements)")
        columns = {col[1] for col in cursor.fetchall()}
        if "created_at" in columns:
            cursor.execute("ALTER TABLE settlements RENAME COLUMN created_at TO settlement_date")
        if "notes" not in columns:
            cursor.execute("ALTER TABLE settlements ADD COLUMN notes VARCHAR DEFAULT ''")
    except sqlite3.OperationalError:
        pass

    conn.commit()
    conn.close()

def init_db():
    """Create all tables. Enforces SQLite foreign keys at connect time."""
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
        
    migrate_database()
    Base.metadata.create_all(bind=engine)

