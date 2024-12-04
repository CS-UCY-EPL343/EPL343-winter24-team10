from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = 'secret_key'
ALGORITHM = 'HS256' 
ACCESS_TOKEN_EXPIRE_MINUTES = 30 

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    """
    Create a JWT token with a specific expiration time.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta 
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES) 
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str):
    """
    Verify the JWT token and return the payload.
    If the token is invalid, raise an HTTPException.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

def create_email_verification_token(email: str):
    expiration = timedelta(hours=1)  # Token expires in 1 hour
    to_encode = {"sub": email, "exp": datetime.utcnow() + expiration}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
  