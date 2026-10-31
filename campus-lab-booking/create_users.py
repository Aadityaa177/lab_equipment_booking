
from getpass import getpass
from sqlalchemy import text
from werkzeug.security import generate_password_hash
from app import app, db

VALID_ROLES = {
    "1": "STUDENT",
    "2": "FACULTY",
    "3": "STAFF",
    "4": "INCHARGE",
}

def create_user():
    print("\n=== Campus Lab Booking - Create User ===")
    print("1. Student")
    print("2. Faculty")
    print("3. Staff")
    print("4. Lab In-charge")

    role_choice = input("Choose role (1-4): ").strip()

    if role_choice not in VALID_ROLES:
        print("Invalid role.")
        return

    role = VALID_ROLES[role_choice]
    college_id = input("College ID: ").strip().upper()
    full_name = input("Full name: ").strip()
    email = input("Email: ").strip().lower()
    password = getpass("Password (minimum 8 characters): ")
    confirm = getpass("Confirm password: ")

    if not all([college_id, full_name, email, password]):
        print("All fields are required.")
        return

    if len(password) < 8:
        print("Password must contain at least 8 characters.")
        return

    if password != confirm:
        print("Passwords do not match.")
        return

    with app.app_context():
        existing = db.session.execute(
            text("""
                SELECT user_id
                FROM users
                WHERE college_id = :college_id OR email = :email
            """),
            {"college_id": college_id, "email": email}
        ).first()

        if existing:
            print("College ID or email already exists.")
            return

        try:
            db.session.execute(
                text("""
                    INSERT INTO users
                        (college_id, full_name, email, password_hash, role)
                    VALUES
                        (:college_id, :full_name, :email, :password_hash, :role)
                """),
                {
                    "college_id": college_id,
                    "full_name": full_name,
                    "email": email,
                    "password_hash": generate_password_hash(password),
                    "role": role,
                }
            )
            db.session.commit()
            print(f"\nSUCCESS: {role} account {college_id} created.")

        except Exception as error:
            db.session.rollback()
            print("Could not create account. Check whether the ID or email exists.")
            print(f"Details: {error}")

if __name__ == "__main__":
    create_user()
