from flask import Flask

app = Flask(__name__)

@app.route('/')
def hello():
    return "Hello, World! The application is running!"

if __name__ == '__main__':
    app.run(debug=True)
