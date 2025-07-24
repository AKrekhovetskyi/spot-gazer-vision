import sys
from asyncio import CancelledError, run, wait_for
from datetime import UTC, datetime
from multiprocessing import Process
from time import sleep

from src.settings import MAX_STREAMS, STREAMS_USAGE_DURATION
from src.spot_gazer import SpotGazer


async def run_prediction() -> None:
    spot_gazer = SpotGazer()
    try:
        await wait_for(
            spot_gazer.start_detection(datetime.now(UTC) + STREAMS_USAGE_DURATION, MAX_STREAMS),
            STREAMS_USAGE_DURATION.seconds,
        )
    except (KeyboardInterrupt, CancelledError, TimeoutError):
        pass
    finally:
        await spot_gazer.stop_detection()


def run_sync_prediction() -> None:
    run(run_prediction())


def main() -> None:
    times_to_wait = 12  # 1 minute with a 5-second interval between waits.
    while times_to_wait > 0:
        # Running `SpotGazer` in a loop leads to a memory leak because resources are not released
        # when the detection terminates. The solution is to use a process.
        # Inspired by https://github.com/ultralytics/ultralytics/issues/6981.
        process = Process(target=run_sync_prediction)
        process.start()
        process.join()
        if process.exitcode != 0:
            times_to_wait -= 1
            sleep(5)
    sys.exit(1)  # The function is expected to run forever.


if __name__ == "__main__":
    main()
