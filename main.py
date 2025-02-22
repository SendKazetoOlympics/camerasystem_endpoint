from flask import Flask, jsonify, send_file
from flask_cors import CORS
from flask_socketio import SocketIO
from time import time
from enum import Enum
# from picamera2 import Picamera2
# from picamera2.encoders import H264Encoder

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
        video_config
        self.picam2.configure(video_config)
        self.encoder = H264Encoder(10000000)
        self.output = self.tag+'_'+str(int(time()))+'.h264'

    def start(self):
        self.picam2.start_recording(self.encoder, self.output)

    def stop(self):
        self.picam2.stop_recording()
        self.picam2.close()
        
    def close(self):
        self.picam2.close()

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")


videoHandler = VideoHandler('raspi_cam1')

@app.route('/')
def hello():
    return 'Hello, World!'

# @app.route('/start')
# def start():
#     videoHandler.update()
#     videoHandler.start()
#     app.logger.info('Start recording at ' + str(time()))
#     return jsonify({'message': 'Started recording'})

# @app.route('/pause')
# def stop():
#     videoHandler.stop()
#     app.logger.info('Stop recording at ' + str(time()))
#     return jsonify({'message': 'Finish recording'})

# @app.route('/collect')
# def collect():
#     return send_file(videoHandler.output)

@socketio.on('connect')
def handle_connect():
    print('client connected')
    videoHandler.status = CAMERA_STATUS.IDLE

@socketio.on('ping')
def handle_ping():
    print('received ping')

@socketio.on('download')
def handle_download():
    raise NotImplementedError

@socketio.on('start_recording')
def handle_start_recording():
    raise NotImplementedError

@socketio.on('pause_recording')
def handle_pause_recording():
    raise NotImplementedError

@socketio.on('stop_recording')
def handle_stop_recording():
    raise NotImplementedError

if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", debug=True)
