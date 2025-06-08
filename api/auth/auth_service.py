import os
from dotenv import load_dotenv
load_dotenv()
import boto3
import logging
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
import httpx
from jose import jwt, JWTError
from functools import lru_cache

# Initialize AWS Cognito client
region = os.getenv('AWS_REGION', 'us-east-1')
user_pool_id = os.getenv('COGNITO_USER_POOL_ID')
client_id = os.getenv('COGNITO_USER_POOL_CLIENT_ID')

cognito_client = boto3.client('cognito-idp', region_name=region)

auth_router = APIRouter(prefix="/auth")

# Pydantic models for request payloads
class RegisterModel(BaseModel):
    username: str
    password: str
    email: str

class ConfirmModel(BaseModel):
    username: str
    confirmation_code: str

class LoginModel(BaseModel):
    username: str
    password: str

class RefreshModel(BaseModel):
    refresh_token: str

# Endpoint to register a new user
@auth_router.post('/register')
async def register_user(model: RegisterModel):
    try:
        cognito_client.sign_up(
            ClientId=client_id,
            Username=model.username,
            Password=model.password,
            UserAttributes=[{'Name': 'email', 'Value': model.email}]
        )
        return {'message': 'User registration initiated. Please confirm your email.'}
    except cognito_client.exceptions.UsernameExistsException:
        raise HTTPException(status_code=400, detail='Username already exists')
    except cognito_client.exceptions.InvalidPasswordException as e:
        # Password did not meet policy requirements
        msg = e.response.get('Error', {}).get('Message', str(e))
        raise HTTPException(status_code=400, detail=msg)
    except cognito_client.exceptions.InvalidParameterException as e:
        # Missing or invalid parameters
        msg = e.response.get('Error', {}).get('Message', str(e))
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        logging.error(f"Error during sign up: {e}")
        raise HTTPException(status_code=500, detail='Registration failed')

# Endpoint to confirm user registration
@auth_router.post('/confirm')
async def confirm_user(model: ConfirmModel):
    try:
        cognito_client.confirm_sign_up(
            ClientId=client_id,
            Username=model.username,
            ConfirmationCode=model.confirmation_code
        )
        return {'message': 'User confirmed successfully'}
    except cognito_client.exceptions.CodeMismatchException:
        raise HTTPException(status_code=400, detail='Invalid confirmation code')
    except cognito_client.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=400, detail='Confirmation code expired')
    except Exception as e:
        logging.error(f"Error during confirmation: {e}")
        raise HTTPException(status_code=500, detail='Confirmation failed')

# Endpoint to log in and obtain JWT tokens
@auth_router.post('/login')
async def login_user(model: LoginModel):
    try:
        resp = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters={'USERNAME': model.username, 'PASSWORD': model.password}
        )
        auth_result = resp.get('AuthenticationResult', {})
        return {
            'access_token': auth_result.get('AccessToken'),
            'id_token': auth_result.get('IdToken'),
            'refresh_token': auth_result.get('RefreshToken')
        }
    except cognito_client.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail='Invalid credentials')
    except Exception as e:
        logging.error(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail='Login failed')

# Endpoint to refresh tokens
@auth_router.post('/refresh')
async def refresh_token(model: RefreshModel):
    try:
        resp = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={'REFRESH_TOKEN': model.refresh_token}
        )
        auth_result = resp.get('AuthenticationResult', {})
        return {
            'access_token': auth_result.get('AccessToken'),
            'id_token': auth_result.get('IdToken')
        }
    except Exception as e:
        logging.error(f"Error during token refresh: {e}")
        raise HTTPException(status_code=500, detail='Token refresh failed')

# Fetch and cache JWKS for manual JWT verification
COGNITO_REGION = os.getenv('COGNITO_REGION', os.getenv('AWS_REGION', 'us-east-1'))
COGNITO_USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID')
COGNITO_JWKS_URL = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"

@lru_cache()
def get_cognito_jwks():
    resp = httpx.get(COGNITO_JWKS_URL)
    resp.raise_for_status()
    return resp.json()

async def get_current_user(request: Request):
    # Parse and verify JWT from Authorization header
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        raise HTTPException(status_code=401, detail='Missing or invalid Authorization header')
    token = auth_header.split(' ', 1)[1]
    jwks = get_cognito_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get('kid')
        key = next((k for k in jwks['keys'] if k['kid'] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail='Public key not found in JWKS')
        claims = jwt.decode(
            token,
            key,
            algorithms=['RS256'],
            audience=client_id,
            issuer=f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}"
        )
        return claims
    except JWTError as e:
        logging.error(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail='Invalid token')

# Alias for backward compatibility/tests
get_user = get_current_user

from fastapi import Depends

# Dependency to extract user_id directly
async def get_user_id_from_token(user_claims: dict = Depends(get_current_user)):
    return user_claims.get('sub') or user_claims.get('username')