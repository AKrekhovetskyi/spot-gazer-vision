from datetime import UTC, datetime
from typing import Any, Literal

from aiohttp import ClientSession
from aiohttp.typedefs import StrOrURL
from jwt import decode

from .logging_config import logging

logger = logging.getLogger(__file__)


class AiohttpJWTClient:
    """Asynchronous HTTP client with a JWT authentication built-in.

    The client ensure the JWT authentication provided by the Simple JWT library:
    https://django-rest-framework-simplejwt.readthedocs.io/en/latest/

    This client manages access and refresh tokens, automatically refreshing them as needed.
    It uses an aiohttp ClientSession for HTTP requests and sets the Authorization header
    for authenticated requests.

    Usage:
    ```python
    client = AiohttpJWTClient(
        username="admin",
        password="1234",
        api_token_url="/token/",
        api_token_refresh_url="/token/refresh/",
        base_url="http://api.example.org",
    )
    await client.request_json("/api/")
    await client.close()
    ```

    Note:
        - Remember to close the session after use to free resources.
        - Tokens expiration is handled automatically.
        - The bearer `Authorization` header is set by default.
    """

    def __init__(
        self,
        *,
        username: str,
        password: str,
        api_token_url: StrOrURL,
        api_token_refresh_url: StrOrURL,
        base_url: StrOrURL | None = None,
    ) -> None:
        self.__username = username
        self.__password = password
        self.api_token_url = api_token_url
        self.api_token_refresh_url = api_token_refresh_url
        # NOTE: remember to close the session!
        self.session = ClientSession(base_url)

        self.__access_token: str
        self.__refresh_token: str
        self._access_token_expiration: datetime
        self._refresh_token_expiration: datetime | None = None

    async def request_json(
        self, url: str, method: Literal["get", "post", "put", "patch", "delete"] = "get", **kwargs: Any
    ) -> dict[str, Any]:
        await self.refresh_tokens()
        async with getattr(self.session, method)(url, **kwargs) as response:
            return await response.json()

    async def refresh_tokens(self) -> None:
        """Refresh tokens and update the default authorization header."""
        if not self._refresh_token_expiration or datetime.now(UTC) > self._refresh_token_expiration:
            async with self.session.post(
                self.api_token_url, json={"username": self.__username, "password": self.__password}
            ) as response:
                tokens = await response.json()
                self.__access_token = tokens["access"]
                self.__refresh_token = tokens["refresh"]
        elif datetime.now(UTC) > self._access_token_expiration:
            async with self.session.post(
                self.api_token_refresh_url, json={"refresh": self.__refresh_token}
            ) as response:
                self.__access_token = (await response.json())["access"]
        else:
            return
        self._extract_tokens_expiration_datetime()
        self.session.headers["Authorization"] = f"Bearer {self.__access_token}"

    def _extract_tokens_expiration_datetime(self) -> None:
        decoded_access_token = decode(self.__access_token, options={"verify_signature": False})
        self._access_token_expiration = datetime.fromtimestamp(decoded_access_token["exp"], tz=UTC)

        decoded_refresh_token = decode(self.__refresh_token, options={"verify_signature": False})
        self._refresh_token_expiration = datetime.fromtimestamp(decoded_refresh_token["exp"], tz=UTC)

    async def close(self) -> None:
        """Shortcut for the `self.session.close`."""
        await self.session.close()
