from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

SECRET_KEY = "amin1998@" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

security = HTTPBearer()

class AuthenticationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        if self._should_skip_auth(request.url.path):
            return await call_next(request)

        try:
            auth_header = request.headers.get("Authorization")
            if not auth_header:
                raise HTTPException(tatus_code=401,
                    detail="Missing authentication token"
                )
            token = auth_header.split(" ")[1]
            payload = self._decode_token(token)

            request.state.user_id = payload.get("sub")
            request.state.user_role = payload.get("role")
            return await call_next(request)

        except (JWTError, IndexError):
            raise HTTPException(status_code=401,
                detail="invalid authentication token"
            )

    def _should_skip_auth(self, path: str) -> bool:
        public_paths = {"/health",
            "/api/users/register",
            "/api/users/login",
            "/docs",
            "/openapi.json"}

        return any(path.startswith(p) for p in public_paths)
    def _decode_token(self, token: str) -> dict:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def create_access_token(data: dict,expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)



def get_current_user_id(request: Request) -> str:
    if not hasattr(request.state, "user_id"):
        raise HTTPException(status_code=401,
            detail="Not authsnticated")
    return request.state.user_id