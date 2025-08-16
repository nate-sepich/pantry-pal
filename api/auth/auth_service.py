import os

from dotenv import load_dotenv

load_dotenv()
import logging
from functools import lru_cache

import boto3
import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from jose import JWTError, jwt
from pydantic import BaseModel

# Initialize AWS Cognito client
region = os.getenv("AWS_REGION", "us-east-1")
user_pool_id = os.getenv("COGNITO_USER_POOL_ID")
client_id = os.getenv("COGNITO_USER_POOL_CLIENT_ID")

cognito_client = boto3.client("cognito-idp", region_name=region)

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


class ForgotPasswordModel(BaseModel):
    username: str


class ResetPasswordModel(BaseModel):
    username: str
    confirmation_code: str
    new_password: str


# Endpoint to register a new user
@auth_router.post("/register")
async def register_user(model: RegisterModel):
    try:
        cognito_client.sign_up(
            ClientId=client_id,
            Username=model.username,
            Password=model.password,
            UserAttributes=[{"Name": "email", "Value": model.email}],
        )
        return {"message": "User registration initiated. Please confirm your email."}
    except cognito_client.exceptions.UsernameExistsException:
        raise HTTPException(status_code=400, detail="Username already exists")
    except cognito_client.exceptions.InvalidPasswordException as e:
        # Password did not meet policy requirements
        msg = e.response.get("Error", {}).get("Message", str(e))
        raise HTTPException(status_code=400, detail=msg)
    except cognito_client.exceptions.InvalidParameterException as e:
        # Missing or invalid parameters
        msg = e.response.get("Error", {}).get("Message", str(e))
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        logging.error(f"Error during sign up: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")


# Endpoint to confirm user registration
@auth_router.post("/confirm")
async def confirm_user(model: ConfirmModel):
    try:
        cognito_client.confirm_sign_up(
            ClientId=client_id, Username=model.username, ConfirmationCode=model.confirmation_code
        )
        return {"message": "User confirmed successfully"}
    except cognito_client.exceptions.CodeMismatchException:
        raise HTTPException(status_code=400, detail="Invalid confirmation code")
    except cognito_client.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=400, detail="Confirmation code expired")
    except Exception as e:
        logging.error(f"Error during confirmation: {e}")
        raise HTTPException(status_code=500, detail="Confirmation failed")


# Endpoint to log in and obtain JWT tokens
@auth_router.post("/login")
async def login_user(model: LoginModel):
    try:
        logging.info(f"Login attempt for username: {model.username}")
        logging.info(f"Using client_id: {client_id}")
        logging.info(f"Using user_pool_id: {user_pool_id}")

        resp = cognito_client.initiate_auth(
            ClientId=client_id,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": model.username, "PASSWORD": model.password},
        )

        logging.info(f"Cognito response keys: {list(resp.keys())}")

        # Check if Cognito returned a challenge
        if "ChallengeName" in resp:
            challenge_name = resp.get("ChallengeName")
            logging.info(f"Cognito challenge received: {challenge_name}")

            if challenge_name == "NEW_PASSWORD_REQUIRED":
                logging.error(f"User {model.username} must set a new password")
                raise HTTPException(
                    status_code=400, detail="RESET_PASSWORD_REQUIRED"  # Special code for frontend
                )
            elif challenge_name == "SOFTWARE_TOKEN_MFA":
                logging.error(f"MFA required for user {model.username}")
                raise HTTPException(
                    status_code=400,
                    detail="Multi-factor authentication is required but not supported in this app. Please contact support.",
                )
            elif challenge_name == "SMS_MFA":
                logging.error(f"SMS MFA required for user {model.username}")
                raise HTTPException(
                    status_code=400,
                    detail="SMS verification is required but not supported in this app. Please contact support.",
                )
            else:
                logging.error(f"Unsupported challenge: {challenge_name}")
                raise HTTPException(
                    status_code=400,
                    detail="Authentication requires additional steps not supported in this app. Please contact support.",
                )

        # Normal authentication flow
        auth_result = resp.get("AuthenticationResult", {})
        logging.info(f"AuthenticationResult keys: {list(auth_result.keys())}")

        # Log what tokens we received (but not their values for security)
        access_token = auth_result.get("AccessToken")
        id_token = auth_result.get("IdToken")
        refresh_token = auth_result.get("RefreshToken")

        logging.info(f"AccessToken present: {access_token is not None}")
        logging.info(f"IdToken present: {id_token is not None}")
        logging.info(f"RefreshToken present: {refresh_token is not None}")

        if not id_token:
            logging.error(
                "No IdToken received from Cognito - this should not happen in normal auth flow"
            )
            raise HTTPException(
                status_code=500, detail="No ID token received from authentication service"
            )

        response_data = {
            "access_token": access_token,
            "id_token": id_token,
            "refresh_token": refresh_token,
        }

        logging.info(f"Returning response with keys: {list(response_data.keys())}")
        return response_data

    except HTTPException:
        # Re-raise HTTP exceptions (these are our custom ones)
        raise
    except cognito_client.exceptions.NotAuthorizedException as e:
        logging.error(f"Invalid credentials for user {model.username}: {e}")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    except cognito_client.exceptions.UserNotConfirmedException:
        logging.error(f"User not confirmed: {model.username}")
        raise HTTPException(
            status_code=400,
            detail="Your account is not confirmed. Please check your email for a confirmation code and use the registration flow to confirm your account.",
        )
    except cognito_client.exceptions.UserNotFoundException:
        logging.error(f"User not found: {model.username}")
        raise HTTPException(status_code=401, detail="Invalid username or password")
    except cognito_client.exceptions.PasswordResetRequiredException as e:
        logging.error(f"Password reset required for user {model.username}: {e}")
        raise HTTPException(
            status_code=400, detail="RESET_PASSWORD_REQUIRED"
        )  # Special code for frontend
    except cognito_client.exceptions.TooManyRequestsException:
        logging.error(f"Too many requests for user {model.username}")
        raise HTTPException(
            status_code=429, detail="Too many login attempts. Please wait and try again later."
        )
    except Exception as e:
        logging.error(
            f"Unexpected error during login for {model.username}: {type(e).__name__}: {e}"
        )
        logging.error(f"Error details: {getattr(e, 'response', {})}")
        raise HTTPException(status_code=500, detail="Login failed due to server error")


