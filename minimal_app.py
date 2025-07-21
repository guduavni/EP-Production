"""
Minimal Flask application to test the server.
"""
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def hello():
    return "EP-Simulator is running!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
