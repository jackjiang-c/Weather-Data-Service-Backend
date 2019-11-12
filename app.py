import pickle
import json
from functools import wraps
from time import time, sleep

import requests
from flask import Flask
from flask import request
from flask_restplus import Resource, Api, abort
from flask_restplus import reqparse
from flask_restplus import fields
from flask_restplus import inputs
from itsdangerous import JSONWebSignatureSerializer, BadSignature, SignatureExpired
from flask_cors import CORS

app = Flask(__name__)
api = Api(app, authorizations={
                'API-KEY': {
                    'type': 'apiKey',
                    'in': 'header',
                    'name': 'AUTH-TOKEN'
                }
            },
          default= 'User credentials',
          security='API-KEY',
          description="This is just a simple example to show how publish data as a service.")
port = 9999
cors = CORS(app)
ns = api.namespace('api', description='Weather Predict')

# api schema:
credential_model = api.model('credential', {
    'username': fields.String,
    'password': fields.String
})

# parser
parser = reqparse.RequestParser()
credential_parser = reqparse.RequestParser()
credential_parser.add_argument('username', type = str)
credential_parser.add_argument('password', type = str)
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

credential_model = api.model('credential', {
    'username': fields.String,
    'password': fields.String
})
@app.before_request
def before_request_func():
    print("before_request is running!")


@ns.route('/weather')
class Weather(Resource):
    #@requires_auth
    def get(self):
        print("Using api to get weather data!")
        # https://openweathermap.org/appid
        response = requests.get('http://api.openweathermap.org/data/2.5/forecast?id=2147714&APPID=9d5a57bcfdb7d976e995381200306ca6')
        if response.status_code == 404:
            return {}
        recv = json.loads(response.content)
        print(recv)
        return response.json()


@ns.route('/predict')
class Prediction(Resource):
    @requires_auth
    def post(self):
        result = {}
        return result


@api.route('/users/authenticate')
class Authentication(Resource):
    @api.response(200,'Successful')
    @api.doc(description='Generates a authentication token')
    @api.expect(credential_parser, validate=True)
    def post(self):
        args = credential_parser.parse_args()
        # need to get to
        username = args.get('username')
        password = args.get('password')
        sleep(0.5)
        if username == 'admin' and password == 'admin':
            #{'id': 0, 'firstName':'Oyster', 'lastName':'Quin'}
            return {"token": auth.generate_token(username)}
        return {'message': 'Username or password is incorrect'}, 401


if __name__ == '__main__':
    SECRET_KEY = "I DONT ALWAYS USE INTERNET EXPLORER; BUT WHEN I DO, ITS USUALLY TO DOWNLOAD A BETTER BROWSER"
    expires_in = 60000
    auth = AuthenticationToken(SECRET_KEY, expires_in)
    # run the application
    app.run(debug=True, port=port)

