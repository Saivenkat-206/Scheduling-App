from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class LoginReq(BaseModel):
    username: str
    password: str

@router.post("/login")
def login(payload: LoginReq):
    # hardcoded simple auth as requested
    if payload.username == "admin" and payload.password == "admin123":
        return {"ok": True, "token": "dummy-token"}
    raise HTTPException(status_code=401, detail="Invalid credentials")
