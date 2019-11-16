import pickle
import json
from functools import wraps
from time import time, sleep
import sqlite3

import requests
from flask import Flask
from flask import request
from flask_restplus import Resource, Api, abort
from flask_restplus import reqparse
from flask_restplus import fields
from flask_restplus import inputs
from itsdangerous import JSONWebSignatureSerializer, BadSignature, SignatureExpired
from flask_cors import CORS


import random
import modules.db as db
import modules.waether_api as weather

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

# api user credential schema:
credential_model = api.model('credential', {
    'username': fields.String,
    'password': fields.String
})

# api user registration schema:
registration_model =api.model('registration',{
    'username': fields.String,
    'password': fields.String,
    'firstName': fields.String,
    'lastName': fields.String,
    'age': fields.Integer,
})

# parser
#parser = reqparse.RequestParser()
credential_parser = reqparse.RequestParser()
credential_parser.add_argument('username', type=str)
credential_parser.add_argument('password', type=str)

registration_parser = reqparse.RequestParser()
registration_parser.add_argument('username', type=str)
registration_parser.add_argument('password', type=str)
registration_parser.add_argument('firstName', type=str)
registration_parser.add_argument('lastName', type=str)
registration_parser.add_argument('age', type=int)

# Preparing the Classifier
# load classifier from pickle


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
            user = auth.validate_token(token)
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
        print("Using api to get weather data!")
        # https://openweathermap.org/appid
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
        db.log_usage(usage_db,'weather', time())
        result = weather.convert_weather_data(recv)
        return result


@ns.route('/predict')
class Prediction(Resource):
    @requires_auth
    def post(self):
        print("Predicting weahter")
        list = [20, 30, 40, 50, 60, 70, 80, 52, 23, 100]
        result = random.choices(list, k=7)
        db.log_usage(usage_db,'predict',time())
        sleep(0.5)
        return result


@api.route('/users/register')
class Registration(Resource):
    @api.response(200, 'Successful')
    @api.doc(description='Register a normal user')
    @api.expect(registration_parser, validate=True)
    def post(self):
        args = registration_parser.parse_args()
        reg_info = dict()
        reg_info['username'] = args.get('username')
        reg_info['password'] = args.get('password')
        reg_info['firstName'] = args.get('firstName')
        reg_info['lastName'] = args.get('lastName')
        reg_info['age'] = args.get('age')
        reg_info['role'] = 'User'
        result = db.register(user_db, reg_info)
        if result:
            return 'Success'
        else:
            return reg_info['username'] + ' has already been taken', 403

@api.route('/users/authenticate')
class Authentication(Resource):
    @api.response(200, 'Successful')
    @api.doc(description='Generates a authentication token')
    @api.expect(credential_parser, validate=True)
    def post(self):
        args = credential_parser.parse_args()
        username = args.get('username')
        password = args.get('password')
        sleep(0.5)
        if username == 'admin' and password == 'admin':
            info = {'id': 0, 'firstName': 'Oyster', 'lastName': 'Quin', 'role': 'Admin',
                    'token': auth.generate_token(username)}
            return info
        if username == 'user' and password == 'user':
            info = {'id': 1, 'firstName': 'Ginny', 'lastName': 'Sharp', 'role': 'User',
                    'token': auth.generate_token(username)}
            return info
        return {'message': 'Username or password is incorrect'}, 401


@api.route('/usage')
class Usage(Resource):
    @api.response(200, 'Successful')
    @api.doc(description='Generate api usage information')
    @requires_auth
    def get(self):
        weather_usage = db.get_api_usage_24(usage_db,'weather')
        predict_usage = db.get_api_usage_24(usage_db,'predict')
        return {'weather': weather_usage, 'predict': predict_usage,'Good': None}


if __name__ == '__main__':
    usage_db = 'log.db'
    user_db = 'user.db'
    # initialize dababase
    db.db_init(user_db,'user')
    db.db_init(usage_db,'log')
    # set up authentication
    SECRET_KEY = "I DONT ALWAYS USE INTERNET EXPLORER BUT WHEN I DO ITS USUALLY TO DOWNLOAD A BETTER BROWSER"
    expires_in = 60000
    auth = AuthenticationToken(SECRET_KEY, expires_in)
    # run the application
    app.run(debug=True, port=port)
