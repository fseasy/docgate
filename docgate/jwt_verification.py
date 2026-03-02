"""based on https://gist.github.com/rishabhpoddar/ea31502923ec9a53136371f2b6317ffa
it's a sync version.
with Gemini3 help, created the async version.
"""

import asyncio
import time
from typing import Self, TypedDict, TypeVar

import httpx
from jwt import PyJWK, PyJWKClient, decode, get_unverified_header
from jwt.exceptions import DecodeError, PyJWKClientError
from pydantic import BaseModel, Field, field_validator

from .config import LOGGER as logger, SUPERTOKENS_CONNECTION_URI


class _AsyncJWKManager:
  def __init__(self, jwks_uri: str, cache_ttl: int = 10 * 60):
    """
    Args:
      jwks_uri: url for jwks
      cache_ttl: TTL for cache in minutes. default 10min as ChatGPT recommended
    """
    self.jwks_uri = jwks_uri
    self.cache_ttl = cache_ttl
    self._jwks_client = PyJWKClient(jwks_uri)
    self._signing_keys: dict[str, PyJWK] = {}  # Map kid -> PyJWK
    self._last_refresh_time = 0.0
    self._lock = asyncio.Lock()  # asyncio lock to prevent cache stampede

  def _is_cache_fresh(self) -> bool:
    """Check if cache is fresh"""
    return (time.time() - self._last_refresh_time) < self.cache_ttl

  async def _refresh_keys(self) -> None:
    """
    Asynchronously refresh JWKS.
    Uses httpx instead of requests to avoid blocking the event loop.
    """
    try:
      async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.get(self.jwks_uri)
        resp.raise_for_status()
        jwk_set = resp.json()

      # Update in-memory cache
      new_keys = {}
      for jwk_data in jwk_set.get("keys", []):
        try:
          key = PyJWK(jwk_data)
          new_keys[jwk_data["kid"]] = key
        except Exception as e:
          logger.warning(f"Failed to parse JWK: {e}")

      self._signing_keys = new_keys
      self._last_refresh_time = time.time()
      logger.info("JWKS refreshed")

    except Exception as e:
      logger.error(f"Failed to fetch JWKS: {e}")
      raise

  async def get_signing_key(self, kid: str) -> PyJWK:
    """
    Get the signing public key for a specific kid.
    Logic:
    1. Check in-memory cache -> Return if hit.
    2. Cache expired or miss -> Acquire lock -> Double check cache.
    3. Still missing -> Trigger network request to refresh.
    """
    # 1. Fast path: Read operations don't need a lock because asyncio
    # is single-threaded and dictionary lookups are atomic.
    if self._is_cache_fresh() and kid in self._signing_keys:
      return self._signing_keys[kid]

    # 2. Slow path: Refresh required
    async with self._lock:
      # Double check: Another coroutine might have just finished refreshing
      if self._is_cache_fresh() and kid in self._signing_keys:
        return self._signing_keys[kid]

      # Must refresh
      await self._refresh_keys()

      if kid in self._signing_keys:
        return self._signing_keys[kid]

      # If still not found after refresh, the kid in the token is invalid or deleted
      raise PyJWKClientError(f"Unable to find a signing key that matches '{kid}'")


# Global Singleton
_JWKS_URI = f"{SUPERTOKENS_CONNECTION_URI}/.well-known/jwks.json"
_jwk_manager = _AsyncJWKManager(_JWKS_URI)


T = TypeVar("T")


class RawVersionedValue[T](TypedDict):
  v: T
  t: int


class VersionedValue[T](BaseModel):
  value: T
  updated_at: int

  @classmethod
  def from_raw(cls, data: RawVersionedValue[T]) -> Self:
    return cls(value=data["v"], updated_at=data["t"])


class AuthJWTPayload(BaseModel):
  # === standard JWT ===
  issued_at: int = Field(alias="iat")
  expires_at: int = Field(alias="exp")
  issuer: str = Field(alias="iss")

  # === id ===
  user_id: str = Field(alias="sub")
  refresh_subject: str = Field(alias="rsub")
  tenant_id: str = Field(alias="tId")

  # === session ===
  session_handle: str = Field(alias="sessionHandle")
  refresh_token_hash: str | None = Field(default=None, alias="refreshTokenHash1")
  parent_refresh_token_hash: str | None = Field(default=None, alias="parentRefreshTokenHash1")
  anti_csrf_token: str | None = Field(default=None, alias="antiCsrfToken")

  # === business ===
  email: str

  email_verified: VersionedValue[bool] | None = Field(default=None, alias="st-ev")
  roles: VersionedValue[list[str]] | None = Field(default=None, alias="st-role")
  permissions: VersionedValue[list[str]] | None = Field(default=None, alias="st-perm")

  @field_validator("email_verified", "roles", "permissions", mode="before")
  @classmethod
  def parse_versioned(cls, v: RawVersionedValue[T]) -> VersionedValue[T]:
    if v is None:
      return None
    return VersionedValue.from_raw(v)

  class Config:
    populate_by_name = True
    extra = "ignore"


async def verify_jwt(token: str) -> AuthJWTPayload:
  """
  token: asAccessToken string (from Cookies, request.cookies.get("sAccessToken"))

  Exceptions:
    DecodeError
    PyJWKClientError

  """
  try:
    # 1. Extract kid (Key ID) from Header.
    # This is a pure CPU operation and very fast, no await needed.
    header = get_unverified_header(token)
    kid = header.get("kid")
    if not kid:
      raise DecodeError("Token header missing 'kid'")

    # 2. Get public key (Async I/O).
    # If cache hits, this is instantaneous.
    signing_key = await _jwk_manager.get_signing_key(kid)

    # 3. Verify signature (CPU-intensive -> Offload to thread pool).
    # RSA decryption is fast but can briefly block the EventLoop under high concurrency.
    # Offloading to executor ensures other Nginx requests are not stuck.
    loop = asyncio.get_running_loop()
    payload = await loop.run_in_executor(
      None,  # Use the default ThreadPoolExecutor
      lambda: decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        # supertokens access-token doesn't have aud field, so don't verify it
        options={
          "verify_signature": True,
          "verify_exp": True,
          "verify_iss": True,  # auth server
        },
      ),
    )

    return AuthJWTPayload.model_validate(payload)

  except Exception as e:
    raise e
