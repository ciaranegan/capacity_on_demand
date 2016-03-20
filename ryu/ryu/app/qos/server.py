from flask import Flask, Response, request
from ryu.app.qos.models import Base
from ryu.app.qos.dbconnection import DBConnection

app = Flask(__name__)

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

    reservation_id = add_reservation(reservation_info)
    if not reservation_id:
        return Response("Unable to process the requested reservation", status=400, mimetype="application/json")

    return Response({"reservation_id": reservation_id}, status=200, mimetype="application/json")


@app.route('/reservation/<res_id>', methods=['UPDATE'])
def update_reservation(res_id):
    reservation_info = request.json
    if not "bw" in reservation_info:
        return Response("No bandwidth provided", status=400, mimetype="application/json")

    reservation_id = update_reservation(res_id, reservation_info["bw"])
    if not reservation_id:
        return Response("Invalid reservation id", status=400, mimetype="application/json")

    return Response({"reservation_id": reservation_id}, status=200, mimetype="application/json")


if __name__ == '__main__':
    app.run()
