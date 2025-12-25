# =========================
# HEADER MAPS
# =========================

GROUP_A_HEADER_MAP = {
    "OA": "OA",
    "EPICOR_NO": "EPICOR NO",
    "CUSTOMER_NAME": "CUSTOMER NAME",
    "INSP": "INSP",
    "AGENTS": "AGENTS",
    "CODE": "CODE",
    "FAN_MODEL": "FAN MODEL",
    "QTY": "QTY",
    "AMOUNT": "AMOUNT",
    "EDD": "EDD",
    "REVISED_EDD": "REVISED EDD",
    "PROJECT_STATUS": "PROJECT STATUS",
    "FACTORY_STATUS": "FACTORY STATUS",
    "PAYMENT_TERMS": "PAYMENT TERMS",
    "CASE":  "CASE",
    "HUB": "HUB",
    "SHAFT": "SHAFT",
    "IMP": "IMP",
    "FCP": "FCP",
    "ASS": "ASS",
    "TEST": "TEST",
    "FP": "FP",
    "PACK": "PACK",
    "DESPATCH_DATE": "DESPATCH DATE",
    "REMARKS": "REMARKS"
}

SHUTDOWN_HEADER_MAP = {
    "OA": "OA",
    "EPICOR_NO": "EPICOR NO",
    "CUSTOMER_NAME": "CUSTOMER NAME",
    "INSP": "INSP",
    "AGENTS": "AGENTS",
    "CODE": "CODE",
    "FAN_MODEL": "FAN MODEL",
    "QTY": "QTY",
    "AMOUNT": "AMOUNT",
    "EDD": "EDD",
    "REVISED_EDD": "REVISED EDD",
    "PROJECT_STATUS": "PROJECT STATUS",
    "FACTORY_STATUS": "FACTORY STATUS",
    "PAYMENT_TERMS": "PAYMENT TERMS",
    "CASE":  "CASE",
    "HUB": "HUB",
    "SHAFT": "SHAFT",
    "IMP": "IMP",
    "FCP": "FCP",
    "ASS": "ASS",
    "TEST": "TEST",
    "FP": "FP",
    "PACK": "PACK",
    "DESPATCH_DATE": "DESPATCH DATE",
    "REMARKS": "REMARKS"
}

# For backwards compatibility
HEADER_MAP = GROUP_A_HEADER_MAP
REVERSE_HEADER_MAP = {v: k for k, v in GROUP_A_HEADER_MAP.items()}

def get_header_map(sheet_type: str):
    """Get the appropriate header map based on sheet type"""
    if sheet_type.lower() == "shutdown":
        return SHUTDOWN_HEADER_MAP
    return GROUP_A_HEADER_MAP

def infer_sheet_type(table_name: str) -> str:
    """Infer sheet type from table name"""
    if table_name.lower().startswith("shutdown"):
        return "shutdown"
    return "group_a"

# =========================
# IMPORTS
# =========================

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import Integer, Numeric, Date
from app.database import SessionLocal
from app.dynamic_table import get_table_class
import pandas as pd
from fastapi.responses import StreamingResponse
from io import BytesIO
import math
from datetime import date

def is_future_date(d: date | None) -> bool:
    if not d:
        return False
    return d > date.today()

router = APIRouter()

# =========================
# DB DEP
# =========================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# =========================
# SANITIZER (FIXES YOUR ERRORS)
# =========================

def sanitize_for_add(col, payload):
    value = payload.get(col.name)

    # 🔍 DEBUG
    print(f"[SANITIZE] Column={col.name}, RawValue={value}, Type={type(value)}")

    # Handle pandas NaN explicitly
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None

    if value == "" or value == "NA":
        if isinstance(col.type, (Integer, Numeric, Date)):
            return None
        return "NA"

    if isinstance(col.type, Integer):
        try:
            return int(value)
        except:
            return None

    if isinstance(col.type, Numeric):
        try:
            return float(value)
        except:
            return None

    if isinstance(col.type, Date):
        try:
            # Handle strings with multiple dates (newlines, commas, semicolons)
            if isinstance(value, str):
                import re

                parts = [p.strip() for p in re.split(r"[\n,;]+", value) if p.strip()]
                if len(parts) > 1:
                    # Try to parse all parts and pick the earliest valid date
                    try:
                        dt_index = pd.to_datetime(parts, dayfirst=True, errors="coerce")
                        valid = [d for d in dt_index if not pd.isna(d)]
                        if valid:
                            return min(valid).date()
                    except Exception:
                        # fallback to first part
                        value = parts[0]
                else:
                    value = parts[0] if parts else value

            parsed = pd.to_datetime(value, dayfirst=True, errors="coerce")
            if pd.isna(parsed):
                return None
            return parsed.date()
        except Exception:
            return None

    return str(value)

