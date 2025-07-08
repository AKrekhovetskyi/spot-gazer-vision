import asyncio
from pathlib import Path
from typing import Any, cast

from ultralytics import YOLO
from ultralytics.utils import SETTINGS

from .logging_config import logging
from .settings import YOLO_PREDICTION_PARAMETERS

SETTINGS.update({"sync": False})  # Prevent sync analytics and crashes with Ultralytics HUB (Google Analytics).
logger = logging.getLogger(__name__)


class SpotGazer(YOLO):
    """Detect parking spot occupancy in concurrent mode."""

    def __init__(
        self,
        parking_lots: list[list[dict[str, Any]]],
        model: str | Path = YOLO_PREDICTION_PARAMETERS["model"],  # type: ignore[assignment]
        task: str = YOLO_PREDICTION_PARAMETERS["task"],
    ) -> None:
        """
        :param parking_lots: dictionary list of all video sources. Dictionary fields:
        - parking_lot_id: int
        - stream_source: str
        - processing_rate: int
        """
        super().__init__(model, task)
        # Initializing parking lots and gathering detection coroutines.
        self.parking_lots = parking_lots
        self._gathered_tasks = []

    async def start_detection(self) -> None:
        """Start separate asynchronous tasks for each parking lot. One parking lot can have several camera streams."""
        logger.info("Occupancy detection of %d parking lots has been started!", len(self.parking_lots))
        self._gathered_tasks = cast(
            "list[asyncio.Future]",
            await asyncio.gather(
                *(self._detect_parking_occupancy(parking_lot) for parking_lot in self.parking_lots),
            ),
        )

    def stop_detection(self) -> None:
        (task.cancel() for task in self._gathered_tasks)
        logger.info("Detection stopped!")

    @staticmethod
    async def _deactivate_broken_stream(parking_lot_id: int) -> None:
        # TODO @AKrekhovetskyi: make post request to the server to deactivate the stream  # noqa: FIX002
        # https://github.com/AKrekhovetskyi/spot-gazer-vision/issues/3
        logger.warning("Parking lot %d is not active anymore.", parking_lot_id)

    async def _detect_parking_occupancy(self, parking_streams: list[dict[str, Any]]) -> None:
        logger.info("Determining the occupancy of parking lot №%d", parking_streams[0]["parking_lot_id"])
        active_streams = []
        for stream in parking_streams:
            try:
                # Initialize predictor.
                stream["prediction"] = self.predict(
                    source=stream["stream_source"], stream=True, **YOLO_PREDICTION_PARAMETERS
                )
            except OSError:
                logger.exception("Error while processing stream %s", stream["stream_source"])
                await self._deactivate_broken_stream(stream["parking_lot_id"])
                continue
            active_streams.append(stream)

        # Continuously process frames from the video streams.
        while True:
            if not active_streams:
                break

            detected_vehicles = 0
            for stream in active_streams:
                try:
                    detected_vehicles += len(next(stream["prediction"]))
                except (StopIteration, ConnectionError):
                    await self._deactivate_broken_stream(stream["parking_lot_id"])
                    active_streams.remove(stream)
                    break
            else:
                await self._save_occupancy(active_streams[0]["parking_lot_id"], detected_vehicles)
                detected_vehicles = 0

                # Sleep for the specified processing rate before processing the next frame
                await asyncio.sleep(active_streams[0]["processing_rate"])

    @staticmethod
    async def _save_occupancy(parking_lot_id: int, occupied_spots: int) -> None:
        # TODO @AKrekhovetskyi: make post request to the server to save predicted occupancy  # noqa: FIX002
        # https://github.com/AKrekhovetskyi/spot-gazer-vision/issues/4
        logger.debug("Parking lot: %d; occupied spots: %d.", parking_lot_id, occupied_spots)
