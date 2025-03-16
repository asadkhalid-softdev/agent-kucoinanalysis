from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated
import jwt
from jwt.exceptions import PyJWTError
from datetime import datetime

from config.settings import Settings

settings = Settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def verify_token(token: str) -> str:
    """
    Verify JWT token and return username
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        
        # Check if token is expired
        exp = payload.get("exp")
        if exp is None or datetime.utcnow().timestamp() > exp:
            raise credentials_exception
            
        return username
    except PyJWTError:
        raise credentials_exception

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> str:
    """
    Get current user from token
    """
    return await verify_token(token)
