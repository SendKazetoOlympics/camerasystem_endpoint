import subprocess
from flask import Flask, send_file, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO
from time import time
from enum import Enum
from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder, H264Encoder
from libcamera import controls
import os


class CAMERA_STATUS(Enum):
    IDLE = 0
    RECORDING = 1
    PAUSED = 2
    DISCONNECTED = 3


class VideoHandler:
    def __init__(self, tag: str):
        self.tag = tag
        self.picam2 = None
        self.encoder = None
        self.output = None
        self.status = CAMERA_STATUS.DISCONNECTED
        self.time_stamp_array = []
        self.mediamtx_process = None

    def update(self):
        self.picam2 = Picamera2()
        sensor_mode = self.picam2.sensor_modes[1]
        video_config = self.picam2.create_video_configuration(
            sensor={"output_size": sensor_mode["size"]}
        )
        self.picam2.configure(video_config)
        self.picam2.set_controls(
            {"AfMode": controls.AfModeEnum.Continuous, "FrameRate": sensor_mode["fps"]}
        )
        self.encoder = H264Encoder(framerate=int(sensor_mode["fps"]))
        # Ensure output directory exists
        output_dir = os.path.join(os.path.dirname(__file__), "output")
        os.makedirs(output_dir, exist_ok=True)
        self.output = os.path.join(output_dir, self.tag + "_" + str(int(time())))

    def start(self):
        def apply_timestamp(request):
            self.time_stamp_array.append(time())

        self.picam2.pre_callback = apply_timestamp
        self.picam2.start_recording(self.encoder, self.output + ".h264")

    def stop(self):
        self.picam2.stop_recording()
        self.picam2.close()
        os.system(f"ffmpeg -i {self.output}.h264 -c copy {self.output}.mp4")

    def get_timestamps(self):
        return {
            "timestamps": self.time_stamp_array,
        }

    def start_mediamtx(self):
        if self.mediamtx_process is not None and self.mediamtx_process.poll() is None:
            return {"status": "already running"}, 400

        base_dir = os.path.dirname(__file__)
        mediamtx_path = os.path.join(base_dir, "mediamtx", "mediamtx")
        mediamtx_config = os.path.join(base_dir, "mediamtx", "mediamtx.yml")
        if not os.path.exists(mediamtx_path):
            return {"error": "mediamtx executable not found"}, 404
        if not os.path.exists(mediamtx_config):
            return {"error": "mediamtx config not found"}, 404

        self.mediamtx_process = subprocess.Popen([mediamtx_path, mediamtx_config])
        return {"status": "started", "pid": self.mediamtx_process.pid}, 200

    def stop_mediamtx(self):
        if self.mediamtx_process is None or self.mediamtx_process.poll() is not None:
            return {"status": "not running"}, 400

        self.mediamtx_process.terminate()
        try:
            self.mediamtx_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.mediamtx_process.kill()
        self.mediamtx_process = None
        return {"status": "stopped"}, 200


app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


videoHandler = VideoHandler("raspi_cam1")


@app.route("/")
def hello():
    return "Hello, World!"


@app.route("/download")
def download():
    if videoHandler.output is None:
        return "No video to download"
    # Return timestamps and download URL as JSON
    timestamps = videoHandler.get_timestamps()
    download_url = request.host_url.rstrip('/') + '/download_video'
    return jsonify({
        "download_url": download_url,
        "timestamps": timestamps
    })

@app.route("/download_video")
def download_video():
    if videoHandler.output is None:
        return "No video to download"
    return send_file(videoHandler.output+'.mp4', as_attachment=True)


@socketio.on("connect")
def handle_connect():
    print("client connected")
    videoHandler.status = CAMERA_STATUS.IDLE


@socketio.on("ping")
def handle_ping():
    print("received ping")
    return time()


@socketio.on("start_recording")
def handle_start_recording():
    print("Start recording at " + str(time()))
    videoHandler.update()
    videoHandler.start()
    videoHandler.status = CAMERA_STATUS.RECORDING


@socketio.on("pause_recording")
def handle_pause_recording():
    raise NotImplementedError


@socketio.on("stop_recording")
def handle_stop_recording():
    print("Stop recording at " + str(time()))
    videoHandler.stop()
    videoHandler.status = CAMERA_STATUS.IDLE


@app.route("/start_mediamtx", methods=["POST"])
def start_mediamtx():
    result, code = videoHandler.start_mediamtx()
    return jsonify(result), code

@app.route("/stop_mediamtx", methods=["POST"])
def stop_mediamtx():
    result, code = videoHandler.stop_mediamtx()
    return jsonify(result), code


if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", debug=True)
