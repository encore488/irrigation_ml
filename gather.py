'''
You must already have coordinates to interact with this file.
You want to create a new field? Use create_polygon(polygon_coord), which returns a polygon_id.
You need the humidity of an existing field? Use get_agromon_humidity(polygon_id)
'''



import pandas as pd
import requests
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()

# Access the AgroMonitoring API key
agromon_key = os.getenv("agromon_key")



# Function used in accessing the AgroMonitoring API
def create_polygon(polygon_coord):
    '''Can only be done once per polygon, or an error is thrown.'''
    # Create the polygon JSON structure
    polygon_points = [{"lat": lat, "lng": lon} for lat, lon in polygon_coord]
    polygon_payload = {
        "name": "My Polygon",
        "geo_json": {
            "type": "Feature",
            "properties": {},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[(point["lng"], point["lat"]) for point in polygon_points]]
            }
        }
    }

    # Create the polygon
    polygon_url = f"http://api.agromonitoring.com/agro/1.0/polygons?appid={agromon_key}"
    polygon_response = requests.post(polygon_url, json=polygon_payload)

    if polygon_response.status_code != 200:
        print("Error creating polygon:", polygon_response.json())
        return None

    polygon_id = polygon_response.json().get("id")
    return polygon_id



def get_agromon_humidity(polygon_id):
    
    
    # Fetch weather data for the polygon
    data_url = f"http://api.agromonitoring.com/agro/1.0/weather?polyid={polygon_id}&appid={agromon_key}"
    data_response = requests.get(data_url)

    if data_response.status_code != 200:
        print("Error fetching data:", data_response.json())
        return None
    return data_response.json()["main"]["humidity"]








'''Should I irrigate today or not?  :  Takes in “crop_thirstiness” level.'''
def irrigate_today(crop_thirstiness, crop_type):
    if crop_thirstiness > 0.5:
        return "Yes"
    else:
        return "No"
''' def crop_thirst: a composite score made up of… Precipitation history, current, and predicted + groundwater level or soil moisture, past irrigations, maybe soil type? And maybe temperature? 
However, different crops have different levels. '''


# Testing functions area
# Existing polygon ID
polygon_id = "5673134086352a3cf702cf1d7"

'''new_coords = [
(3.5357, 6.4364),
(3.5376, 6.4364),
(3.5376, 6.4344),
(3.5357, 6.4344),
(3.5357, 6.4364)
]
new_id = create_polygon(new_coords)
print("New ID:", new_id)
print("Humidity:", get_agromon_humidity(new_id))'''
print("Humidity:", get_agromon_humidity(polygon_id))