from dataclasses import dataclass

@dataclass
class Settings:
    FRAME_WIDTH: int = 640
    FRAME_HEIGHT: int = 480
    MOG2_HISTORY: int = 500
    MOG2_VAR_THRESHOLD: float = 50.0
    MOG2_DETECT_SHADOWS: bool = False
    MORPH_KERNEL_SIZE: tuple = (5, 5)
    MIN_CONTOUR_AREA: int = 800
    NMS_IOU_THRESHOLD: float = 0.3
    DISTANCE_THRESHOLD_PX: int = 150
    ALARM_COOLDOWN_FRAMES: int = 30

settings = Settings()
