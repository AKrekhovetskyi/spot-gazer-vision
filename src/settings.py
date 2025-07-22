import os

CONFIDENCE = 0.1  # Confidence threshold.
IOU = 0.7  # IoU threshold.

# Default classes.
CAR = 2
MOTORCYCLE = 3
BUS = 5
TRUCK = 7

# The classes on the basis of which the dataset was collected.
CLASS_CAR = 0
CLASS_FREE = 1

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
    "classes": [CAR, MOTORCYCLE, BUS, TRUCK],
    "show_boxes": False,
    "verbose": False,
    "vid_stride": 10,
}

# Set separate global logging level for console and file.
# Supported values: DEBUG, INFO, WARNING, ERROR, CRITICAL.
CONSOLE_LOG_LEVEL = "DEBUG"
FILE_LOG_LEVEL = "DEBUG" if __debug__ else "WARNING"

SPOTGAZER_URL = os.environ["SPOTGAZER_URL"]
SERVICE_USERNAME = os.environ["SERVICE_USERNAME"]
SERVICE_PASSWORD = os.environ["SERVICE_PASSWORD"]
