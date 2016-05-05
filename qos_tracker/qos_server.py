from flask import Flask
from qos_tracker import QoSTracker

app = Flask(__name__)
qos_tracker = QoSTracker()

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/reservation', methods=['POST'])
def add_reservation():
    # POST request
    # curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X POST -d '{"src": "10.0.0.1", "dst": "10.0.0.4", "bw": 10}' http://localhost:5000/add_reservation
    reservation_info = request.json
    if not reservation_info:
        return Response("Reservation info expected in json form", status=400, mimetype="application/json")

    qos_tracker.add_reservation(reservation_info)

    return Response({"reservation_id": reservation_id}, status=200, mimetype="application/json")


if __name__ == '__main__':
    qos_tracker.start()
    app.run()
