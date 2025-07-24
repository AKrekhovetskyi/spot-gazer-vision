from asyncio import wait_for
from datetime import UTC, datetime
from typing import Any
from unittest.mock import patch

import pytest
from faker import Faker

from src import SpotGazer
from src.aiohttp_jwt_client import AiohttpJWTClient
from src.settings import STREAMS_USAGE_DURATION


@pytest.fixture
def video_stream_sources(faker: Faker) -> dict[str, list[dict[str, Any]]]:
    return {
        "results": [
            {
                "parking_lot_address": faker.pystr(),
                "parking_lot_id": faker.pyint(),
                "processing_rate": faker.pyint(min_value=1, max_value=3),
                "streams": [
                    {
                        "id": faker.pyint(),
                        "stream_source": "https://www.youtube.com/watch?v=LcSaBafrb-w&ab_channel=LingoNetworks",
                        "is_active": True,
                        "in_use_until": None,
                    }
                    for _ in range(2)
                ],
            },
            {
                "parking_lot_address": faker.pystr(),
                "parking_lot_id": faker.pyint(),
                "processing_rate": faker.pyint(min_value=1, max_value=3),
                "streams": [
                    {
                        "id": faker.pyint(),
                        "stream_source": faker.url(),
                        "is_active": True,
                        "in_use_until": None,
                    }
                ],
            },
        ]
    }


class TestSpotGazer:
    async def test_start_stop_detection(self, video_stream_sources: dict[str, list[dict[str, Any]]]) -> None:
        with patch.object(AiohttpJWTClient, "request_json") as mock:
            mock.return_value = video_stream_sources

            spot_gazer = SpotGazer()
            try:
                await wait_for(spot_gazer.start_detection(datetime.now(UTC) + STREAMS_USAGE_DURATION), 15)
            except (KeyboardInterrupt, TimeoutError):
                await spot_gazer.stop_detection()
