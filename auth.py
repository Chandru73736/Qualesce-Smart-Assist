import sqlite3
import bcrypt

# ---------------- Create DB Table ----------------
def create_user_table():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY,
            password BLOB
        )
    """)
    conn.commit()
    conn.close()

# ---------------- Add User ----------------
def add_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

    try:
        c.execute("INSERT INTO users(username,password) VALUES (?,?)",
                  (username, hashed))
        conn.commit()
        return True
    except:
        return False
    finally:
        conn.close()

# ---------------- Login User ----------------
def login_user(username, password):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()

    c.execute("SELECT password FROM users WHERE username=?", (username,))
    data = c.fetchone()
    conn.close()

    if data:
        return bcrypt.checkpw(password.encode(), data[0])
    return False