# Endpoint to initiate password reset
@auth_router.post("/forgot-password")
async def forgot_password(model: ForgotPasswordModel):
    try:
        logging.info(f"Password reset request for username: {model.username}")
        cognito_client.forgot_password(ClientId=client_id, Username=model.username)
        logging.info(f"Password reset initiated for user: {model.username}")
        return {"message": "Password reset code sent to your email"}
    except cognito_client.exceptions.UserNotFoundException:
        # Don't reveal if user exists or not for security
        return {
            "message": "If the username exists, a password reset code has been sent to your email"
        }
    except cognito_client.exceptions.InvalidParameterException as e:
        msg = e.response.get("Error", {}).get("Message", str(e))
        raise HTTPException(status_code=400, detail=msg)
    except Exception as e:
        logging.error(f"Error during password reset for {model.username}: {e}")
        raise HTTPException(status_code=500, detail="Password reset failed")


# Endpoint to confirm password reset
@auth_router.post("/reset-password")
async def reset_password(model: ResetPasswordModel):
    try:
        logging.info(f"Password reset confirmation for username: {model.username}")
        cognito_client.confirm_forgot_password(
            ClientId=client_id,
            Username=model.username,
            ConfirmationCode=model.confirmation_code,
            Password=model.new_password,
        )
        logging.info(f"Password reset completed for user: {model.username}")
        return {"message": "Password reset successfully. You can now login with your new password."}
    except cognito_client.exceptions.CodeMismatchException:
        raise HTTPException(status_code=400, detail="Invalid confirmation code")
    except cognito_client.exceptions.ExpiredCodeException:
        raise HTTPException(
            status_code=400, detail="Confirmation code expired. Please request a new one."
        )
    except cognito_client.exceptions.InvalidPasswordException as e:
        msg = e.response.get("Error", {}).get("Message", str(e))
        raise HTTPException(status_code=400, detail=msg)
    except cognito_client.exceptions.UserNotFoundException:
        raise HTTPException(status_code=400, detail="Invalid username")
    except Exception as e:
        logging.error(f"Error during password reset confirmation for {model.username}: {e}")
        raise HTTPException(status_code=500, detail="Password reset confirmation failed")


# Fetch and cache JWKS for manual JWT verification
COGNITO_REGION = os.getenv("COGNITO_REGION", os.getenv("AWS_REGION", "us-east-1"))
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_JWKS_URL = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"
)


@lru_cache
def get_cognito_jwks():
    resp = httpx.get(COGNITO_JWKS_URL)
    resp.raise_for_status()
    return resp.json()


async def get_current_user(request: Request):
    # Parse and verify JWT from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    token = auth_header.split(" ", 1)[1]
    jwks = get_cognito_jwks()
    try:
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=401, detail="Public key not found in JWKS")
        claims = jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            audience=client_id,
            issuer=f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}",
        )
        return claims
    except JWTError as e:
        logging.error(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")


# Alias for backward compatibility/tests
get_user = get_current_user


# Dependency to extract user_id directly
async def get_user_id_from_token(user_claims: dict = Depends(get_current_user)):
    return user_claims.get("sub") or user_claims.get("username")


# Add a health check endpoint for debugging
@auth_router.get("/health")
async def health_check():
    """Health check endpoint to verify API connectivity"""
    return {
        "status": "healthy",
        "service": "auth",
        "cognito_configured": bool(client_id and user_pool_id),
        "region": region,
    }


# Add environment validation
def validate_cognito_config():
    """Validate that required Cognito environment variables are set"""
    missing = []
    if not user_pool_id:
        missing.append("COGNITO_USER_POOL_ID")
    if not client_id:
        missing.append("COGNITO_USER_POOL_CLIENT_ID")
    if not region:
        missing.append("AWS_REGION")

    if missing:
        logging.error(f"Missing required environment variables: {missing}")
        return False

    logging.info(
        f"Cognito configuration validated - Pool ID: {user_pool_id[:10]}..., Client ID: {client_id[:10]}..., Region: {region}"
    )
    return True


# Validate configuration on startup
if not validate_cognito_config():
    logging.critical("Cognito configuration invalid - authentication will not work")
