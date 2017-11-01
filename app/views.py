import flask
from flask import render_template
from sqlalchemy import func, tuple_
from sqlalchemy.exc import SQLAlchemyError

from app import app
from functools import wraps
from flask import request, Response

from config import AUTH_LOGIN, AUTH_PASS, CASTLE
from app.types import *

MSG_UNDER_CONSTRUCTION = 'Страница находится в разработке'


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


@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')


def get_squads():
    try:
        squads = Session().query(Squad).all()
        all_squads = []
        for squad in squads:
            all_squads.append(squad.squad_name)
        return all_squads
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/users')
def get_usernames():
    try:
        session = Session()
        actual_profiles = session.query(Character.user_id, func.max(Character.date)).group_by(Character.user_id)
        profiles = actual_profiles.all()
        players_count = len(profiles)
        characters = session.query(Character).filter(tuple_(Character.user_id, Character.date)
                                                     .in_([(a[0], a[1]) for a in profiles]))
        if CASTLE:
            characters = characters.filter_by(castle=CASTLE)
        characters = characters.all()
        all_users = []
        all_id = []
        all_names = []
        all_usernames = []
        for player in characters:
            user_id = player.user_id
            name = session.query(User).filter_by(id=user_id).first()
            username = session.query(User).filter_by(id=user_id).first()
            all_users.append(player.name)
            all_id.append(user_id)
            all_names.append(name)
            all_usernames.append(username.username)
        return render_template('users.html', output=all_users, link=all_id, count=players_count, names=all_names,
                               usernames=all_usernames)
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/player/<int:id>', methods=['GET'])
def get_user(id):
    session = Session()
    try:
        user = session.query(User).filter_by(id=id).first()
        return render_template('player.html', output=user)
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/squads')
def squads_function():
    return render_template('squads.html', output=get_squads())


@app.route('/top')
def top():
    return render_template('top.html', output=MSG_UNDER_CONSTRUCTION)


@app.route('/build')
def build():
    return render_template('build.html', output=MSG_UNDER_CONSTRUCTION)


@app.route('/reports')
def reports():
    return render_template('reports.html', output=MSG_UNDER_CONSTRUCTION)


@app.route('/squad_craft')
def squad_craft():
    return render_template('squad_craft.html', output=MSG_UNDER_CONSTRUCTION)