import re
from sqlalchemy import (
    Table,
    Column,
    Integer,
    Date,
    Numeric,
    Text,
    String,
)
from sqlalchemy import inspect, text
from app.database import Base, engine
import datetime

# ===== EXACT HEADERS (SOURCE OF TRUTH) =====

GROUP_A_HEADERS = [
    "OA", "EPICOR NO", "CUSTOMER NAME", "INSP", "AGENTS", "CODE", "FAN MODEL",
    "QTY", "AMOUNT", "EDD", "REVISED EDD", "PROJECT STATUS",
    "FACTORY STATUS", "PAYMENT TERMS", "CASE", "HUB", "SHAFT",
    "IMP", "FCP", "ASS", "TEST", "FP", "PACK", "DESPATCH DATE", "REMARKS"
]

SHUTDOWN_HEADERS = [
    "OA", "EPICOR NO", "CUSTOMER NAME", "INSP", "AGENTS", "CODE", "FAN MODEL",
    "QTY", "AMOUNT", "EDD", "REVISED EDD", "PROJECT STATUS",
    "FACTORY STATUS", "PAYMENT TERMS", "CASE", "HUB", "SHAFT",
    "IMP", "FCP", "ASS", "TEST", "FP", "PACK", "DESPATCH DATE", "REMARKS"
]

# ===== TYPE INFERENCE =====

# Date columns for group_a tables
GROUP_A_DATE_COLS = {
    "EDD", "REVISED EDD", "CASE", "HUB", "SHAFT", "IMP", "FCP", "ASS", "TEST", "FP", "PACK", "DESPATCH DATE"
}

# Date columns for shutdown tables
SHUTDOWN_DATE_COLS = {
    "EDD", "REVISED EDD", "CASE", "HUB", "SHAFT", "IMP", "FCP", "ASS", "TEST", "FP", "PACK", "DESPATCH DATE"
}

def _col_type_for_header(header: str, sheet_type: str = "group_a"):
    if header in {"QTY", "LEAD TIME (DAYS)"}:
        return Integer
    if header == "AMOUNT":
        return Numeric(12, 2)
    
    # Check explicit date columns
    if sheet_type == "shutdown" and header in SHUTDOWN_DATE_COLS:
        return Date
    if sheet_type == "group_a" and header in GROUP_A_DATE_COLS:
        return Date
    
    # Fallback for existing DATE/DT patterns
    if "DATE" in header or header.endswith("DT"):
        return Date
    
    if header == "REMARKS":
        return Text
    return String(255)

# ===== SAFE PYTHON ATTRIBUTE NAME =====

def _make_safe_key(header: str) -> str:
    key = re.sub(r"[^0-9a-zA-Z_]", "_", header)
    if re.match(r"^[0-9]", key):
        key = "_" + key
    return key.upper()

# ===== MAIN FACTORY =====

def get_table_class(table_name: str, sheet_type: str = "group_a"):
    metadata = Base.metadata

    # reuse table if already defined
    headers = SHUTDOWN_HEADERS if sheet_type == "shutdown" else GROUP_A_HEADERS

    if table_name in metadata.tables:
        table = metadata.tables[table_name]
    else:
        columns = [
            Column("id", Integer, primary_key=True, autoincrement=True)
        ]

        for header in headers:
            # Make EPICOR NO unique for dynamic tables
            is_epicor = header.upper() == "EPICOR NO"
            columns.append(
                Column(
                    header,                      # DB column name (EXCEL EXACT)
                    _col_type_for_header(header, sheet_type),
                    key=_make_safe_key(header),  # Python-safe attribute
                    nullable=True,
                    unique=is_epicor
                )
            )

        table = Table(table_name, metadata, *columns)
        metadata.create_all(bind=engine)

    # Ensure existing DB table has expected columns; if not, ALTER TABLE to add them
    try:
        inspector = inspect(engine)
        existing = {c["name"] for c in inspector.get_columns(table_name)}
    except Exception:
        existing = set()

    # Map to SQL types and add missing columns
    def _sql_type_for_header(header: str, sheet_type: str = "group_a") -> str:
        t = _col_type_for_header(header, sheet_type)
        # Map SQLAlchemy types to MySQL type strings
        if isinstance(t, type) and t is Integer:
            return "INT"
        if isinstance(t, Numeric) or getattr(t, "__class__", None).__name__ == 'Numeric':
            # Numeric(12,2)
            try:
                precision, scale = t.precision, t.scale
                return f"DECIMAL({precision},{scale})"
            except Exception:
                return "DECIMAL(12,2)"
        if isinstance(t, type) and t is Date:
            return "DATE"
        if isinstance(t, type) and t is Text:
            return "TEXT"
        # default to varchar(255)
        return "VARCHAR(255)"


    missing = [h for h in headers if h not in existing]
    if missing:
        with engine.connect() as conn:
            for h in missing:
                sql_type = _sql_type_for_header(h, sheet_type)
                alter = f"ALTER TABLE `{table_name}` ADD COLUMN `{h}` {sql_type} NULL"
                try:
                    conn.execute(text(alter))
                except Exception:
                    # best-effort: ignore failures here (could be concurrent or permissions)
                    print(f"Failed to add column {h} to {table_name}")
    # Ensure EPICOR NO has a unique constraint/index
    try:
        ucs = inspector.get_unique_constraints(table_name)
        uc_cols = {col for uc in ucs for col in uc.get("column_names", [])}
    except Exception:
        uc_cols = set()

    if "EPICOR NO" in headers or "EPICOR NO" in existing:
        if "EPICOR NO" not in uc_cols:
            # create a unique index (best-effort)
            idx_name = f"ux_{table_name}_EPICOR_NO"
            add_unique_sql = f"ALTER TABLE `{table_name}` ADD UNIQUE INDEX `{idx_name}` (`EPICOR NO`)"
            try:
                with engine.connect() as conn:
                    conn.execute(text(add_unique_sql))
            except Exception:
                print(f"Failed to add unique index for EPICOR NO on {table_name}")

    # cache mapped class so SQLAlchemy doesn’t remap
    if hasattr(table, "_mapped_class"):
        return table._mapped_class

    class_name = "T_" + re.sub(r"\W+", "_", table_name)
    model = type(class_name, (Base,), {"__table__": table})

    table._mapped_class = model
    return model

def headers_for_sheet(sheet_type: str):
    return SHUTDOWN_HEADERS if sheet_type == "shutdown" else GROUP_A_HEADERS
