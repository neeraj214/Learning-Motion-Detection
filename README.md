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
| Frontend | React (Vite) + Tailwind CSS |
| Algorithm | MOG2 + NMS + CentroidTracker |

**Architecture**

```
social-distancing-detector/
├── backend/            ← FastAPI + detector + tracker
│   ├── main.py         ← CLI entry point (windowed / headless)
│   ├── stream.py       ← FastAPI MJPEG + JSON status API
│   ├── requirements.txt
│   └── core/
│       ├── config.py    ← Settings dataclass
│       ├── detector.py  ← Detector (MOG2 + NMS + process_frame_with_ids)
│       └── tracker.py   ← CentroidTracker (persistent IDs across frames)
└── frontend/           ← React (Vite) + Tailwind UI
    ├── src/
    │   ├── components/ ← StatusBanner, StatsPanel
    │   ├── hooks/      ← useSSE (real-time events)
    │   ├── config.js   ← API endpoint configuration
    │   └── App.jsx     ← Main UI assembly (Phase 5)
    └── tailwind.config.js
```

**Key Features**
- `CentroidTracker`: persistent object IDs across frames using greedy Euclidean matching.
- `Detector.process_frame_with_ids`: chains detection → tracking, returns `{ID: (x,y,w,h)}`.
- Social distancing violation detection: flags pairs of people below `DISTANCE_THRESHOLD_PX`.
- FastAPI streaming server (`/video_feed` MJPEG, `/events` SSE).
- **Real-time Frontend**:
  - `useSSE` hook for live data synchronization with the backend.
  - `StatusBanner`: Dynamic color-coded alerts (Safe/Warning/Alarm).
  - `StatsPanel`: 2x2 dashboard grid for tracking metrics.
- Alarm cooldown to prevent log spam.
- CLI runner with `--camera` and `--headless` flags.

**Running**

```bash
# Backend
cd social-distancing-detector/backend
pip install -r requirements.txt
python -m backend.stream  # runs on http://localhost:8000

# Frontend
cd ../frontend
npm install
npm run dev               # runs on http://localhost:5173
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
| React (CRA/Vite) | Both frontends |
| Tailwind CSS | Social Distancing Detector Frontend |

---

## Repository Structure

```
Learning-Motion-Detection/
├── Background-Subtraction-Demo/
│   ├── motion_detection/   ← Flask backend + OpenCV logic
│   └── frontend/           ← React app
├── social-distancing-detector/
│   ├── backend/            ← FastAPI + detector + tracker
│   └── frontend/           ← React (Vite) + Tailwind UI
└── README.md
```
