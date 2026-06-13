import os
import jwt
import base64
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security = HTTPBearer()

def get_jwks_url():
    pub_key = os.getenv("CLERK_PUBLISHABLE_KEY", "")
    if pub_key.startswith("pk_test_") or pub_key.startswith("pk_live_"):
        try:
            # strip prefix
            prefix = "pk_test_" if pub_key.startswith("pk_test_") else "pk_live_"
            b64_part = pub_key.split(prefix)[1]
            # add padding if needed
            b64_part += "=" * ((4 - len(b64_part) % 4) % 4)
            domain = base64.b64decode(b64_part).decode('utf-8')
            if domain.endswith('$'):
                domain = domain[:-1]
            return f"https://{domain}/.well-known/jwks.json"
        except Exception:
            pass
    # hardcode fallback based on provided keys
    return "https://vast-ox-23.clerk.accounts.dev/.well-known/jwks.json"

jwks_client = jwt.PyJWKClient(get_jwks_url())

def verify_clerk_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        return payload.get("sub")
    except jwt.PyJWKClientError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to fetch JWKS to verify token",
        )
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
