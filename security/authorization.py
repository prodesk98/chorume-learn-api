from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from config import env

bearer_scheme = HTTPBearer()


def validate_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)) -> HTTPAuthorizationCredentials:
    if credentials.scheme != "Bearer" or credentials.credentials != env.LEARN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing token")
    return credentials

