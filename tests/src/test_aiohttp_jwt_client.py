from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from aiohttp import web
from aiohttp.pytest_plugin import AiohttpClient
from aiohttp.test_utils import TestClient
from faker import Faker
from jwt import encode

from src.aiohttp_jwt_client import TOKEN_REFRESH_URL, TOKEN_URL, AiohttpJWTClient

fake = Faker()


@pytest.fixture
def auth_token_payload() -> dict[str, Any]:
    user_pk = fake.pyint(min_value=1)
    return {
        "access": {
            "user_pk": user_pk,
            "token_type": "access",
            "cold_stuff": "☃",
            "exp": (datetime.now(UTC) + timedelta(minutes=5)).timestamp(),
            "jti": fake.pystr(),
        },
        "refresh": {
            "user_pk": user_pk,
            "token_type": "refresh",
            "cold_stuff": "☃",
            "exp": (datetime.now(UTC) + timedelta(hours=24)).timestamp(),
            "jti": fake.pystr(),
        },
    }


@pytest.fixture
def auth_tokens(auth_token_payload: dict[str, Any]) -> dict[str, str]:
    """Simulate Simple JWT payload.

    https://github.com/jazzband/djangorestframework-simplejwt/blob/master/rest_framework_simplejwt/tokens.py
    https://github.com/jazzband/djangorestframework-simplejwt/blob/master/rest_framework_simplejwt/serializers.py
    """
    algorithm = "HS256"
    key = fake.pystr()
    return {
        "access": encode(auth_token_payload["access"], key, algorithm=algorithm),
        "refresh": encode(auth_token_payload["refresh"], key, algorithm=algorithm),
    }


@pytest.fixture
async def test_client(
    aiohttp_client: AiohttpClient, auth_tokens: dict[str, str]
) -> TestClient[web.Request, web.Application]:
    async def post_handler(request: web.Request) -> web.Response:
        request_body = await request.json()
        if "username" in request_body:
            return web.json_response(auth_tokens)
        return web.json_response(
            {
                # Use created JWT to simplify testing.
                "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX3BrIjoyMTE3LCJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiY29"
                "sZF9zdHVmZiI6Ilx1MjYwMyIsImV4cCI6MTc1MzE5MzU0OC44NjY0MjMsImp0aSI6IlVCTG1CZXFSc2ZKZGxTZ01xUVZnIn0.jILM5"
                "YgRJkIprMaEjcR1OJ9_HTqOhyST7GXWjZr6BLQ"
            }
        )

    app = web.Application()
    app.router.add_post(TOKEN_URL, post_handler)
    app.router.add_post(TOKEN_REFRESH_URL, post_handler)
    return await aiohttp_client(app)


@pytest.fixture
async def aiohttp_jwt_client(test_client: TestClient) -> AsyncIterator[AiohttpJWTClient]:
    client = AiohttpJWTClient()
    await client.session.close()
    test_client.headers = {}  # type: ignore[reportAttributeAccessIssue]
    client.session = test_client  # type: ignore[reportAttributeAccessIssue]
    yield client
    await client.session.close()


class TestAiohttpJWTClient:
    async def test__extract_token_expiration_datetime(
        self, auth_token_payload: dict[str, Any], auth_tokens: dict[str, str], aiohttp_jwt_client: AiohttpJWTClient
    ) -> None:
        aiohttp_jwt_client._AiohttpJWTClient__access_token = auth_tokens["access"]  # type: ignore[reportAttributeAccessIssue]
        aiohttp_jwt_client._AiohttpJWTClient__refresh_token = auth_tokens["refresh"]  # type: ignore[reportAttributeAccessIssue]
        aiohttp_jwt_client._extract_tokens_expiration_datetime()

        access_token_expiration = datetime.fromtimestamp(auth_token_payload["access"]["exp"], tz=UTC)
        assert aiohttp_jwt_client._access_token_expiration == access_token_expiration

        refresh_token_expiration = datetime.fromtimestamp(auth_token_payload["refresh"]["exp"], tz=UTC)
        assert aiohttp_jwt_client._refresh_token_expiration == refresh_token_expiration

    async def test_refresh_tokens(self, aiohttp_jwt_client: AiohttpJWTClient) -> None:
        assert not aiohttp_jwt_client._refresh_token_expiration
        await aiohttp_jwt_client.refresh_tokens()
        # Make sure the attributes have been populated.
        access_token_expiration = aiohttp_jwt_client._access_token_expiration
        assert access_token_expiration
        assert aiohttp_jwt_client._refresh_token_expiration
        access_token = aiohttp_jwt_client._AiohttpJWTClient__access_token  # type: ignore[reportAttributeAccessIssue]
        assert access_token
        assert aiohttp_jwt_client._AiohttpJWTClient__refresh_token  # type: ignore[reportAttributeAccessIssue]

        # Simulate access token expiration scenario.
        aiohttp_jwt_client._access_token_expiration -= timedelta(hours=fake.pyint(min_value=1, max_value=12))
        await aiohttp_jwt_client.refresh_tokens()
        assert aiohttp_jwt_client._AiohttpJWTClient__access_token != access_token  # type: ignore[reportAttributeAccessIssue]
        assert aiohttp_jwt_client._access_token_expiration != access_token_expiration
