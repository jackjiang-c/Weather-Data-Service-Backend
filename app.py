import pickle
import json
from functools import wraps
from time import time, sleep
import sqlite3

import requests
from flask import Flask
from flask import request, jsonify
from flask_restplus import Resource, Api, abort
from flask_restplus import reqparse
from flask_restplus import fields
from flask_restplus import inputs
from itsdangerous import JSONWebSignatureSerializer, BadSignature, SignatureExpired
from flask_cors import CORS
from sklearn.externals import joblib

import modules.db as db
import modules.weather_api as weather
from models.Predict_model import predictWeather
from modules.helps import is_number, give_solution

app = Flask(__name__)
api = Api(app, authorizations={
    'API-KEY': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'AUTH-TOKEN'
    }
},
      default='General request',
      security='API-KEY',
      description="Weather prediction service api")

port = 9999
cors = CORS(app)

users = api.namespace('users', description='User operations')
apis = api.namespace('api', description='Statistics about the api')

# api user registration schema:
registration_model = users.model('registration', {
    'username': fields.String(description='The username of user', require=True, min_length=4),
    'password': fields.String(description='The password of user', require=True, min_length=6),
    'firstName': fields.String(description='The first name of user', require=True, min_length=1),
    'lastName': fields.String(description='The last name of user', require=True, min_length=1),
    'age': fields.Integer(description='The age of user', require=True, min=0, max=200),
    'gender': fields.String(description='The gender of user', require=True, enum=['Male', 'Female'])
})

user_model = api.model('user information', {
    'firstName': fields.String(description='The first name of user', require=True, min_length=1),
    'lastName': fields.String(description='The last name of user', require=True, min_length=1),
    'age': fields.Integer(description='The age of user', require=True, min=0, max=200),
    'gender': fields.String(description='The gender of user', require=True, enum=['Male', 'Female'])
})

climate_model = users.model('climate', {
    'temp_avg': fields.Float(description='The average temperature', require=True, min=-50, max=80),
    'rainfall': fields.Float(description='The railfall', require=True, min=0, max=2000),
    'evaporation': fields.Float(description='The evaporation', require=True, min=0, max=1000),
    'sunshine': fields.Float(description='The sunshine duration', require=True, min=0, max=24),
    'windGustSpeed': fields.Float(description='The wind gust speed', require=True, min=0, max=500),
    'windSpeed_avg': fields.Float(description='The average wind speed', require=True, min=0, max=500),
    'humidity_avg': fields.Float(description='The average humidity', require=True, min=0, max=100),
    'pressure_avg': fields.Float(description='The average pressure', require=True, min=0, max=2000),
    'cloud_avg': fields.Float(description='The wind gust speed', require=True, min=0, max=100)
})

api_type = api.model('api_type', {
    'api_type': fields.String
})

# parser
# parser = reqparse.RequestParser()
credential_parser = reqparse.RequestParser()
credential_parser.add_argument('username', type=str)
credential_parser.add_argument('password', type=str)


# Authentication token Generation class
class AuthenticationToken:
    def __init__(self, secret_key, expires_in):
        self.secret_key = secret_key
        self.expires_in = expires_in
        self.serializer = JSONWebSignatureSerializer(secret_key)

    def generate_token(self, username):
        info = {
            'username': username,
            'creation_time': time()
        }
        token = self.serializer.dumps(info)
        return token.decode()

    def validate_token(self, token):
        info = self.serializer.loads(token.encode())
        if time() - info['creation_time'] > self.expires_in:
            raise SignatureExpired("The Token has been expired; get a new token")
        return info['username']


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('AUTH-TOKEN')
        if not token:
            abort(401, 'Authentication token is missing')
        try:
            user_endpoint = '/get_info/'
            userEndPointIndex = request.url.find(user_endpoint)
            user = auth.validate_token(token)
            if userEndPointIndex >= 0:
                current_user = db.getuser(user_db, username=user)
                uid = int(request.url[userEndPointIndex + len(user_endpoint):])
                # if the current user is not admin, it has no permission to access any other user's information
                if current_user[5] != 'Admin' and current_user[0] != uid:
                    abort(403, "Current user has no permission to access this endpoint.")
            usage_endpoint = '/usage'
            usageEndPointIndex = request.url.find(usage_endpoint)
            if usageEndPointIndex >= 0:
                current_user = db.getuser(user_db, username=user)
                if current_user[5] != 'Admin':
                    abort(403, "Only authorized user has permission to access this endpoint.")
        except SignatureExpired as e:
            abort(401, e.message)
        except BadSignature as e:
            abort(401, e.message)
        return f(*args, **kwargs)

    return decorated


