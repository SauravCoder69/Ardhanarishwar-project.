import argparse
import sqlite3
from getpass import getpass

from database.database import get_connection, hash_password, init_db


def create_admin(username: str, password: str, full_name: str) -> None:
    username = username.strip()
    full_name = full_name.strip()
    if not username:
        raise ValueError("Username cannot be empty.")
    if not full_name:
        raise ValueError("Full name cannot be empty.")
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long.")

    connection = get_connection()
    try:
        connection.execute(
            "INSERT INTO users (username, password_hash, role, tenant_id, full_name) "
            "VALUES (?, ?, 'Admin', 'tenant_global', ?)",
            (username, hash_password(password), full_name),
        )
        connection.commit()
    except sqlite3.IntegrityError as error:
        raise ValueError(f"Username '{username}' already exists.") from error
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Create an administrator account.")
    parser.add_argument("username", help="username for the new administrator")
    args = parser.parse_args()

    full_name = input("Admin full name: ").strip()
    password = getpass("Admin password (minimum 12 characters): ")
    confirmation = getpass("Confirm admin password: ")
    if password != confirmation:
        parser.error("Passwords do not match.")

    init_db()
    try:
        create_admin(args.username, password, full_name)
    except ValueError as error:
        parser.error(str(error))
    print(f"Admin account '{args.username}' created. You can now log in.")


if __name__ == "__main__":
    main()
