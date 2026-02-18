#!/usr/bin/env python3

from app.database import engine, Base
from app.models import User, UserType
from app.auth import hash_password
import sys

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully!")

def create_admin_user():
    from sqlalchemy.orm import sessionmaker
    from app.database import SessionLocal

    db = SessionLocal()
    try:
        # Check if admin user already exists
        existing_admin = db.query(User).filter(User.email == "admin@example.com").first()
        if existing_admin:
            print("Admin user already exists!")
            return

        # Create admin user
        admin_user = User(
            email="admin@example.com",
            password_hash=hash_password("admin123"),
            user_type=UserType.SUPERUSER
        )
        db.add(admin_user)
        db.commit()
        print("Admin user created successfully!")
        print("Email: admin@example.com")
        print("Password: admin123")
        print("User Type: SUPERUSER")

    except Exception as e:
        print(f"Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "create_admin":
        create_admin_user()
    else:
        init_db()