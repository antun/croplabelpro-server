import flask
import functions_framework
from flask import jsonify

@functions_framework.http
def prompt(request: flask.Request) -> flask.typing.ResponseReturnValue:
    print('request: ', request)
    return jsonify(
        msg="Hello world!"
    )

