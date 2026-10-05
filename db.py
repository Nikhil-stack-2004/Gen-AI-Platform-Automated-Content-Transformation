import sqlite3
import os

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =========================================================
# DATABASE CONFIGURATION
# =========================================================

DATABASE_DIR = "database"
DATABASE_FILE = os.path.join(
    DATABASE_DIR,
    "users.db"
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_connection():

    os.makedirs(
        DATABASE_DIR,
        exist_ok=True
    )

    connection = sqlite3.connect(
        DATABASE_FILE
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_database():

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP
        )
    """)

    connection.commit()

    connection.close()

    print("Database initialized successfully.")


# =========================================================
# CREATE USER
# =========================================================

def create_user(
    username,
    email,
    password
):

    connection = get_connection()

    cursor = connection.cursor()

    hashed_password = generate_password_hash(
        password
    )

    cursor.execute("""
        INSERT INTO users (
            username,
            email,
            password
        )
        VALUES (?, ?, ?)
    """, (
        username.strip(),
        email.strip().lower(),
        hashed_password
    ))

    connection.commit()

    connection.close()


# =========================================================
# GET USER BY EMAIL
# =========================================================

def get_user_by_email(email):

    connection = get_connection()

    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM users
        WHERE email = ?
    """, (
        email.strip().lower(),
    ))

    user = cursor.fetchone()

    connection.close()

    return user


# =========================================================
# VERIFY PASSWORD
# =========================================================

def verify_password(
    password,
    stored_password
):

    try:

        return check_password_hash(
            stored_password,
            password
        )

    except Exception as e:

        print(
            "Password verification error:",
            e
        )

        return False


# =========================================================
# RESET PASSWORD
# =========================================================

def reset_password(
    email,
    new_password
):

    connection = get_connection()

    cursor = connection.cursor()

    hashed_password = generate_password_hash(
        new_password
    )

    cursor.execute("""
        UPDATE users
        SET password = ?
        WHERE email = ?
    """, (
        hashed_password,
        email.strip().lower()
    ))

    connection.commit()

    updated_rows = cursor.rowcount

    connection.close()

    return updated_rows > 0


# =========================================================
# TEST DATABASE
# =========================================================

if __name__ == "__main__":

    init_database()

    print(
        "Database test completed."
    )