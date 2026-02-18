from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import ShutdownJob

router = APIRouter()


def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()


@router.get("/")
def fetch(db: Session = Depends(get_db)):
    return db.query(ShutdownJob).all()


@router.post("/")
def insert(payload: dict, db: Session = Depends(get_db)):
    obj = ShutdownJob(**payload)
    db.add(obj)
    db.commit()
    return {"created": True}