# =========================
# OPEN TABLE
# =========================

class OpenTableReq(BaseModel):
    sheet_type: str
    month: str
    year: str

@router.post("/open_table")
def open_table(req: OpenTableReq, db: Session = Depends(get_db)):
    table_name = f"{req.sheet_type.lower()}_{req.month.zfill(2)}_{req.year[-2:]}"
    sheet_type = infer_sheet_type(table_name)
    print(f"[OPEN TABLE] {table_name}, SheetType={sheet_type}")

    Model = get_table_class(table_name, sheet_type)
    rows = db.query(Model).all()

    cols = [c for c in Model.__table__.columns if c.name != "id"]
    out = []

    for r in rows:
        row = {c.name: getattr(r, c.key) for c in cols}
        row["id"] = r.id
        out.append(row)

    return {
        "table_name": table_name,
        "headers": [c.name for c in cols],
        "rows": out,
    }

# =========================
# CRUD
# =========================

@router.post("/rows/{table_name}")
def create_row(table_name: str, payload: dict, db: Session = Depends(get_db)):
    sheet_type = infer_sheet_type(table_name)
    Model = get_table_class(table_name, sheet_type)

    print(f"[CREATE ROW] Table={table_name}, SheetType={sheet_type}")
    print(f"[PAYLOAD] {payload}")
    print(f"[PAYLOAD KEYS] {list(payload.keys())}")
    print(f"[MODEL COLUMNS] {[c.name for c in Model.__table__.columns]}")

    # If payload contains an `id`, try to update that row instead of creating a new one
    row_id = payload.get("id")
    if row_id is not None:
        try:
            row_id = int(row_id)
        except Exception:
            row_id = None

    if row_id is not None:
        obj = db.query(Model).filter(Model.id == row_id).first()
        if obj:
            for col in Model.__table__.columns:
                if col.name == "id":
                    continue
                if col.name in payload:
                    setattr(obj, col.key, sanitize_for_add(col, payload))

            db.commit()
            return {"updated": True, "id": obj.id}

    # Otherwise create a new row
    obj = Model()

    for col in Model.__table__.columns:
        if col.name == "id":
            continue
        setattr(obj, col.key, sanitize_for_add(col, payload))

    db.add(obj)
    db.commit()
    db.refresh(obj)
    warnings = []

    for col in Model.__table__.columns:
        if col.name == "id":
            continue

    value = sanitize_for_add(col, payload)
    setattr(obj, col.name, value)

    if col.type.__class__.__name__ == "Date" and is_future_date(value):
        warnings.append(f"{col.name} is a future date")

    return {"created": True, "id": obj.id, "warnings": warnings}

@router.put("/rows/{table_name}/{row_id}")
def update_row(table_name: str, row_id: int, payload: dict, db: Session = Depends(get_db)):
    sheet_type = infer_sheet_type(table_name)
    Model = get_table_class(table_name, sheet_type)
    obj = db.query(Model).filter(Model.id == row_id).first()

    if not obj:
        raise HTTPException(status_code=404, detail="Row not found")

    print(f"[UPDATE ROW] Table={table_name}, ID={row_id}, SheetType={sheet_type}")
    print(f"[PAYLOAD] {payload}")
    print(f"[PAYLOAD KEYS] {list(payload.keys())}")
    print(f"[MODEL COLUMNS] {[c.name for c in Model.__table__.columns]}")

    warnings = []

    for col in Model.__table__.columns:
        if col.name == "id":
            continue

        value = sanitize_for_add(col, payload)
        setattr(obj, col.name, value)

        if col.type.__class__.__name__ == "Date" and is_future_date(value):
            warnings.append(f"{col.name} is a future date")

    db.commit()
    return {"updated": True, "id": obj.id, "warnings": warnings}

@router.delete("/rows/{table_name}/{row_id}")
def delete_row(table_name: str, row_id: int, db: Session = Depends(get_db)):
    sheet_type = infer_sheet_type(table_name)
    Model = get_table_class(table_name, sheet_type)
    obj = db.query(Model).filter(Model.id == row_id).first()

    if not obj:
        raise HTTPException(status_code=404, detail="Row not found")

    db.delete(obj)
    db.commit()
    return {"deleted": True}

# =========================
# EXPORT (WITH COLORS)
# =========================

