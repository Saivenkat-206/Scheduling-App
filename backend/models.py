from sqlalchemy import Column, Integer, String, Numeric, Date, Text
from app.database import Base

# GROUP A
class GroupABase(Base):
    __abstract__ = True
    id = Column(Integer, primary_key=True)

    OA = Column(String(255))
    EPICOR_NO = Column(String(255))
    CUSTOMER_NAME = Column(String(255))
    INSP = Column(String(255))
    AGENTS = Column(String(255))
    CODE = Column(String(255))
    FAN_MODEL = Column(String(255))
    QTY = Column(Integer)
    AMOUNT = Column(Numeric(12, 2))
    EDD = Column(Date)
    REVISED_EDD = Column(Date)
    PROJECT_STATUS = Column(String(255))
    FACTORY_STATUS = Column(String(255))
    PAYMENT_TERMS = Column(String(255))
    CASE = Column(String(255))
    HUB = Column(String(255))
    SHAFT = Column(String(255))
    IMP = Column(String(255))
    FCP = Column(String(255))
    ASS = Column(String(255))
    TEST = Column(String(255))
    FP = Column(String(255))
    PACK = Column(String(255))
    DESPATCH_DATE = Column(Date)
    REMARKS = Column(Text)

class USLLCOrders(GroupABase): __tablename__ = "us_llc_orders"
class UrgentOrders(GroupABase): __tablename__ = "urgent_orders"
class RegularOrders(GroupABase): __tablename__ = "regular_orders"
class DoubtfulOrders(GroupABase): __tablename__ = "doubtful_orders"
class DomesticOrders(GroupABase): __tablename__ = "domestic_orders"
class WabtecOrders(GroupABase): __tablename__ = "wabtec_orders"


# SHUTDOWN JOB
class ShutdownJob(Base):
    __tablename__ = "shutdown_job"

    id = Column(Integer, primary_key=True)
    OA = Column(String(255))
    EPICOR_NO = Column(String(255))
    PO_CLRD_DT = Column(Date)
    OA_REL_DATE = Column(Date)
    LEAD_TIME_DAYS = Column(Integer)
    CUSTOMER_NAME = Column(String(255))
    AGENTS = Column(String(255))
    FAN_MODEL = Column(String(255))
    QTY = Column(Integer)
    AMOUNT = Column(Numeric(12, 2))
    NEED_DATE = Column(Date)
    REVISED_NEED_DATE = Column(Date)
    PROMISED_DATE = Column(Date)
    REVISED_PROMISED_DATE = Column(Date)
    FAN_STATUS = Column(String(255))
