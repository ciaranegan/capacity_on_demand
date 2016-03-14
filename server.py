from flask import Flask, Response, request
from ryu.app.qos.dbconnection import add_reservation

app = Flask(__name__)

@app.route('/')
def hello_world():
    return 'Hello World!'

@app.route('/add_reservation', methods=['POST'])
def add_reservation():
    reservation_info = request.json
    if not reservation_info:
        return Response("Reservation info expected in json form", status=400, mimetype="application/json")

    reservation_id = add_reservation(reservation_info)
    if not reservation_id:
        return Response("Unable to process the requested reservation", status=400, mimetype="application/json")

    return Response({"reservation_id": reservation_id}, status=200, mimetype="application/json")

if __name__ == '__main__':
    app.run()

# POST request
# curl -i -H "Accept: application/json" -H "Content-Type: application/json" -X POST -d '{"hsllo": "asd", "asd": "asdas"}' http://localhost:5000/add_reservation