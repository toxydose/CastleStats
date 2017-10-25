from flask import render_template
from app import app
from functools import wraps
from flask import request, Response
from config import AUTH_LOGIN, AUTH_PASS


def check_auth(username, password):
    """This function is called to check if a username /
    password combination is valid.
    """
    return username == AUTH_LOGIN and password == AUTH_PASS


def authenticate():
    """Sends a 401 response that enables basic auth"""
    return Response(
        'Could not verify your access level for that URL.\n'
        'You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


if AUTH_PASS and AUTH_LOGIN:
    @app.route('/')
    @requires_auth
    def index():
        return render_template("index.html")
else:
    @app.route('/')
    def index():
        return render_template("index.html")