@router.get("/export/{table_name}")
def export_table(table_name: str, db: Session = Depends(get_db)):
    sheet_type = infer_sheet_type(table_name)
    Model = get_table_class(table_name, sheet_type)
    rows = db.query(Model).all()

    header_map = get_header_map(sheet_type)
    data = []
    for r in rows:
        record = {}
        for db_col, excel_col in header_map.items():
            record[excel_col] = getattr(r, db_col, None)
        data.append(record)

    df = pd.DataFrame(data)

    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name=table_name)

        workbook = writer.book
        worksheet = writer.sheets[table_name]

        # Get date columns for this sheet type
        from app.dynamic_table import GROUP_A_DATE_COLS, SHUTDOWN_DATE_COLS
        date_cols = SHUTDOWN_DATE_COLS if sheet_type == "shutdown" else GROUP_A_DATE_COLS

        # Color formats
        green_fmt = workbook.add_format({"bg_color": "#90EE90"})  # Light green for filled dates
        remarks_fmt = workbook.add_format({"bg_color": "#FFF9C4"})  # Yellow for remarks

        for idx, col in enumerate(df.columns):
            # Green for date columns with values
            if col in date_cols:
                for row_idx in range(len(df)):
                    cell_value = df.iloc[row_idx, idx]
                    if pd.notna(cell_value) and cell_value != "NA":
                        worksheet.write(row_idx + 1, idx, cell_value, green_fmt)
            
            # Yellow for remarks only when not empty
            if col == "REMARKS":
                for row_idx in range(len(df)):
                    cell_value = df.iloc[row_idx, idx]
                    if pd.notna(cell_value) and cell_value != "NA" and str(cell_value).strip():
                        worksheet.write(row_idx + 1, idx, cell_value, remarks_fmt)

    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={table_name}.xlsx"},
    )

# =========================
# IMPORT (THIS IS THE BIG FIX)
# =========================

@router.post("/import/{table_name}")
def import_table(
    table_name: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    sheet_type = infer_sheet_type(table_name)
    print(f"[IMPORT] Table={table_name}, SheetType={sheet_type}, File={file.filename}")

    Model = get_table_class(table_name, sheet_type)

    # ---- STEP 1: read raw to find header row ----
    raw_df = pd.read_excel(file.file, header=None)

    header_row_idx = None
    for i, row in raw_df.iterrows():
        if "OA" in row.values:
            header_row_idx = i
            break

    if header_row_idx is None:
        raise HTTPException(
            status_code=400,
            detail="Could not detect header row (OA not found)",
        )

    print(f"[HEADER ROW INDEX] {header_row_idx}")

    # ---- STEP 2: re-read with correct header ----
    file.file.seek(0)  # IMPORTANT: reset file pointer
    df = pd.read_excel(file.file, header=header_row_idx)
    df.columns = [c.strip() for c in df.columns]

    print("[EXCEL HEADERS]", list(df.columns))

    # ---- STEP 3: validate columns ----
    header_map = get_header_map(sheet_type)
    excel_columns = set(header_map.values())
    
    model_columns = {
        col.name for col in Model.__table__.columns if col.name != "id"
    }

    missing = model_columns - set(df.columns)
    extra = set(df.columns) - model_columns

    print("[MODEL COLS]", model_columns)
    print("[MISSING COLS]", missing)
    print("[EXTRA COLS]", extra)

    if missing:
        raise HTTPException(
            status_code=400,
            detail=f"Missing columns: {missing}",
        )

    # ---- STEP 4: insert rows ----
    inserted = 0

    for idx, row in df.iterrows():
        obj = Model()
        payload = row.to_dict()

        print(f"[ROW {idx}]", payload)

        for col in Model.__table__.columns:
            if col.name == "id":
                continue

            # Use the centralized sanitizer to coerce/clean values
            clean_val = sanitize_for_add(col, payload)
            setattr(obj, col.key, clean_val)

        db.add(obj)
        inserted += 1

    db.commit()

    print(f"[IMPORT DONE] rows={inserted}")
    return {"imported_rows": inserted}

@router.get("/rows/{table_name}")
def list_rows(table_name: str, db: Session = Depends(get_db)):
    Model = get_table_class(table_name, "us_llc")
    rows = db.query(Model).limit(5000).all()

    cols = [c for c in Model.__table__.columns if c.name != "id"]

    out = []
    for r in rows:
        row = {}
        for c in cols:
            row[c.name] = getattr(r, c.key)
        row["id"] = r.id
        out.append(row)

    return {
        "table_name": table_name,
        "headers": [c.name for c in cols],
        "rows": out
    }
