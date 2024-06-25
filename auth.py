import os
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Import your secret token 
from dotenv import load_dotenv

load_dotenv()
SECRET_TOKEN = os.getenv("SECRET_TOKEN")

security = HTTPBearer()

async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """
    Authenticates the user using a Bearer Token.
    """
    if credentials.scheme != "Bearer":
        raise HTTPException(status_code=401, detail="Invalid authentication scheme")

    if credentials.credentials != SECRET_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid token")

    return credentials