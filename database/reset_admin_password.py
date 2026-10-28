import argparse
from getpass import getpass

from database.database import get_connection, hash_password, init_db


def reset_admin_password(username: str, password: str) -> None:
    if len(password) < 12:
        raise ValueError("Password must be at least 12 characters long.")

    connection = get_connection()
    try:
        user = connection.execute(
            "SELECT id, role FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        if user is None or user["role"] != "Admin":
            raise ValueError(f"No administrator account found for '{username}'.")

        connection.execute(
            "UPDATE users SET password_hash = ? WHERE id = ?",
            (hash_password(password), user["id"]),
        )
        connection.commit()
    finally:
        connection.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset an existing administrator password.")
    parser.add_argument("username", help="username of the existing administrator account")
    args = parser.parse_args()

    init_db()
    password = getpass("New administrator password (minimum 12 characters): ")
    confirmation = getpass("Confirm new administrator password: ")
    if password != confirmation:
        parser.error("Passwords do not match.")

    try:
        reset_admin_password(args.username, password)
    except ValueError as error:
        parser.error(str(error))
    print(f"Password reset for administrator '{args.username}'.")


if __name__ == "__main__":
    main()
