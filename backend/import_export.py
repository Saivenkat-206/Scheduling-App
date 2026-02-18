from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
import logging
from app.database import SessionLocal
from app.dynamic_table import get_table_class, headers_for_sheet
import pandas as pd
from io import BytesIO
from openpyxl import Workbook
from fastapi.responses import StreamingResponse
from typing import Generator
from app.permissions import get_current_user, is_allowed, Action
from app.models import User
from sqlalchemy.orm import Session

router = APIRouter()

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/import/{sheet_type}/{mm}/{yy}")
async def import_table(sheet_type: str, mm: str, yy: str, file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not is_allowed(current_user, Action.IMPORT, sheet_type):
        raise HTTPException(status_code=403, detail="Not authorized to import")
    
    mm = mm.zfill(2)
    yy = yy[-2:]
    table_name = f"{sheet_type.lower()}_{mm}_{yy}"

    # read workbook into pandas
    try:
        df = pd.read_excel(file.file, engine="openpyxl", dtype=object)
    except Exception:
        logging.exception("Failed to parse uploaded Excel file")
        raise HTTPException(status_code=400, detail="could not process uploaded Excel file")

    # expected headers must match exactly
    expected = headers_for_sheet(sheet_type.lower())
    actual = list(df.columns)
    if actual != expected:
        raise HTTPException(status_code=400, detail=f"Header mismatch. Expected EXACT headers: {expected}. Got: {actual}")

    Model = get_table_class(table_name, sheet_type.lower())
    tbl = Model.__table__

    records = df.where(pd.notnull(df), None).to_dict(orient="records")
    objs = []
    for rec in records:
        kwargs = {}
        for col in tbl.columns:
            if col.name == "id":
                continue
            kwargs[col.key] = rec.get(col.name)
        objs.append(Model(**kwargs))
    mm = mm.zfill(2)
    yy = yy[-2:]
    table_name = f"{sheet_type.lower()}_{mm}_{yy}"

    # read workbook into pandas
    try:
        df = pd.read_excel(file.file, engine="openpyxl", dtype=object)
    except Exception:
        logging.exception("Failed to parse uploaded Excel file")
        raise HTTPException(status_code=400, detail="could not process uploaded Excel file")

    # expected headers must match exactly
    expected = headers_for_sheet(sheet_type.lower())
    actual = list(df.columns)
    if actual != expected:
        raise HTTPException(status_code=400, detail=f"Header mismatch. Expected EXACT headers: {expected}. Got: {actual}")

    Model = get_table_class(table_name, sheet_type.lower())
    tbl = Model.__table__

    records = df.where(pd.notnull(df), None).to_dict(orient="records")
    objs = []
    for rec in records:
        kwargs = {}
        for col in tbl.columns:
            if col.name == "id":
                continue
            kwargs[col.key] = rec.get(col.name)
        objs.append(Model(**kwargs))

    db.add_all(objs)
    db.commit()
    return {"imported": len(objs), "table": table_name}

@router.get("/export/{sheet_type}/{mm}/{yy}")
def export_table(sheet_type: str, mm: str, yy: str, db = Depends(get_db)):
    mm = mm.zfill(2)
    yy = yy[-2:]
    table_name = f"{sheet_type.lower()}_{mm}_{yy}"
    Model = get_table_class(table_name, sheet_type.lower())
    tbl = Model.__table__
    cols = [c for c in tbl.columns if c.name != "id"]

    rows = db.query(Model).all()

    wb = Workbook()
    ws = wb.active
    header_row = [c.name for c in cols]
    ws.append(header_row)

    for r in rows:
        row_values = []
        for c in cols:
            val = getattr(r, c.key)
            row_values.append(val)
        ws.append(row_values)

    stream = BytesIO()
    wb.save(stream)
    stream.seek(0)
    filename = f"{table_name}.xlsx"
    return StreamingResponse(stream, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": f'attachment; filename="{filename}"'})
