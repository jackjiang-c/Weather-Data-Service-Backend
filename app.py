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
from modules.helps import is_number

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
          description="This is just a simple example to show how publish data as a service.")
port = 9999
cors = CORS(app)
ns = api.namespace('api', description='Weather Predict')

# api user registration schema:
registration_model = api.model('registration', {
    'username': fields.String,
    'password': fields.String,
    'firstName': fields.String,
    'lastName': fields.String,
    'age': fields.Integer,
})

# api climate schema:
climate_model = api.model('climate', {
    'temp_avg': fields.Float,
    'rainfall': fields.Float,
    'evaporation': fields.Float,
    'sunshine': fields.Float,
    'windGustSpeed': fields.Float,
    'windSpeed_avg': fields.Float,
    'humidity_avg': fields.Float,
    'pressure_avg': fields.Float,
    'cloud_avg': fields.Float
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
            user_endpoint = '/users/'
            userEndPointIndex = request.url.find('/users/')
            user = auth.validate_token(token)
            if userEndPointIndex >= 0:
                usageEndPointIndex = request.url.find('/usage')
                current_user = db.getuser(user_db, username=user)
                if usageEndPointIndex < 0:
                    uid = int(request.url[userEndPointIndex + len(user_endpoint):])
                    # if the current user is not admin, it has no permission to access any other user's information
                    if current_user[4] != 'Admin' and current_user[0] != uid:
                        abort(403, "Current user has no permission to access this endpoint.")
                else:
                    if current_user[4] != 'Admin':
                        abort(403, "Current user has no permission to access this endpoint.")
        except SignatureExpired as e:
            abort(401, e.message)
        except BadSignature as e:
            abort(401, e.message)
        return f(*args, **kwargs)

    return decorated


@ns.route('/weather')
class Weather(Resource):
    @api.response(200, 'Successful')
    @requires_auth
    def get(self):
        """response = requests.get('http://api.openweathermap.org/data/2.5/weather?id=2147714&APPID=9d5a57bcfdb7d976e995381200306ca6')
        if response.status_code != 200:
            return {'message': 'No current weather available!'}, 504
        recv = json.loads(response.content)"""
        # dummy current weather information (same json structure)
        recv = {
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
        }
        w = weather.convert_weather_data(recv)
        # dummy climate
        """cli = {'temp_avg': 25.1, 'rainfall': 0.0, 'evaporation': 14.4, 'sunshine': 12.4, 'windGustSpeed': 56.0,
               'windSpeed_avg': 18.5, 'humidity_avg': 43.5, 'pressure_avg': 1013.2, 'cloud_avg': 4.0}"""
        cli = weather.get_weather_data()
        db.log_usage(log_db, 'weather', time())
        return jsonify({'weather': w, 'climate': cli})


@ns.route('/predict')
class Prediction(Resource):
    @ns.doc(description='predict wind, rain and temperature by climate data')
    @ns.expect(climate_model, validate=True)
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
        db.log_usage(log_db, 'predict', time())
        sleep(0.4)
        result['temp'] = float(format(result['temp'], '.1f'))
        return jsonify(result)


@api.route('/users/register')
class Registration(Resource):
    @api.response(200, 'Successful')
    @api.doc(description='Register a normal user')
    @api.expect(registration_model, validate=True)
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


@api.route('/users/<int:uid>')
class Users(Resource):
    @api.response(200, 'Successful')
    @api.doc(description='Get user information by its ID')
    @requires_auth
    def get(self, uid):
        user_info = db.getuser(user_db, uid=uid)
        if user_info is None:
            return {'message': 'ID has not found'}, 404
        else:
            result = {'firstName': user_info[1], 'lastName': user_info[2], 'age': user_info[3],
                      'role': user_info[4]}
            return jsonify(result)


@api.route('/users/authenticate')
class Authentication(Resource):
    @api.response(200, 'Successful')
    @api.doc(description='Generates a authentication token')
    @api.expect(credential_parser, validate=True)
    def post(self):
        args = credential_parser.parse_args()
        username = args.get('username')
        password = args.get('password')
        sleep(0.5)  # simulate delay
        userinfo = db.login(user_db, (username, password))
        if userinfo is None:
            return {'message': 'Username or password is incorrect'}, 401
        else:
            db.log_usage(log_db, 'authenticate', time())
            return jsonify({'token': auth.generate_token(username), 'id': userinfo[0]})


@api.route('/users/usage')
class Usage(Resource):
    @api.response(200, 'Successful')
    @api.doc(description='Generate major api usage information')
    @requires_auth
    def get(self):
        weather_usage_total = db.get_api_usage(log_db, 'weather', type='t')
        weather_usage_24 = db.get_api_usage(log_db, 'weather', type='24')
        weather_usage_7d = db.get_api_usage(log_db, 'weather', type='7d')
        # predict api
        predict_usage_total = db.get_api_usage(log_db, 'predict', type='t')
        predict_usage_24 = db.get_api_usage(log_db, 'predict', type='24')
        predict_usage_7d = db.get_api_usage(log_db, 'predict', type='7d')
        # register api only record the successful registration
        register_usage_total = db.get_api_usage(log_db, 'register', type='t')
        register_usage_24 = db.get_api_usage(log_db, 'register', type='24')
        register_usage_7d = db.get_api_usage(log_db, 'register', type='7d')
        # authentication api
        auth_usage_total = db.get_api_usage(log_db, 'authenticate', type='t')
        auth_usage_24 = db.get_api_usage(log_db, 'authenticate', type='24')
        auth_usage_7d = db.get_api_usage(log_db, 'authenticate', type='7d')
        result = {'weather': {'last24': weather_usage_24, 'last7d': weather_usage_7d, 'total': weather_usage_total},
                  'predict': {'last24': predict_usage_24, 'last7d': predict_usage_7d, 'total': predict_usage_total},
                  'authenticate': {'last24': auth_usage_24, 'last7d': auth_usage_7d, 'total': auth_usage_total},
                  'register': {'last24': register_usage_24, 'last7d': register_usage_7d, 'total': register_usage_total}}
        return jsonify(result)


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
