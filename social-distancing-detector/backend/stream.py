import cv2
import threading
import numpy as np
import time
import asyncio
from typing import AsyncGenerator

from core.config import settings
from pipeline import pipeline

class CameraManager:
    def __init__(self):
        self.cap: cv2.VideoCapture | None = None
        self.lock = threading.Lock()
        self._running: bool = False

    def start(self) -> None:
        if self._running:
            return
            
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, 30)
        
        if not self.cap.isOpened():
            raise RuntimeError("Could not open webcam")
            
        self._running = True
        print("[CameraManager] Webcam started")

    def stop(self) -> None:
        if not self._running:
            return
            
        with self.lock:
            if self.cap is not None:
                self.cap.release()
            self.cap = None
            
        self._running = False
        print("[CameraManager] Webcam stopped")

    def read_frame(self) -> np.ndarray | None:
        with self.lock:
            if self.cap is None or not self._running:
                return None
            ret, frame = self.cap.read()
            if not ret:
                return None
            return frame

    def is_running(self) -> bool:
        return self._running

camera = CameraManager()

async def generate_mjpeg() -> AsyncGenerator[bytes, None]:
    if not camera.is_running():
        camera.start()
        
    while True:
        frame = camera.read_frame()
        if frame is None:
            await asyncio.sleep(0.01)
            continue
            
        annotated, stats = pipeline.process(frame)
        
        ret, buffer = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ret:
            continue
            
        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + buffer.tobytes()
            + b"\r\n"
        )
        
        await asyncio.sleep(1/30)

if __name__ == "__main__":
    camera.start()
    for _ in range(10):
        frame = camera.read_frame()
        if frame is not None:
            print(frame.shape)
        else:
            print("Failed to read frame")
        time.sleep(0.1) # small delay for frame capture
    camera.stop()
