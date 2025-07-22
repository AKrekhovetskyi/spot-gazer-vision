from datetime import UTC, datetime

from aiohttp import ClientSession
from jwt import decode

from .settings import SERVICE_PASSWORD, SERVICE_USERNAME, SPOTGAZER_URL

TOKEN_URL = "/api/token/"  # noqa: S105
TOKEN_REFRESH_URL = "/api/token/refresh/"  # noqa: S105


class AiohttpJWTClient:
    """
    Asynchronous JWT authentication client for interacting with the SpotGazer API.

    This client manages access and refresh tokens, automatically refreshing them as needed.
    It uses an aiohttp ClientSession for HTTP requests and sets the Authorization header
    for authenticated requests.

    Usage:
        client = AiohttpJWTClient()
        await client.refresh_tokens()  # Ensure tokens are valid before making requests.

    Note:
        - Remember to close the session after use to free resources.
        - Token expiration is handled automatically, but you must call `refresh_tokens`
          before making requests to ensure valid authentication.
    """

    def __init__(self) -> None:
        # NOTE: remember to close the session!
        self.session = ClientSession(SPOTGAZER_URL)
        self.__access_token: str
        self.__refresh_token: str
        self._access_token_expiration: datetime
        self._refresh_token_expiration: datetime | None = None

    async def refresh_tokens(self) -> None:
        """Refresh tokens and update the default authorization header."""
        if not self._refresh_token_expiration or datetime.now(UTC) > self._refresh_token_expiration:
            async with self.session.post(
                TOKEN_URL, json={"username": SERVICE_USERNAME, "password": SERVICE_PASSWORD}
            ) as response:
                tokens = await response.json()
                self.__access_token = tokens["access"]
                self.__refresh_token = tokens["refresh"]
        elif datetime.now(UTC) > self._access_token_expiration:
            async with self.session.post(TOKEN_REFRESH_URL, json={"refresh": self.__refresh_token}) as response:
                self.__access_token = (await response.json())["access"]

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
