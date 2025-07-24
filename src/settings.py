import os
from datetime import timedelta

CONFIDENCE = 0.25
IOU = 0.7

# Default classes.
CAR = 2
MOTORCYCLE = 3
TRUCK = 7

# Inference arguments:
# https://docs.ultralytics.com/modes/predict/#inference-arguments
YOLO_PREDICTION_PARAMETERS = {
    "save": False,
    "single_cls": False,
    "model": "yolo11n.pt",
    "data": "/content/datasets/parking_dataset/data.yaml",
    "task": "detect",
    "half": True,
    "conf": CONFIDENCE,
    "iou": IOU,
    "imgsz": 640,
    "show_labels": False,
    "classes": [CAR, MOTORCYCLE, TRUCK],
    "show_boxes": False,
    "verbose": False,
    "vid_stride": 10,
}

STREAMS_USAGE_DURATION = timedelta(minutes=30)
MAX_STREAMS = 10
"""
The required processing power grows significantly with every new stream.
"""

# Set separate global logging level for console and file.
# Supported values: DEBUG, INFO, WARNING, ERROR, CRITICAL.
CONSOLE_LOG_LEVEL = os.getenv("CONSOLE_LOG_LEVEL", "DEBUG")
FILE_LOG_LEVEL = "DEBUG" if __debug__ else os.getenv("FILE_LOG_LEVEL", "WARNING")

SPOTGAZER_BASE_URL = os.environ["SPOTGAZER_BASE_URL"]
SERVICE_USERNAME = os.environ["SERVICE_USERNAME"]
SERVICE_PASSWORD = os.environ["SERVICE_PASSWORD"]
TOKEN_URL = "/api/token/"  # noqa: S105
TOKEN_REFRESH_URL = "/api/token/refresh/"  # noqa: S105
