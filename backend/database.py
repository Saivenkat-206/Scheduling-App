from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# --- SIMPLE MYSQL CONFIG ---
MYSQL_USER = "root"
MYSQL_PASSWORD = "Wasdopkl#123"   # <-- put your MySQL password here
MYSQL_HOST = "localhost"
MYSQL_DB = "scheduling_app"

DATABASE_URL = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:3306/{MYSQL_DB}"

# --- SQLALCHEMY ENGINE ---
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base = declarative_base()
