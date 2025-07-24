import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from ultralytics import YOLO
from ultralytics.data.loaders import get_best_youtube_url
from ultralytics.utils import SETTINGS
from yt_dlp.utils import DownloadError

from .aiohttp_jwt_client import AiohttpJWTClient
from .logging_config import logging
from .settings import (
    SERVICE_PASSWORD,
    SERVICE_USERNAME,
    SPOTGAZER_BASE_URL,
    TOKEN_REFRESH_URL,
    TOKEN_URL,
    YOLO_PREDICTION_PARAMETERS,
)

SETTINGS.update({"sync": False})  # Prevent sync analytics and crashes with Ultralytics HUB (Google Analytics).
logger = logging.getLogger(__name__)


class NoVideoStreamsAvailableError(Exception): ...


class SpotGazer:
    """Detect parking spot occupancy in concurrent mode."""

    def __init__(
        self,
        model: str | Path = YOLO_PREDICTION_PARAMETERS["model"],  # type: ignore[assignment]
        task: str = YOLO_PREDICTION_PARAMETERS["task"],
    ) -> None:
        self._model = model
        self._task = task
        self.http_client = AiohttpJWTClient(
            username=SERVICE_USERNAME,
            password=SERVICE_PASSWORD,
            api_token_url=TOKEN_URL,
            api_token_refresh_url=TOKEN_REFRESH_URL,
            base_url=SPOTGAZER_BASE_URL,
        )
        self._yolo_models: list[YOLO] = []
        self._gathered_tasks = []

    async def start_detection(self, mark_streams_in_use_until: datetime, limit_streams: int = 20) -> None:
        """Start separate asynchronous task for each parking lot. One parking lot can have several camera streams."""
        video_stream_sources = await self.http_client.request_json(
            "/api/video-stream-sources/",
            params={
                "active_only": int(True),
                "limit": limit_streams,
                "mark_in_use_until": mark_streams_in_use_until.isoformat(),
            },
        )
        parking_lot_video_streams: list[dict[str, Any]] = video_stream_sources["results"]
        if not parking_lot_video_streams:
            raise NoVideoStreamsAvailableError

        logger.info("Occupancy detection of %d parking lots has been started!", len(parking_lot_video_streams))
        self._gathered_tasks = cast(
            "list[asyncio.Future]",
            await asyncio.gather(
                *(self._detect_parking_occupancy(parking_streams) for parking_streams in parking_lot_video_streams),
            ),
        )

    async def stop_detection(self) -> None:
        # Terminate all video stream loaders.
        (yolo.predictor.dataset.close() for yolo in self._yolo_models)  # type: ignore[reportOptionalMemberAccess]
        self._yolo_models.clear()
        (task.cancel() for task in self._gathered_tasks)
        self._gathered_tasks.clear()
        await self.http_client.close()
        logger.info("Detection stopped!")

    @staticmethod
    async def _deactivate_broken_stream(id_: int) -> None:
        # TODO @AKrekhovetskyi: make post request to the server to deactivate the stream  # noqa: FIX002
        # https://github.com/AKrekhovetskyi/spot-gazer-vision/issues/3
        logger.warning("Parking lot stream %d is not active anymore.", id_)

    async def _detect_parking_occupancy(self, parking_streams: dict[str, Any]) -> None:
        logger.info("Determining the occupancy of parking lot ID %d", parking_streams["parking_lot_id"])
        active_streams = []
        for stream in parking_streams["streams"]:
            if "youtube" in stream["stream_source"]:
                try:
                    stream["stream_source"] = get_best_youtube_url(stream["stream_source"], method="yt-dlp")
                except DownloadError:
                    logger.exception("Can't get best YouTube URL of stream ID %s", stream["id"])
                    await self._deactivate_broken_stream(stream["id"])
                    continue

            # Initialize predictor. Pass `show=True` to display the stream.
            yolo = YOLO(model=self._model, task=self._task)
            self._yolo_models.append(yolo)
            stream["predictor"] = yolo.predict(
                source=stream["stream_source"], stream=True, **YOLO_PREDICTION_PARAMETERS
            )
            active_streams.append(stream)

        # Continuously process frames from the video streams.
        while True:
            if not active_streams:
                logger.warning("No active streams left on parking lot ID %d", parking_streams["parking_lot_id"])
                break

            detected_vehicles = 0
            for stream in active_streams:
                try:
                    # NOTE: Sometimes the video steam may become unavailable.
                    # In this case, there is a potential risk of an even loop blockage.
                    # Stay tuned for this! It's possible to use signals with alarm to cancel such a coroutine.
                    detected_vehicles += len(next(stream["predictor"]))
                except (StopIteration, ConnectionError):
                    logger.exception("Unexpected inference stop of stream ID %s", stream["id"])
                    await self._deactivate_broken_stream(stream["id"])
                    active_streams.remove(stream)
                    break
            else:
                occupancy = await self.http_client.request_json(
                    "/api/occupancy/",
                    method="post",
                    data={"parking_lot_id": parking_streams["parking_lot_id"], "occupied_spots": detected_vehicles},
                )
                logger.debug(occupancy)
                # Sleep for the specified processing rate before processing the next frame
                await asyncio.sleep(parking_streams["processing_rate"])
