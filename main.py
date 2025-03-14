from flask import Flask, send_file
from flask_cors import CORS
from flask_socketio import SocketIO
from time import time
from enum import Enum
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder
from picamera2.outputs import FfmpegOutput
from libcamera import controls

class CAMERA_STATUS(Enum):
    IDLE = 0
    RECORDING = 1
    PAUSED = 2
    DISCONNECTED = 3

class VideoHandler:
    def __init__(self,
                 tag: str):
        self.tag = tag
        self.picam2 = None
        self.encoder = None
        self.output = None
        self.status = CAMERA_STATUS.DISCONNECTED
    
    def update(self):
        self.picam2 = Picamera2()
        video_config = self.picam2.create_video_configuration()
        self.picam2.configure(video_config)
        self.picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
        self.encoder = H264Encoder(10000000)
        self.output = self.tag+'_'+str(int(time()))+'.mp4'

    def start(self):
        self.picam2.start_recording(self.encoder, FfmpegOutput(self.output))

    def stop(self):
        self.picam2.stop_recording()
        self.picam2.close()
        
    def close(self):
        self.picam2.close()

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


videoHandler = VideoHandler('raspi_cam1')

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/download')
def download():
    # if videoHandler.output is None:
    #     return 'No video to download'
    return send_file(videoHandler.output, as_attachment=True)

@socketio.on('connect')
def handle_connect():
    print('client connected')
    videoHandler.status = CAMERA_STATUS.IDLE

@socketio.on('ping')
def handle_ping():
    print('received ping')
    return time()

@socketio.on('start_recording')
def handle_start_recording():
    print('Start recording at ' + str(time()))
    videoHandler.update()
    videoHandler.start()
    videoHandler.status = CAMERA_STATUS.RECORDING

@socketio.on('pause_recording')
def handle_pause_recording():
    raise NotImplementedError

@socketio.on('stop_recording')
def handle_stop_recording():
    print('Stop recording at ' + str(time()))
    videoHandler.stop()
    videoHandler.status = CAMERA_STATUS.IDLE

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)
