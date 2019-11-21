import datetime
import requests
from bs4 import BeautifulSoup as bs
import pandas as pd
import io
import time

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
    temp = float(format(raw_weather['main']['temp'] - K, '.1f'))
    min_temp = float(format(raw_weather['main']['temp_min'] - K, '.1f'))
    max_temp = float(format(raw_weather['main']['temp_max'] - K, '.1f'))
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
    return {'temp': temp, 'maxTemp': max_temp, 'minTemp': min_temp, 'humidity': humidity, 'type': type,
            'sunrise': sunrise, 'sunset': sunset, 'icon': icon, 'location': raw_weather['name'],
            'country': raw_weather['sys']['country'], 'time': time}


def getMean(soup):
    mean_table = soup.find_all('tbody')[1]
    weather_data = mean_table.tr.next_sibling.find_all('td')
    col_name = ['Minimum temperature (C)', 'Maximum temperature (C)', 'Rainfall (mm)', 'Evaporation (mm)',
                'Sunshine (hours)', 'Direction of maximum wind gust ', 'Speed of maximum wind gust (km/h)',
                'Time of maximum wind gust', '9am Temperature (C)', '9am relative humidity (%)',
                '9am cloud amount (oktas)', '9am wind direction', '9am wind speed (km/h)', '9am MSL pressure (hPa)',
                '3pm Temperature (C)', '3pm relative humidity (%)', '3pm cloud amount (oktas)', '3pm wind direction',
                '3pm wind speed (km/h)', '3pm MSL pressure (hPa)']
    mean_data = {}
    for i in range(len(weather_data)):
        if weather_data[i].get_text() == '\xa0':
            mean_data[col_name[i]] = ' '
        else:
            mean_data[col_name[i]] = weather_data[i].get_text()
    return mean_data


def getCSVLink(link):
    page = requests.get(link)
    soup = bs(page.content, 'html.parser')
    csv = soup.find_all(class_='content')
    p = csv[1].p
    for i in range(0, 7):
        p = p.next_sibling
    href = 'http://www.bom.gov.au' + p.a['href']
    return href, p, getMean(soup)


def todf(href, f='c'):
    r = requests.get(href).content
    a = r.decode('utf-8', 'ignore')
    li = a.splitlines()[9:]
    csv = ''
    for i in li:
        csv += i[1:] + '\n'
    ds = pd.read_csv(io.StringIO(csv))
    ds.fillna(value='NaN', inplace=True)
    if f == 'c':
        return ds
    else:
        last_index = ds.index.stop - 1
        end = dict(ds.iloc[last_index])
        end2 = dict(ds.iloc[last_index - 1])
        return end, end2

def prev_month_mean(p):
    for i in range(0, 3):
        p = p.next_sibling
    pre_href = 'http://www.bom.gov.au' + p.a.next_sibling.next_sibling['href']
    page = requests.get(pre_href)
    soup = bs(page.content, 'html.parser')
    prev_csv = soup.find_all(class_='content')
    return getMean(soup), prev_csv

def prev_month_last_two_day(soup_csv):
    p = soup_csv[1].p
    for i in range(0, 7):
        p = p.next_sibling
    href = 'http://www.bom.gov.au' + p.a['href']
    last, sec_last = todf(href, f='p')
    return last, sec_last


def get2DayData(ds, soup_csv):
    today = time.localtime().tm_mday
    avail_day = ds.index.stop
    if avail_day <= 2:
        l1, l2 = prev_month_last_two_day(soup_csv)
        if today > avail_day:
            return l1, l2
        else:
            last_index = ds.index.stop - 1
            if avail_day == 1:
                return dict(ds.iloc[last_index]), l1
            else:
                return dict(ds.iloc[last_index]), dict(ds.iloc[last_index - 1])
    if today > avail_day:
        today -= 1
    return dict(ds.iloc[today - 1]), dict(ds.iloc[today - 2])


