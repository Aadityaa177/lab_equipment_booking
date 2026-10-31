
import getpass
import pymysql
from werkzeug.security import generate_password_hash

DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": getpass.getpass("Enter your MySQL root password: "),
    "database": "campus_lab_booking",
    "cursorclass": pymysql.cursors.DictCursor,
    "charset": "utf8mb4",
}

print("\n=== Create First Admin Account ===")

college_id = input("Admin College ID: ").strip().upper()
full_name = input("Admin full name: ").strip()
email = input("Admin email: ").strip().lower()
password = getpass.getpass("Set admin password: ")
confirm_password = getpass.getpass("Confirm admin password: ")

if not all([college_id, full_name, email, password]):
    print("Error: All fields are required.")
    raise SystemExit(1)

if password != confirm_password:
    print("Error: Passwords do not match.")
    raise SystemExit(1)

if len(password) < 8:
    print("Error: Password must contain at least 8 characters.")
    raise SystemExit(1)

if "@" not in email:
    print("Error: Enter a valid email address.")
    raise SystemExit(1)

connection = None

try:
    connection = pymysql.connect(**DB_CONFIG)

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT user_id
            FROM users
            WHERE college_id = %s OR email = %s
            """,
            (college_id, email),
        )

        if cursor.fetchone():
            print("Error: That College ID or email already exists.")
            raise SystemExit(1)

        cursor.execute(
            """
            INSERT INTO users
                (college_id, full_name, email, password_hash, role)
            VALUES (%s, %s, %s, %s, 'ADMIN')
            """,
            (
                college_id,
                full_name,
                email,
                generate_password_hash(password),
            ),
        )

    connection.commit()
    print("\nAdmin account created successfully!")
    print("You can now log in through your website.")

except pymysql.MySQLError as error:
    print(f"Database error: {error}")

finally:
    if connection:
        connection.close()
