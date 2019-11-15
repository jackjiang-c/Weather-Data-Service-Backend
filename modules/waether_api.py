import datetime
import requests

"""sample = {'coord': {'lon': 151.21, 'lat': -33.87},
'weather': [{'id': 761, 'main': 'Dust', 'description': 'dust', 'icon': '50n'}], 
'base': 'stations', 
'main': {'temp': 292.27, 'pressure': 1006, 'humidity': 82, 'temp_min': 290.37, 'temp_max': 298.15}, 
'visibility': 10000, 'wind': {'speed': 9.3, 'deg': 180, 'gust': 15.4}, 
'clouds': {'all': 75}, 'dt': 1573555451, 
'sys': {'type': 1, 'id': 9600, 'country': 'AU', 'sunrise': 1573497966, 'sunset': 1573547547},
'timezone': 39600,
'id': 2147714, 'name': 'Sydney', 'cod': 200}
"""


def convert_weather_data(raw_weather):
    K = 273.15
    time_format = "%H:%M"
    # convert Kelvin to Celsius
    temp = format(raw_weather['main']['temp'] - K, '.1f')
    min_temp = format(raw_weather['main']['temp_min'] - K, '.1f')
    max_temp = format(raw_weather['main']['temp_max'] - K, '.1f')
    # convert epoch to locatime
    sunrise = datetime.datetime.fromtimestamp(raw_weather['sys']['sunrise'])
    sunset = datetime.datetime.fromtimestamp(raw_weather['sys']['sunset'])
    sunrise = sunrise.strftime(time_format)
    sunset = sunset.strftime(time_format)
    type = raw_weather['weather'][0]['description']
    icon = raw_weather['weather'][0]['icon']
    # humanity
    humidity = raw_weather['main']['humidity']
    now = datetime.datetime.now()
    time = now.strftime("%H:%M %d %b")
    # todo
    return {'temp': temp, 'maxTemp': max_temp, 'minTemp': min_temp, 'humidity': humidity, 'type': type,
            'sunrise': sunrise, 'sunset': sunset, 'icon': icon, 'location': raw_weather['name'],
            'country': raw_weather['sys']['country'], 'time': time}


# todo
def get_today_forecast():
    pass


# todo
def get_today_weather_data():
    current_weahter_data = "http://reg.bom.gov.au/products/IDN60901/IDN60901.94768.shtml"
    pass
