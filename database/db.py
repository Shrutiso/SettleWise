import sqlite3
import os
import uuid
from datetime import datetime

# Absolute path — expenses.db always in project root
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "expenses.db")


def get_connection():
    """Return a connection to the SQLite database with dict-like rows."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create all 10 tables. Called once at app startup."""
    conn = get_connection()
    c = conn.cursor()

    # 1. Users
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)

    # 2. Groups
    c.execute("""
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_name TEXT NOT NULL,
            description TEXT DEFAULT '',
            currency TEXT DEFAULT 'INR',
            created_by INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # 3. Group Members — with join_date/leave_date for Sam scenario
    c.execute("""
        CREATE TABLE IF NOT EXISTS group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            join_date TEXT NOT NULL DEFAULT (date('now')),
            leave_date TEXT DEFAULT NULL,
            is_active INTEGER DEFAULT 1,
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(group_id, user_id)
        )
    """)

    # 4. Expenses — with currency and split_type
    c.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            payer_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'INR',
            description TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            split_type TEXT DEFAULT 'equal',
            expense_date TEXT NOT NULL,
            source TEXT DEFAULT 'manual',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY (payer_id) REFERENCES users(id)
        )
    """)
    try:
        c.execute("ALTER TABLE expenses ADD COLUMN source TEXT DEFAULT 'manual'")
    except sqlite3.OperationalError:
        pass

    # 5. Expense Splits
    c.execute("""
        CREATE TABLE IF NOT EXISTS expense_splits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            share_amount REAL NOT NULL,
            share_percentage REAL DEFAULT NULL,
            FOREIGN KEY (expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(expense_id, user_id)
        )
    """)

    # 6. Exchange Rates — for Priya scenario
    c.execute("""
        CREATE TABLE IF NOT EXISTS exchange_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_currency TEXT NOT NULL,
            to_currency TEXT NOT NULL,
            rate REAL NOT NULL,
            updated_at TEXT DEFAULT (datetime('now')),
            UNIQUE(from_currency, to_currency)
        )
    """)

    # 7. Settlements — for Aisha scenario
    c.execute("""
        CREATE TABLE IF NOT EXISTS settlements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            payer_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            currency TEXT DEFAULT 'INR',
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY (payer_id) REFERENCES users(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    """)

    # 8. Import Logs — audit trail
    c.execute("""
        CREATE TABLE IF NOT EXISTS import_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            import_batch_id TEXT NOT NULL,
            group_id INTEGER,
            row_number INTEGER,
            issue_type TEXT NOT NULL,
            original_value TEXT,
            action_taken TEXT NOT NULL,
            timestamp TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (group_id) REFERENCES groups(id)
        )
    """)

    # 9. Approval Requests — for Meera duplicate approval
    c.execute("""
        CREATE TABLE IF NOT EXISTS approval_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            expense_id INTEGER,
            duplicate_of_id INTEGER,
            request_type TEXT DEFAULT 'duplicate_removal',
            status TEXT DEFAULT 'pending',
            details TEXT,
            requested_by INTEGER,
            reviewed_by INTEGER,
            created_at TEXT DEFAULT (datetime('now')),
            reviewed_at TEXT,
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY (expense_id) REFERENCES expenses(id),
            FOREIGN KEY (requested_by) REFERENCES users(id),
            FOREIGN KEY (reviewed_by) REFERENCES users(id)
        )
    """)

    # 10. Balances cache
    c.execute("""
        CREATE TABLE IF NOT EXISTS balances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount_owed REAL DEFAULT 0,
            amount_receivable REAL DEFAULT 0,
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (group_id) REFERENCES groups(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(group_id, user_id)
        )
    """)

    # Seed exchange rates
    rates = [
        ('USD', 'INR', 83.0),
        ('EUR', 'INR', 90.5),
        ('GBP', 'INR', 105.0),
        ('JPY', 'INR', 0.56),
        ('AUD', 'INR', 55.0),
        ('CAD', 'INR', 62.0),
        ('INR', 'INR', 1.0),
    ]
    for fr, to, rate in rates:
        c.execute("""
            INSERT OR IGNORE INTO exchange_rates (from_currency, to_currency, rate)
            VALUES (?, ?, ?)
        """, (fr, to, rate))

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def fetch_one(query, params=()):
    conn = get_connection()
    row = conn.execute(query, params).fetchone()
    conn.close()
    return dict(row) if row else None


def fetch_all(query, params=()):
    conn = get_connection()
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def execute(query, params=()):
    conn = get_connection()
    c = conn.cursor()
    c.execute(query, params)
    conn.commit()
    last_id = c.lastrowid
    conn.close()
    return last_id


def execute_many(query, params_list):
    conn = get_connection()
    conn.executemany(query, params_list)
    conn.commit()
    conn.close()


def generate_batch_id():
    """Generate a unique import batch ID."""
    return str(uuid.uuid4())[:8]