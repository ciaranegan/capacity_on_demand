from flask import Flask
from qos_tracker import QoSTracker

app = Flask(__name__)
qos_tracker = QoSTracker()

@app.route('/')
def hello_world():
    return 'Hello World!'

if __name__ == '__main__':
    qos_tracker.start()
    app.run()
