from flask import Flask
from flask_cors import CORS
from flask import jsonify

app = Flask(__name__)
CORS(app)

@app.route('/start')
def start():
    return jsonify({'message': 'Hello World!'})

@app.route('/pause')
def pause():
    return jsonify({'message': 'Pause'})

@app.route('/collect')
def collect():
    return jsonify({'message': 'Collect'})

if __name__ == '__main__':
    app.run()