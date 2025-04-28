import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from jose import JWTError, jwt
from datetime import datetime, timedelta
import boto3
from boto3.dynamodb.conditions import Key
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Load SECRET_KEY from .env
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY is not set in the environment variables")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize DynamoDB client
dynamodb = boto3.resource('dynamodb')
auth_table = dynamodb.Table('AuthTable')  # Replace with your DynamoDB table name

auth_router = APIRouter(prefix="/auth")

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenRefresh(BaseModel):
    refresh_token: str

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

def read_user_from_auth_table(username: str):
    logging.info(f"Fetching user from AuthTable for username: {username}")
    try:
        response = auth_table.get_item(Key={'username': username})
        return response.get('Item')
    except Exception as e:
        logging.error(f"Error fetching user: {e}")
        return None

@auth_router.post("/login")
def login(user: UserLogin):
    logging.info(f"Attempting login for user: {user.username}")
    db_user = read_user_from_auth_table(user.username)
    if db_user and db_user["password"] == user.password:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": db_user["username"]}, expires_delta=access_token_expires
        )
        logging.info(f"Generated access token for user: {user.username}")
        return {
            "username": db_user["username"],
            "access_token": access_token,
            "token_type": "bearer"
        }
    logging.warning(f"Invalid username or password for user: {user.username}")
    raise HTTPException(status_code=401, detail="Invalid username or password")

@auth_router.post("/refresh")
def refresh_token(token_data: TokenRefresh):
    logging.info("Refreshing access token")
    try:
        payload = jwt.decode(token_data.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

        # Generate a new access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        new_access_token = create_access_token(
            data={"sub": username}, expires_delta=access_token_expires
        )
        logging.info(f"Generated new access token for user: {username}")
        return {
            "access_token": new_access_token,
            "token_type": "bearer"
        }
    except JWTError as e:
        logging.error(f"JWT decoding error during token refresh: {e}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")