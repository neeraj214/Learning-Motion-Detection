# Learning Motion Detection

A hands-on monorepo for learning real-time motion detection and computer vision with Python and OpenCV.

---

## Projects

### 1. Background Subtraction Demo

A real-time motion detection system using classic computer vision techniques.

| Path | `Background-Subtraction-Demo/` |
|------|-------------------------------|
| Backend | Flask (Python) |
| Frontend | React |
| Algorithm | MOG2 background subtraction |

**Architecture**

```
Background-Subtraction-Demo/
├── motion_detection/
│   ├── main.py       ← Full detection loop (Phases 2-5): camera, MOG2, contours, logging
│   ├── app.py        ← Flask server: MJPEG stream + motion status API
│   ├── webcam_test.py
│   └── motion_log.txt
└── frontend/         ← React UI
```

**Key Features**
- MOG2 background subtraction with Gaussian pre-blur
- Morphological cleanup (open → close → dilate)
- Contour filtering by minimum area
- Real-time MJPEG streaming via Flask (`/video_feed`)
- Motion state REST API (`/motion_status`, `/set_threshold`)
- Motion event logging to `motion_log.txt`

**Running**

```bash
# Backend
cd Background-Subtraction-Demo/motion_detection
pip install flask flask-cors opencv-python
python app.py          # streams on http://localhost:5000

# Standalone (no server needed)
python main.py         # opens local OpenCV window

# Frontend
cd ../frontend
npm install && npm start
```

---

### 2. Social Distancing Detector

A modular people-tracking and social distancing violation detection system.

| Path | `social-distancing-detector/` |
|------|------------------------------|
| Backend | FastAPI (Python) |
| Frontend | React (scaffold) |
| Algorithm | MOG2 + NMS + CentroidTracker |

**Architecture**

```
social-distancing-detector/
└── backend/
    ├── main.py          ← CLI entry point (windowed / headless)
    ├── stream.py        ← FastAPI MJPEG + JSON status API
    ├── requirements.txt
    └── core/
        ├── config.py    ← Settings dataclass
        ├── detector.py  ← Detector (MOG2 + NMS + process_frame_with_ids)
        └── tracker.py   ← CentroidTracker (persistent IDs across frames)
```

**Key Features**
- `CentroidTracker`: persistent object IDs across frames using greedy Euclidean matching
- `Detector.process_frame_with_ids`: chains detection → tracking, returns `{ID: (x,y,w,h)}`
- Social distancing violation detection: flags pairs of people below `DISTANCE_THRESHOLD_PX`
- FastAPI streaming server (`/video_feed` MJPEG, `/status` JSON)
- Alarm cooldown to prevent log spam
- CLI runner with `--camera` and `--headless` flags

**Running**

```bash
cd social-distancing-detector/backend
pip install -r requirements.txt

# Option A: windowed CLI (shows OpenCV window)
python -m backend.main

# Option B: headless server (MJPEG + JSON API on :8000)
python -m backend.stream
```

---

## Tech Stack

| Technology | Used In |
|------------|---------|
| Python 3.10+ | Both projects |
| OpenCV (`cv2`) | Both projects |
| NumPy | Both projects |
| Flask + Flask-CORS | Background Subtraction Demo |
| FastAPI + Uvicorn | Social Distancing Detector |
| React | Both frontends |

---

## Repository Structure

```
Learning-Motion-Detection/
├── Background-Subtraction-Demo/
│   ├── motion_detection/   ← Flask backend + OpenCV logic
│   └── frontend/           ← React app
├── social-distancing-detector/
│   ├── backend/            ← FastAPI + detector + tracker
│   └── frontend/           ← React app (scaffold)
└── README.md
```
