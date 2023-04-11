from contextlib import nullcontext
from sqlite3 import Date, Timestamp
from flask import Flask, jsonify
from pymongo import MongoClient
from bson import ObjectId
import datetime
import certifi
import json

# Converts all Object IDs to String
# Commented out of test coverage, this is implicitly tested by many of the functions in this file
class MyEncoder(json.JSONEncoder): # pragma: no cover
    def default(self,obj):
        if isinstance(obj, ObjectId) or isinstance(obj, Timestamp):
            return str(obj)
        return super(MyEncoder, self).default(obj)

app = Flask(__name__)

app.json_encoder = MyEncoder

client = MongoClient("mongodb+srv://admin:12345@vandytracker.9qo0o0i.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=certifi.where())
db = client.get_database("webdata")
db = client.get_database("VandyTracker")
locations = db.get_collection("Locations")
swipes = db.get_collection("Fake_Data")

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/getDataByLocation/<string:locationID>')
def getDataByLocation(locationID):
    data_json = []
    data = swipes.find({"locationID": locationID})


    for swipe in data:
        data_json.append(swipe)

    return jsonify(data_json)

@app.route('/getAllSwipes')
def getAllSwipes():
    data_json = []
    data = swipes.find()

    for swipe in data:
        data_json.append(swipe)

    return data_json

@app.route('/testDate')
def testDate():
    from_date = datetime.datetime(2023, 4, 15, 10, 44, 40, 000000)
    to_date = datetime.datetime(2023, 4, 15, 10, 45, 40, 000000)
    ts = swipes.count_documents({"Timestamp": {"$gte": from_date, "$lt": to_date}})

    return str(ts)

# getCurrentOccupancy(location_id)
# getOccupancyByHour(locationID, hour)
# getAverageOccupancy(locationID, weekday, hour)
# getAverageOccupancy(location_id)
# getBusyTimes(location_id)