from contextlib import nullcontext
from sqlite3 import Date
from flask import Flask
from pymongo import MongoClient
import certifi
import json

app = Flask(__name__)

client = MongoClient("mongodb+srv://admin:12345@vandytracker.9qo0o0i.mongodb.net/?retryWrites=true&w=majority", tlsCAFile=certifi.where())
db = client.get_database("webdata")
db = client.get_database("VandyTracker")
locations = db.get_collection("Locations")
swipes = db.get_collection("Swipes")

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route('/getDataByLocation/<string:locationID>')
def getDataByLocation(locationID):
    data_json = []
    data = swipes.find({"locationID": locationID})

    for swipe in data:
        data_json.append(swipe)

    return data_json

@app.route('/getAllSwipes')
def getAllSwipes():
    data_json = []
    data = swipes.find()

    for swipe in data:
        data_json.append(swipe)

    return data_json

def getLastWeekSwipes():
    data_json = []
    data = swipes.aggregate([
        { "$match": {
            "$expr": {
                "$gt": [
                    "$time",
                    { "$dateSubtract": { "startDate": "$$NOW", "unit": "day", "amount": 7 }}]}}}])
    
    for swipe in data:
        data_json.append(swipe)

    return data_json

def create_stream():
    return ""