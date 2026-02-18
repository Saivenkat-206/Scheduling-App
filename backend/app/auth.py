from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import SessionLocal
import bcrypt
import jwt
from datetime import datetime, timedelta
from app.models import User, UserType
from app.config import settings

router = APIRouter()

class LoginReq(BaseModel):
    email: str
    password: str

class UserCreate(BaseModel):
    email: str
    password: str
    user_type: UserType

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

@router.post("/login")
def login(payload: LoginReq, db: Session = Depends(get_db)):
    # Dummy login for testing
    if payload.email == "admin" and payload.password == "admin123":
        access_token = create_access_token(data={"sub": "admin", "user_type": "superuser"})
        return {"ok": True, "token": access_token, "user_type": "superuser"}
    
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user.email, "user_type": user.user_type.value})
    return {"ok": True, "token": access_token, "user_type": user.user_type.value}

@router.post("/users")
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    # In production, this should be protected and only allow superusers to create users
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    hashed_password = hash_password(payload.password)
    new_user = User(email=payload.email, password_hash=hashed_password, user_type=payload.user_type)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "User created successfully"}
