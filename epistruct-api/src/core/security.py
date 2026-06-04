import httpx
from jose import JWTError, jwt
from jose.jwk import construct as jwk_construct

from src.core.config import settings

_jwks_cache: dict[str, dict] = {}


def _get_public_key(kid: str):
    if kid not in _jwks_cache:
        url = f"{settings.supabase_url}/auth/v1/.well-known/jwks.json"
        response = httpx.get(url, timeout=10)
        response.raise_for_status()
        for key in response.json().get("keys", []):
            _jwks_cache[key["kid"]] = key
    if kid not in _jwks_cache:
        raise ValueError(f"Unknown key ID: {kid}")
    return jwk_construct(_jwks_cache[kid])


def verify_supabase_jwt(token: str) -> dict:
    try:
        header = jwt.get_unverified_header(token)
        kid = header.get("kid")
        if not kid:
            raise ValueError("Missing kid in token header")
        public_key = _get_public_key(kid)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["ES256"],
            audience="authenticated",
        )
        return payload
    except JWTError as e:
        raise ValueError("Invalid token") from e