def getValue(l1,l2, key, default=0, special='Calm'):
    if l1[key] != 'NaN' and l1[key] != ' ':
        if l1[key] == special:
            return 0
        return float(l1[key])
    else:
        if l2[key] != 'NaN' and l2[key] != ' ':
            return float(l2[key])
        else:
            return default


def get_predict_data_from_site(link):
    csv_href, p, c_mean = getCSVLink(link)
    p_mean, soup_csv = prev_month_mean(p)
    df = todf(csv_href)
    last, last2 = get2DayData(df, soup_csv)
    r_mean = {}
    for k, v in c_mean.items():
        if v == ' ':
            if p_mean[k] == ' ':
                r_mean[k] = 0
            else:
                r_mean[k] = float(p_mean[k])
        else:
            r_mean[k] = float(c_mean[k])
    return last, last2, r_mean


def get_weather_data():
    predict_data_link = "http://www.bom.gov.au/climate/dwo/IDCJDW2124.latest.shtml"
    l1, l2, mean = get_predict_data_from_site(predict_data_link)
    # a avg temp
    mintemp = getValue(l1, l2, 'Minimum temperature (C)', default=mean['Minimum temperature (C)'])
    maxtemp = getValue(l1, l2, 'Maximum temperature (C)', default=mean['Maximum temperature (C)'])
    avgtemp = (mintemp + maxtemp) / 2
    # b rainfall
    rainfall = getValue(l1, l2, 'Rainfall (mm)', default=mean['Rainfall (mm)'])
    # c Evaporation
    evap = getValue(l1, l2, 'Evaporation (mm)', default=mean['Evaporation (mm)'])
    # d sunshine
    sunshine = getValue(l1, l2, 'Sunshine (hours)', default=mean['Sunshine (hours)'])
    # e WindGustSpeed
    windGustSpeed = getValue(l1, l2, 'Speed of maximum wind gust (km/h)')
    # f windSpeed
    winspeed9am = getValue(l1, l2, '9am wind speed (km/h)', default=mean['9am wind speed (km/h)'])
    winspeed3pm = getValue(l1, l2, '3pm wind speed (km/h)', default=mean['3pm wind speed (km/h)'])
    avgwindspeed = (winspeed9am + winspeed3pm) / 2
    # g humidity
    humidity9am = getValue(l1, l2, '9am relative humidity (%)', default=mean['9am relative humidity (%)'])
    humidity3pm = getValue(l1, l2, '3pm relative humidity (%)', default=mean['3pm relative humidity (%)'])
    avghumidity = (humidity9am + humidity3pm) / 2
    # h pressure
    pressure9am = getValue(l1, l2, '9am MSL pressure (hPa)', default=mean['9am MSL pressure (hPa)'])
    pressure3pm = getValue(l1, l2, '3pm MSL pressure (hPa)', default=mean['3pm MSL pressure (hPa)'])
    avgpressure = (pressure9am + pressure3pm) / 2
    # i cloud
    cloud9am = getValue(l1, l2, '9am cloud amount (oktas)', default=mean['9am cloud amount (oktas)'])
    cloud3pm = getValue(l1, l2, '3pm cloud amount (oktas)', default=mean['3pm cloud amount (oktas)'])
    avgcloud = (cloud9am + cloud3pm) / 2
    weather = [avgtemp, rainfall, evap, sunshine, windGustSpeed, avgwindspeed, avghumidity, avgpressure, avgcloud]
    col_name = ["temp_avg", "rainfall", "evaporation", "sunshine", "windGustSpeed", "windSpeed_avg", "humidity_avg",
                "pressure_avg", "cloud_avg"]
    data = {col_name[i]: weather[i] for i in range(len(weather))}
    print(data)
    return data

    # http://www.bom.gov.au/climate/dwo/IDCJDW2124.latest.shtml
    #current_weahter_data = "http://reg.bom.gov.au/products/IDN60901/IDN60901.94768.shtml"