@users.route('/get_weather')
class getWeather(Resource):
    @users.response(401, 'Authentication token is missing or expired')
    @users.response(200, 'Get the current weather Successful from the upstream weather api')
    @users.response(504, 'No response from the upstream weather api')
    @users.doc(description='get real time weather data')
    @requires_auth
    def get(self):
        response = requests.get(
            'http://api.openweathermap.org/data/2.5/weather?id=2147714&APPID=9d5a57bcfdb7d976e995381200306ca6')
        if response.status_code != 200:
            return {'message': 'No current weather available!'}, 504
        recv = json.loads(response.content)
        # dummy current weather information (same json structure)
        """recv = {
            "coord": {
                "lon": 151.21,
                "lat": -33.87
            },
            "weather": [
                {
                    "id": 800,
                    "main": "Clear",
                    "description": "clear sky",
                    "icon": "01n"
                }
            ],
            "base": "stations",
            "main": {
                "temp": 287.38,
                "pressure": 1014,
                "humidity": 33,
                "temp_min": 284.82,
                "temp_max": 291.15
            },
            "visibility": 10000,
            "wind": {
                "speed": 4.1,
                "deg": 250
            },
            "clouds": {
                "all": 0
            },
            "dt": 1573655580,
            "sys": {
                "type": 1,
                "id": 9600,
                "country": "AU",
                "sunrise": 1573670684,
                "sunset": 1573720463
            },
            "timezone": 39600,
            "id": 2147714,
            "name": "Sydney",
            "cod": 200
        }"""
        w = weather.convert_weather_data(recv)
        # dummy climate
        """cli = {'temp_avg': 25.1, 'rainfall': 0.0, 'evaporation': 14.4, 'sunshine': 12.4, 'windGustSpeed': 56.0,
               'windSpeed_avg': 18.5, 'humidity_avg': 43.5, 'pressure_avg': 1013.2, 'cloud_avg': 4.0}"""
        cli = weather.get_weather_data()
        db.log_usage(log_db, 'get_weather', time())
        return jsonify({'weather': w, 'climate': cli})


@users.route('/predict_weather')
class Prediction(Resource):
    @users.response(401, 'Authentication token is missing or expired')
    @users.response(200, 'The prediction has been made successfully')
    @users.doc(description='Predict wind, rain and temperature by climate data')
    @users.expect(climate_model, validate=True)
    @requires_auth
    def post(self):
        climate = request.json
        value_validation = {"temp_avg": [-50, 80], "rainfall": [0, 2000], "evaporation": [0, 1000],
                            "sunshine": [0, 24], "windGustSpeed": [0, 500], "windSpeed_avg": [0, 500],
                            "humidity_avg": [0, 100], "pressure_avg": [0, 2000], "cloud_avg": [0, 100]}
        transform = dict()
        for key in value_validation:
            data = climate.get(key, None)
            if data is None:
                return {'message': 'Missing the property {}'.format(key)}, 400
            if not is_number(data):
                return {'message': 'The property {}\'s value is invalid'.format(key)}, 400
            if data < value_validation[key][0] or data > value_validation[key][1]:
                return {'message': 'The property {} is invalid'.format(key)}, 400
            transform[key] = data
        result = predictWeather(transform, rain_predictor, wind_predictor, temp_predictor)
        db.log_usage(log_db, 'predict_weather', time())
        sleep(0.2)
        result['temp'] = float(format(result['temp'], '.1f'))
        token = request.headers.get('AUTH-TOKEN')
        user = auth.validate_token(token)
        current_user = db.getuser(user_db, username=user)
        r = give_solution(result['temp'], result['wind'], result['rain'], current_user[4], current_user[3])
        result['clothes'] = r
        return jsonify(result)


@users.route('/signup')
class Registration(Resource):
    @users.response(200, 'The new user has been created successfully')
    @users.response(400, 'The validation error, some fields are invalid or missing.')
    @users.doc(description='Create a new user')
    @users.expect(registration_model, validate=True)
    def post(self):
        reg_info = request.json
        validator = {'username': [4], 'password': [6], 'firstName': [1], 'lastName': [1], 'age': [1, 199]}
        for key in validator:
            data = reg_info.get(key, None)
            if data is None:
                return {'message': 'Missing the property {}'.format(key)}, 400
            if key == 'age':
                if not is_number(data):
                    return {'message': 'The property {}\'s value is invalid'.format(key)}, 400
                if data < validator[key][0] or data > validator[key][1]:
                    return {'message': 'The property {} is invalid'.format(key)}, 400
            else:
                if len(data) < validator[key][0]:
                    return {'message': 'The property {} is invalid'.format(key)}, 400
        reg_info['role'] = 'User'
        result = db.register(user_db, reg_info)
        sleep(0.5)  # simulate delay
        if result:
            db.log_usage(log_db, 'register', time())
            return jsonify({'message': 'Success'})
        else:
            return {'message': 'Username: ' + reg_info['username'] + ' has already been taken.'}, 400


