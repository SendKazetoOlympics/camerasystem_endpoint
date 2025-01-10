from flask import Flask, jsonify, send_file
from flask_cors import CORS
from time import time
from picamera2 import Picamera2
from picamera2.encoders import H264Encoder


class VideoHandler:
    def __init__(self,
                 tag: str):
        self.tag = tag
        self.picam2 = None
        self.encoder = None
        self.output = None
    
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
CORS(app)


videoHandler = VideoHandler('raspi_cam1')

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/start')
def start():
    videoHandler.update()
    videoHandler.start()
    app.logger.info('Start recording at ' + str(time()))
    return jsonify({'message': 'Started recording'})

@app.route('/pause')
def stop():
    videoHandler.stop()
    app.logger.info('Stop recording at ' + str(time()))
    return jsonify({'message': 'Finish recording'})

@app.route('/collect')
def collect():
    return send_file(videoHandler.output)

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=True)
