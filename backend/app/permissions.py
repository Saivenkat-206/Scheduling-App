from enum import Enum
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import User, UserType
import jwt
from app.config import settings

security = HTTPBearer()

class Action(str, Enum):
    VIEW = "view"
    ADD = "add"
    EDIT = "edit"
    DELETE = "delete"
    IMPORT = "import"
    EXPORT = "export"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        # Handle dummy admin user for testing
        if email == "admin":
            dummy_user = User(id=0, email="admin", password_hash="", user_type=UserType.SUPERUSER)
            return dummy_user
        
        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def is_allowed(user: User, action: Action, table_name: str) -> bool:
    """
    Check if user is allowed to perform action on table_name
    """
    if user.user_type == UserType.SUPERUSER:
        return True  # SuperUser has all access
    
    elif user.user_type == UserType.SUBUSER:
        # SubUser can view, edit, import, export but not add or delete
        return action in [Action.VIEW, Action.EDIT, Action.IMPORT, Action.EXPORT]
    
    elif user.user_type == UserType.VIEWER:
        # Viewer can only view and export
        return action in [Action.VIEW, Action.EXPORT]
    
    return False
