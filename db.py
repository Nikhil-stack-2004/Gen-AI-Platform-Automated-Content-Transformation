import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash


# =========================================================
# DATABASE LOCATION
# =========================================================

DATABASE = "database/users.db"


# =========================================================
# GET DATABASE CONNECTION
# =========================================================

def get_connection():

    connection = sqlite3.connect(DATABASE)

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():

    connection = get_connection()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS users (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password TEXT NOT NULL,

            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP

        )
    """)

    connection.commit()

    connection.close()


# =========================================================
# CREATE USER
# =========================================================

def create_user(
    username,
    email,
    password
):

    connection = get_connection()

    hashed_password = generate_password_hash(
        password
    )

    connection.execute(
        """
        INSERT INTO users
        (username, email, password)

        VALUES (?, ?, ?)
        """,
        (
            username,
            email,
            hashed_password
        )
    )

    connection.commit()

    connection.close()


# =========================================================
# GET USER BY EMAIL
# =========================================================

def get_user_by_email(email):

    connection = get_connection()

    user = connection.execute(
        """
        SELECT *
        FROM users
        WHERE email = ?
        """,
        (email,)
    ).fetchone()

    connection.close()

    return user


# =========================================================
# VERIFY PASSWORD
# =========================================================

def verify_password(
    password,
    hashed_password
):

    return check_password_hash(
        hashed_password,
        password
    )