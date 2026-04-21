# Social Distancing Detector

Real-time social distancing violation detection using classical computer vision.

## Tech Stack
- **Detection**: OpenCV MOG2 background subtraction, centroid tracking, NMS
- **Backend**: FastAPI, MJPEG streaming, JSON status endpoint
- **Frontend**: React + Vite + Tailwind CSS

## Project Structure
social-distancing-detector/
├── backend/
│   ├── core/          # detector, tracker, distancing, alarm
│   ├── main.py        # FastAPI app
│   ├── stream.py      # MJPEG generator + CameraManager
│   └── requirements.txt
└── frontend/          # React + Vite + Tailwind

## Run Locally

### Backend
cd backend
pip install -r requirements.txt
python main.py

### Frontend
cd frontend
npm install
npm run dev

## Endpoints
| Route         | Description                        |
|---------------|------------------------------------|
| /video_feed   | MJPEG annotated webcam stream      |
| /status       | JSON snapshot (fps, ids, alarms)   |
