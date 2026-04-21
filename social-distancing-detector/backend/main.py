from fastapi import FastAPI
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio, json

from stream import camera, generate_mjpeg
from pipeline import pipeline as frame_pipeline

@asynccontextmanager
async def lifespan(app: FastAPI):
    camera.start()
    print("[API] Camera started on startup")
    yield
    camera.stop()
    print("[API] Camera stopped on shutdown")

app = FastAPI(title="Social Distancing Detector", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return JSONResponse({"status": "ok", "message": "Social Distancing Detector API"})

@app.get("/video_feed")
def video_feed():
    return StreamingResponse(
        generate_mjpeg(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )

@app.get("/status")
def get_stats():
    frame = camera.read_frame()
    if frame is None:
        return JSONResponse({"error": "No frame"}, status_code=503)
    _, stats = frame_pipeline.process(frame)
    return JSONResponse(stats)

@app.get("/events")
def events():
    async def event_stream():
        while True:
            frame = camera.read_frame()
            if frame is not None:
                _, stats = frame_pipeline.process(frame)
                payload = json.dumps({
                    "alarm_state":      stats["alarm_state"],
                    "total_people":     stats["total_people"],
                    "violation_count":  stats["violation_count"],
                    "total_violations": stats["total_violations"],
                })
                yield f"data: {payload}\n\n"
            await asyncio.sleep(0.5)

    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no"
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
