"""
Authentication module for SplitBee / SettleWise.
Handles login, registration, password hashing, and session management.
"""
import hashlib
from database.db import fetch_one, execute


def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def create_user(username, password):
    """
    Register a new user.
    Returns (True, user_id) on success, (False, error_message) on failure.
    """
    username = username.strip()
    if not username:
        return False, "Username cannot be empty."
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if not password:
        return False, "Password cannot be empty."
    if len(password) < 4:
        return False, "Password must be at least 4 characters."

    existing = fetch_one("SELECT id, password_hash FROM users WHERE username = ?", (username,))
    if existing:
        # Allow claiming a pre-created account from CSV import with no password set
        if not existing["password_hash"]:
            pw_hash = hash_password(password)
            execute(
                "UPDATE users SET password_hash = ?, created_at = datetime('now') WHERE id = ?",
                (pw_hash, existing["id"])
            )
            return True, existing["id"]
        return False, f"Username '{username}' is already taken."

    pw_hash = hash_password(password)
    user_id = execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, pw_hash)
    )
    return True, user_id


def login_user(username, password):
    """
    Authenticate a user. Returns user dict on success, None on failure.
    """
    user = fetch_one("SELECT * FROM users WHERE username = ?", (username.strip(),))
    if user is None:
        return None
    if user["password_hash"] != hash_password(password):
        return None
    return user


def verify_user(user_id):
    """Check if a user_id exists. Returns user dict or None."""
    return fetch_one("SELECT * FROM users WHERE id = ?", (user_id,))


def get_current_user(st):
    """Get the current logged-in user from session state."""
    if not st.session_state.get("logged_in"):
        return None
    return {
        "id": st.session_state.get("user_id"),
        "username": st.session_state.get("username"),
    }


def get_all_users():
    """Return list of all users."""
    from database.db import fetch_all
    return fetch_all("SELECT id, username, created_at FROM users ORDER BY username")


def logout_user(st):
    """Clear session state."""
    for key in ["authenticated", "user_id", "user_name", "user_email", "logged_in", "username"]:
        st.session_state.pop(key, None)


def seed_demo_user():
    """Create demo user admin/admin123 if it doesn't exist."""
    existing = fetch_one("SELECT id FROM users WHERE username = ?", ("admin",))
    if not existing:
        execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            ("admin", hash_password("admin123"))
        )


# =====================================================
# Compatibility Wrappers for app.py
# =====================================================

def signup(username, password):
    """
    Register a new user (compatibility wrapper).
    Returns (success, message, user_dict or None).
    """
    username = username.strip().title()  # Normalize to match dynamic CSV users
    success, result = create_user(username, password)
    if success:
        # Retrieve user info to return user_data
        user = login_user(username, password)
        return True, "Account registered successfully!", {
            "id": user["id"],
            "full_name": user["username"],
            "email": user["username"],
        }
    else:
        return False, result, None


def login(username, password):
    """
    Authenticate a user (compatibility wrapper).
    Returns (success, message, user_dict or None).
    """
    username = username.strip().title()
    user = login_user(username, password)
    if user:
        return True, "Login successful!", {
            "id": user["id"],
            "full_name": user["username"],
            "email": user["username"],
        }
    else:
        # Check if user exists in database but has no password (pre-created via CSV)
        existing = fetch_one("SELECT id, password_hash FROM users WHERE username = ?", (username,))
        if existing:
            if not existing["password_hash"]:
                return False, "This member exists in database but has not registered an account yet.", None
            else:
                return False, "Incorrect password.", None
        return False, "No account found with this username.", None
