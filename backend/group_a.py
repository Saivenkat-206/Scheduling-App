from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal, Base
from app.models import USLLCOrders, UrgentOrders, RegularOrders, DoubtfulOrders, DomesticOrders, WabtecOrders
from app.models import Base
from app.database import engine

Base.metadata.create_all(bind=engine)
router = APIRouter()

tables = {
    "us_llc": USLLCOrders,
    "urgent": UrgentOrders,
    "regular": RegularOrders,
    "doubtful": DoubtfulOrders,
    "domestic": DomesticOrders,
    "wabtec": WabtecOrders
}


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{table}")
def get_rows(table: str, db: Session = Depends(get_db)):
    if table not in tables: raise HTTPException(404)
    return db.query(tables[table]).all()


@router.post("/{table}")
def create_row(table: str, payload: dict, db: Session = Depends(get_db)):
    if table not in tables: raise HTTPException(404)
    obj = tables[table](**payload)
    db.add(obj)
    db.commit()
    return {"created": True}