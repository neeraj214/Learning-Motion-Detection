from flask import Flask, jsonify, Response
from flask_cors import CORS

app = Flask(__name__)
# Enable CORS for React frontend communications
CORS(app)

@app.route('/')
def index():
    """Placeholder for the index route."""
    return jsonify({"message": "Motion Detection Backend is running."})

@app.route('/video_feed')
def video_feed():
    """Placeholder for the video streaming route."""
    # This will eventually return a Multipart response with JPEG frames
    return "Video feed placeholder"

@app.route('/motion_status')
def motion_status():
    """Placeholder for fetching current motion status."""
    return jsonify({"motion_detected": False, "status": "Idle"})

@app.route('/set_threshold', methods=['POST'])
def set_threshold():
    """Placeholder for updating motion sensitivity threshold."""
    return jsonify({"status": "success", "message": "Threshold updated"})

if __name__ == "__main__":
    # Run the Flask app on port 5000 as requested
    app.run(host='0.0.0.0', port=5000, debug=True)
