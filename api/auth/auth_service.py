import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from storage.utils import read_users, write_users
from jose import JWTError, jwt
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SECRET_KEY = "your_secret_key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

auth_router = APIRouter(prefix="/auth")

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

def create_access_token(data: dict, expires_delta: timedelta = None):
    logging.info("Creating access token")
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    logging.info(f"Token expiry time: {expire}")
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

@auth_router.post("/login")
def login(user: UserLogin):
    logging.info(f"Attempting login for user: {user.username}")
    users = read_users()
    for u in users:
        if u["username"] == user.username and u["password"] == user.password:
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": u["id"]}, expires_delta=access_token_expires
            )
            logging.info(f"Generated access token for user: {user.username}")
            return {
                        "id":u["id"],
                        "user_id":u["id"],
                        "username":u["username"],
                        "access_token": access_token,
                        "token_type": "bearer"
                    }
    logging.warning(f"Invalid username or password for user: {user.username}")
    raise HTTPException(status_code=401, detail="Invalid username or password")