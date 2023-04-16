from contextlib import nullcontext
from sqlite3 import Date, Timestamp
import datetime
from datetime import datetime, timedelta
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

daysOpen =  {
        "Rec" :
            list({"Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sum"}),
        "Rand" :
            ""
}

hours = {
        "Rec" :
        [6,11],
        "Rand" :
            ""
}

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

@app.route('/getLocationType/<string:locationID>')
def getLocationType(locationID):
    if (locationID == "Rec" or locationID == "Alumni"):
        return "gym"
    return "dining"

@app.route('/getCurrentOccupancy/<string:locationID>')
def getCurrentOccupancy(locationID):
    from_date = datetime.datetime.now() - timedelta(hours = 1)
    to_date = datetime.datetime.now()
    occupancy = swipes.count_documents(
        {"locationID": locationID, "Timestamp": {"$gte": from_date, "$lt": to_date}}
    )
    
    return json.dumps({"currentOccupancy":occupancy})

@app.route('/getOccupancyByHour/<string:locationID>/<string:hour>')
def getOccupancyByHour(locationID, hour):
    time = datetime.strptime(hour, "%Y-%m-%dT%H:%M:%S.%f%z")
    ts = time.timestamp()
    #timestamp_str = "2023-04-15T10:44:40.000+00:00"

    from_date = ts - timedelta(hours = 1)
    to_date = time
    ts = swipes.count_documents(
        {"locationID": locationID,
        "Timestamp": {"$gte": from_date, "$lt": to_date}},
    )
    
    return str(ts)

# Not right implementation, can someone help me with this?  
@app.route('/getAverageOccupancyByHourOnWeekday/<string:locationID>/<string:weekday>/<int:hour>')
def getAverageOccupancyByHourOnWeekday(locationID, weekday, hour):

    swipes_by_location_weekday_hour = swipes.find(
        {
            "locationID": locationID,
            "Weekday": weekday,
            "$expr": {
                "$eq": 
                [ {"$hour": "$Timestamp"}, hour - 1 ]
            }
        }
    )

    count = swipes.count_documents(
        {
            "locationID": locationID,
            "Weekday": weekday,
            "$expr": {
                "$eq": 
                [ {"$hour": "$Timestamp"}, hour - 1 ]
            }
        }
    )

    zset = set()
    for swipe in swipes_by_location_weekday_hour:
        print(swipe)
        zset.add(swipe['Timestamp'].date())

    num_days = len(zset)
    if num_days == 0:
        return "No swipes in the specified time period"
    
    avg_occupancy = int(count / num_days)
    return avg_occupancy

@app.route('/getAverageOccupancyByWeekday/<string:locationID>/<string:weekday>')
def getAverageOccupancyByWeekday(locationID, weekday):
    data_json = []

    if (weekday in daysOpen[locationID]):
        open = hours[locationID][0]
        close = hours[locationID][1]

        for i in range(open + 1, close + 1):
            avg = getAverageOccupancyByHourOnWeekday(locationID, weekday, i)
            data_json.append({i : avg})

    print(data_json)

    return json.dumps(data_json)

# Test call below:
# print(getAverageOccupancyByHourOnWeekday('Rec', 'Sum', 23))

# getCurrentOccupancy(location_id)
# getOccupancyByHour(locationID, hour)
# getAverageOccupancy(locationID, weekday, hour)
# getAverageOccupancy(location_id)
# getBusyTimes(location_id) 