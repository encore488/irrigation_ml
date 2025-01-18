'''
You must have api keys (ideally stored in your .env file) and field coordinates to use much of this file.
You want to create a new field? Use create_polygon(polygon_coord), which returns a polygon_id.
You need the humidity of an existing field? Use get_agromon_data(polygon_id, "humidity")
'''


import pandas as pd
import requests
from datetime import datetime, timedelta
import json
from dotenv import load_dotenv
import os

# Load environment variables from the .env file
load_dotenv()



# # # # Agromonitoring # # # #
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

def get_agromon_data(polygon_id, data_type):    
    # Fetch weather data for the polygon
    data_url = f"http://api.agromonitoring.com/agro/1.0/weather?polyid={polygon_id}&appid={agromon_key}"
    data_response = requests.get(data_url)

    if data_response.status_code != 200:
        print("Error fetching data:", data_response.json())
        return None
    return data_response.json()["main"][data_type]


def fetch_soil_data(polygon_id):
    """
    Fetch soil data for a specified polygon from Agromonitoring.com.

    Args:
        polygon_id (str): The ID of the polygon.
        api_key (str): Your Agromonitoring API key.

    Returns:
        dict: A dictionary containing soil data for the polygon, or an error message.
    """
    base_url = "http://api.agromonitoring.com/agro/1.0/soil"
    url = f"{base_url}?polyid={polygon_id}&appid={agromon_key}"

    try:
        response = requests.get(url)
        if response.status_code == 404:
            return {"error": "Polygon not found. Please check the polygon_id."}
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": f"An error occurred: {e}"}

'''Example JSON response from the AgroMonitoring API: 
{'dt': 1731351959, 'weather': [{'id': 800,   'main': 'Clear',  'description': 'clear sky',   'icon': '01n'}],
 'main': {'temp': 300.38,  'feels_like': 303.41,  'temp_min': 300.38,  'temp_max': 300.38,  'pressure': 1009,
  'humidity': 80,  'sea_level': 1009,  'grnd_level': 1009}, 'wind': {'speed': 3.47, 'deg': 161, 'gust': 3.5},
 'clouds': {'all': 9}}'''


# # # # OpenWeather # # # #
# Access the OpenWeather API key
owm_key = os.getenv("owm_key")

def get_owm_weather(city_name, days_ahead=0):
    if days_ahead == 0:
        # Current weather
        base_url = "https://api.openweathermap.org/data/2.5/weather"
    elif 1 <= days_ahead <= 5:
        # 5-day forecast
        base_url = "https://api.openweathermap.org/data/2.5/forecast"
    else:
        print("Error: 'days_ahead' must be between 0 and 5.")
        return

    params = {
        "q": city_name,
        "appid": owm_key,
        "units": "metric"
    }
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Unable to fetch weather data for {city_name}")
'''Example JSON response from the OpenWeather API:
{'coord': {'lon': -74.006, 'lat': 40.7143}, 'weather': [{'id': 804, 'main': 'Clouds', 'description': 'overcast clouds',
 'icon': '04d'}], 'base': 'stations', 'main': {'temp': -1.55, 'feels_like': -7.51, 'temp_min': -2.84, 'temp_max': -0.59,
'pressure': 1011, 'humidity': 50, 'sea_level': 1011, 'grnd_level': 1010}, 'visibility': 10000, 
'wind': {'speed': 6.17, 'deg': 240}, 'clouds': {'all': 100}, 'dt': 1737056512, 'sys': {'type': 1, 'id': 4610, 'country': 'US', 
'sunrise': 1737029838, 'sunset': 1737064442}, 'timezone': -18000, 'id': 5128581, 'name': 'New York', 'cod': 200}'''


# # # # Visual Crossing # # # #     Not working?
# Access the Visual Crossing API key
vc_key = os.getenv("vc_key")

def get_visual_crossing_data(location):
    # Set up the API endpoint
    base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    # Set up parameters
    params = {
        "unitGroup": "metric",
        "key": vc_key,
        "contentType": "json",
    }
    # Create the full URL
    url = f"{base_url}/{location}"
    # Make the API request
    response = requests.get(url, params=params)

    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: Unable to fetch data. Status code: {response.status_code}")
        return None
    
    
def get_crop_watering_data(location):
    # Get the full weather data
    full_data = get_visual_crossing_data(location)
    
    if full_data is None:
        return None
    
    # Extract relevant information
    crop_watering_data = {
        "forecast": []
    }
    
    # Extract forecast data
    for day in full_data.get("days", []):
        daily_data = {
            "date": day.get("datetime"),
            "precipitation": day.get("precip", 0),
            "precipitation_probability": day.get("precipprob", 0),
            "humidity": day.get("humidity", 0),
            "soil_moisture_first_10cm": day.get("soilmoisture01", 0),
            "soil_moisture_10cm_to_40cm": day.get("soilmoisture04", 0),
            "evapotranspiration": day.get("et0", 0)
        }
        crop_watering_data["forecast"].append(daily_data)
    
    return crop_watering_data


def get_agricultural_data(location):
    base_url = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"
    params = {
        "unitGroup": "metric",
        "key": vc_key,
        "contentType": "json",
        "include": "days",
        "elements": "datetime,precip,humidity,soilmoisture01,soilmoisture04,soilmoisture10,soilmoisture20,et0"
    }
    
    url = f"{base_url}/{location}"
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = json.loads(response.text)
        return data['days']
    else:
        print(f"Error: {response.status_code}")
        return None

# Usage example
agricultural_data = get_agricultural_data("Denver,CO")

if agricultural_data:
    for day in agricultural_data:
        print(f"Date: {day['datetime']}")
        print(f"Precipitation: {day['precip']} mm")
        print(f"Humidity: {day['humidity']}%")
        print(f"Soil Moisture (0-0.1m): {day['soilmoisture01']} mm")
        print(f"Soil Moisture (0.1-0.4m): {day['soilmoisture04']} mm")
        print(f"Soil Moisture (0.4-1.0m): {day['soilmoisture10']} mm")
        print(f"Soil Moisture (1.0-2.0m): {day['soilmoisture20']} mm")
        print(f"Evapotranspiration: {day['et0']} mm")
        print("---")





'''Should I irrigate today or not?  :  Takes in “crop_thirstiness” level.'''
def irrigate_today(crop_thirstiness, crop_type):
    if crop_thirstiness > 0.5:
        return "Yes"
    else:
        return "No"
''' def crop_thirst: a composite score made up of… Precipitation history, current, and predicted + groundwater level or soil moisture, past irrigations, maybe soil type? And maybe temperature? 
However, different crops have different levels. '''


# Testing functions area
# Existing polygon ID: polygon_id = "673134086352a3cf702cf1d7"
#print("Humidity:", get_agromon_data(polygon_id, "humidity"))
#print(get_crop_watering_data("New York"))
test_poly_id = os.getenv("test_poly_id")

print("Gathering.... fetch_soil_data result for " + test_poly_id + ":")
print(fetch_soil_data(test_poly_id))