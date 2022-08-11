from flask import *


def bad_request(message):
    response = jsonify({"data": {"user_name": "", "user_nick": ""}, "message": message,"code":400})
    response.status_code = 200
    return response


def unauthorized(message):
    response = jsonify({"data": {"user_name": "", "user_nick": ""}, "message": message,"code":401})
    response.status_code = 200
    return response


def forbidden(message):
    response = jsonify({"data": {"user_name": "", "user_nick": ""}, "message": message,"code":403})
    response.status_code = 200
    return response


def missed(message):
    response = jsonify({"data": {"user_name": "", "user_nick": ""}, "message": message,"code":404})
    response.status_code = 200
    return response


def servererror(message):
    response = jsonify({"data": {"user_name": "", "user_nick": ""}, "message": message,"code":500})
    response.status_code = 200
    return response