from contextlib import nullcontext
from sqlite3 import Date, Timestamp
import datetime
from datetime import datetime, timedelta
from flask import Flask, jsonify
from pymongo import MongoClient
from bson import ObjectId
from flask_cors import CORS

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
CORS(app, resources={r"/*": {"origins": "*"}})

app.json_encoder = MyEncoder

client = MongoClient("mongodb+srv://admin:12345@vandytracker.9qo0o0i.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=certifi.where())
db = client.get_database("webdata")
db = client.get_database("VandyTracker")
locations = db.get_collection("Locations")
swipes = db.get_collection("Fake_Data")

daysOpen =  {
        "Rec" :
            {"Mon":[6,23], "Tues":[6,23], "Wed": [6,23], "Thurs":[6,23], "Fri":[6,22], "Sat":[8,20], "Sun":[12,23]},
        "Rand" :
            {"Mon":[7,15], "Tues":[7,15], "Wed":[7,15], "Thurs":[7,15], "Fri":[7,15]},
        "Roth" :
            {"Mon":[7,20], "Tues":[7,20], "Wed":[7,20], "Thurs":[7,20], "Fri":[7,20], "Sat":[9,20], "Sun":[9,20]},
        "Zeppos" :
            {"Mon":[7,20], "Tues":[7,20], "Wed":[7,20], "Thurs":[7,20], "Fri":[7,20], "Sat":[9,20], "Sun":[9,20]},
        "Central" :
            {"Mon":[8,24], "Tues":[8,24], "Wed":[8,24], "Thurs":[8,24], "Fri":[8,24], "Sat":[8,24], "Sun":[8,24]},
        "Commons" :
            {"Mon":[7,20], "Tues":[7,20], "Wed":[7,20], "Thurs":[7,20], "Fri":[7,20], "Sat":[9,20], "Sun":[9,20]},
        "EBI" :
            {"Mon":[7,20], "Tues":[7, 20], "Wed":[7,20], "Thurs":[7,20], "Fri":[7,20], "Sat":[9,20], "Sun":[9,20]},
        "Alumni" : 
            {"Mon":[6,23], "Tues":[6,23], "Wed": [6,23], "Thurs":[6,23], "Fri":[6,22], "Sat":[8,20], "Sun":[12,23]},
            }

hours = ['8AM','9AM','10AM','11AM','12PM','1PM','2PM','3PM','4PM','5PM','6PM','7PM','8PM','10AM','11AM', '12AM', '1AM']

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/api/getDataByLocation/<string:locationID>')
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

@app.route('/api/getLocationType/<string:locationID>')
def getLocationType(locationID):
    if (locationID == "Rec" or locationID == "Alumni"):
        return "gym"
    return "dining"

@app.route('/api/getCurrentOccupancy/<string:locationID>')
def getCurrentOccupancy(locationID):
    from_date = datetime.datetime.now() - timedelta(hours = 1)
    to_date = datetime.datetime.now()
    occupancy = swipes.count_documents(
        {"locationID": locationID, "Timestamp": {"$gte": from_date, "$lt": to_date}}
    )
    
    return json.dumps(occupancy)

@app.route('/api/getOccupancyByHour/<string:locationID>/<string:hour>')
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
@app.route('/api/getAverageOccupancyByHourOnWeekday/<string:locationID>/<string:weekday>/<int:hour>')
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
        zset.add(swipe['Timestamp'].date())

    num_days = len(zset)
    if num_days == 0:
        return 0
    
    avg_occupancy = int(count / num_days)
    return avg_occupancy

@app.route('/api/getAverageOccupancyByWeekday/<string:locationID>/<string:weekday>')
def getAverageOccupancyByWeekday(locationID, weekday):
    data_json = []

    if (weekday in daysOpen[locationID]):
        open = daysOpen[locationID][weekday][0]
        close = daysOpen[locationID][weekday][1]

        for i in range(open + 1, close + 1):
            avg = getAverageOccupancyByHourOnWeekday(locationID, weekday, i)
            data_json.append({"time" : hours[i - 8], "occupancy" : avg})

    return json.dumps(data_json)

@app.route('/api/getAllAverageOccupancies/<string:locationID>')
def getAllAverageOccupancies(locationID):
    data_json = []
    days = daysOpen[locationID]

    if days is None:
        return json.dumps(data_json)

    for day in days:
        weekdayOccupancies = getAverageOccupancyByWeekday(locationID, day)
        data_json.append({day:weekdayOccupancies})

    return json.dumps(data_json)

@app.route('/api/getAllTotalOccupancies/<string:locationID>')
def getAllTotalOccupancies(locationID):
    data_json = []
    days = daysOpen[locationID]


    if days is None:
        return json.dumps(data_json)

    for day in days:
        count = swipes.count_documents(
        {
            "locationID": locationID,
            "Weekday": day,
            }
        )
        data_json.append({"weekday": day, "occupancy": count})

    return data_json

@app.route('/api/getOccTodayByHour/<string:locationID>/<int:hour>')
def getOccTodayByHour(locationID, hour):
    date = datetime.datetime.now().date()
    
    count = swipes.count_documents(
        {
            "locationID": locationID,
            "$expr": {
                "$and": [
                    {"$eq": [ {"$hour": "$Timestamp"}, hour - 1 ]},
                    {"$eq": [ {"$dateToString": { "format": "%Y-%m-%d", "date": "$Timestamp" }}, str(date) ]}
                ]
            }
        }
    )  
    return str(count)

@app.route('/api/getOccTodayAll/<string:locationID>')
def getOccTodayAll(locationID):
    week_day = datetime.datetime.now().weekday()
    week_arr =["Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sun"]
    data_json = []

    if (week_arr[week_day] in daysOpen[locationID]):
        open = daysOpen[locationID][week_arr[week_day]][0]
        close = daysOpen[locationID][week_arr[week_day]][1]

        for i in range(open + 1, close + 1):
            avg = getOccTodayByHour(locationID, i)
            data_json.append({"time" : hours[i - 8], "occupancy" : avg})

    return json.dumps(data_json)

@app.route('/api/getOccForPopUp/<string:locationID>')
def getOccForPopUp(locationID):
    week_day = datetime.datetime.now().weekday()
    week_arr =["Mon", "Tues", "Wed", "Thurs", "Fri", "Sat", "Sun"]
    data_json = []
    time = datetime.datetime.now().hour

    open = daysOpen[locationID][week_arr[week_day]][0]
    close = daysOpen[locationID][week_arr[week_day]][1]

    if (time > close or time < open):
        avg = 0
        data_json.append({"time" : "Location closed.", "occupancy" : avg})
    else:
        avg = getCurrentOccupancy(locationID)
        data_json.append({"time" : hours[time - 8], "occupancy" : avg})

        if (week_arr[week_day] in daysOpen[locationID]):
            
            end = time + 5
            if (end > close):
                end = close

            for i in range(time + 1, end + 1):
                avg = getAverageOccupancyByHourOnWeekday(locationID, week_arr[week_day], i)
                data_json.append({"time" : hours[i - 8], "occupancy" : avg})
    
    return json.dumps(data_json)

# Test call below:
# print(getAverageOccupancyByHourOnWeekday('Rec', 'Sun', 23))

# getCurrentOccupancy(location_id)
# getOccupancyByHour(locationID, hour)
# getAverageOccupancy(locationID, weekday, hour)
# getAverageOccupancy(location_id)
# getBusyTimes(location_id) 