
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from storage.utils import read_users, write_users

auth_router = APIRouter(prefix="/auth")

class UserLogin(BaseModel):
    username: str
    password: str

@auth_router.post("/login")
def login(user: UserLogin):
    users = read_users()
    for u in users:
        if u["username"] == user.username and u["password"] == user.password:
            return {"id": u["id"], "username": u["username"], "email": u["email"]}
    raise HTTPException(status_code=401, detail="Invalid username or password")