@users.route('/get_info/<int:uid>')
class Users(Resource):
    @users.response(200, 'The user information has been generated and returned successfully', model=user_model)
    @users.response(401, 'Authentication token is missing or expired')
    @users.response(403, 'No permission to access. Normal user can only access own id endpoint')
    @users.response(404, 'The user id is not exist')
    @users.doc(description='Return the user information by specific id', params={'id': 'A user ID'})
    @requires_auth
    def get(self, uid):
        user_info = db.getuser(user_db, uid=uid)
        if user_info is None:
            return {'message': 'ID has not found'}, 404
        else:
            result = {'firstName': user_info[1], 'lastName': user_info[2], 'age': user_info[3],
                      'gender': user_info[4], 'role': user_info[5]}
            return jsonify(result)


@users.route('/login')
class Authentication(Resource):
    @users.response(200, 'user login successfully and a authentication has been returned.')
    @users.response(401, 'user\'s login credential information is incorrect')
    @users.doc(description='Return an authentication token for user')
    @users.expect(credential_parser, validate=True)
    def post(self):
        args = credential_parser.parse_args()
        username = args.get('username')
        password = args.get('password')
        sleep(0.3)  # simulate delay
        userinfo = db.login(user_db, (username, password))
        if userinfo is None:
            return {'message': 'Username or password is incorrect'}, 401
        else:
            db.log_usage(log_db, 'authenticate', time())
            return jsonify({'token': auth.generate_token(username), 'id': userinfo[0]})


@apis.route('/usage')
class Usage(Resource):
    @apis.response(200, 'The usage data has generated and returned successfully')
    @apis.response(404, 'The usage information does not exist')
    @apis.response(403, 'No permission to access this api')
    @apis.doc(description='Generate all api usage information')
    @requires_auth
    def get(self):
        weather_usage_total = db.get_api_usage(log_db, 'get_weather', type='t')
        weather_usage_24 = db.get_api_usage(log_db, 'get_weather', type='24')
        weather_usage_7d = db.get_api_usage(log_db, 'get_weather', type='7d')
        # predict api
        predict_usage_total = db.get_api_usage(log_db, 'predict_weather', type='t')
        predict_usage_24 = db.get_api_usage(log_db, 'predict_weather', type='24')
        predict_usage_7d = db.get_api_usage(log_db, 'predict_weather', type='7d')
        # register api only record the successful registration
        register_usage_total = db.get_api_usage(log_db, 'register', type='t')
        register_usage_24 = db.get_api_usage(log_db, 'register', type='24')
        register_usage_7d = db.get_api_usage(log_db, 'register', type='7d')
        # authentication api
        auth_usage_total = db.get_api_usage(log_db, 'authenticate', type='t')
        auth_usage_24 = db.get_api_usage(log_db, 'authenticate', type='24')
        auth_usage_7d = db.get_api_usage(log_db, 'authenticate', type='7d')
        result = {'get_weather': {'last24': weather_usage_24, 'last7d': weather_usage_7d, 'total': weather_usage_total},
                  'predict_weather': {'last24': predict_usage_24, 'last7d': predict_usage_7d, 'total': predict_usage_total},
                  'login': {'last24': auth_usage_24, 'last7d': auth_usage_7d, 'total': auth_usage_total},
                  'signup': {'last24': register_usage_24, 'last7d': register_usage_7d, 'total': register_usage_total}}
        return jsonify(result)


@apis.route('/usage/<string:api_name>')
class Usage(Resource):
    @apis.response(200, 'The usage information has return successfully')
    @apis.response(404, 'The usage information does not exist')
    @apis.response(403, 'No permission to access this api')
    @apis.doc(description='Generate specific api usage information',params={'api_name': 'The name of the api'})
    def get(self, api_name):
        log_map = {'predict_weather': 'predict_weather', 'login':'authenticate', 'get_weather':'get_weather', 'signup':'register'}
        if api_name not in log_map.keys():
            apis.abort(404, "API {} doesn't support to be check or doesn't exist".format(api_name))
        usage_total = db.get_api_usage(log_db, log_map[api_name], type='t')
        usage_24 = db.get_api_usage(log_db, log_map[api_name], type='24')
        usage_7d = db.get_api_usage(log_db, log_map[api_name], type='7d')
        return {'last24': usage_24, 'last7d': usage_7d, 'total': usage_total}


if __name__ == '__main__':
    log_db = 'log.db'
    user_db = 'user.db'
    # initialize dababase
    db.db_init(user_db, 'user')
    db.db_init(log_db, 'log')
    # load saved models
    rain_predictor = joblib.load('./models/rain.model')
    temp_predictor = joblib.load('./models/temp.model')
    wind_predictor = joblib.load('./models/wind.model')
    # set up authentication
    SECRET_KEY = "I DONT ALWAYS USE INTERNET EXPLORER BUT WHEN I DO ITS USUALLY TO DOWNLOAD A BETTER BROWSER"
    expires_in = 60000
    auth = AuthenticationToken(SECRET_KEY, expires_in)
    # run the application
    app.run(debug=True, port=port)
