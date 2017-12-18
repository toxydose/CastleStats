import flask
from flask import render_template, session as flask_session
from sqlalchemy import func, tuple_
from sqlalchemy.exc import SQLAlchemyError

from app import app
from functools import wraps
from flask import request, Response

from app.constants import *
from config import AUTH_LOGIN, AUTH_PASS, CASTLE, APP_SECRET_KEY
from app.types import *

from datetime import datetime, timedelta


app.secret_key = APP_SECRET_KEY


@app.before_request
def function_session():
    flask_session.modified = True
    flask_session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)


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


def requires_bauth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)

    return decorated


def requires_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if 'user_id' in flask_session:
            return func(*args, **kwargs)
        else:
            return render_template('403.html')
    return wrapper


@app.route('/', methods=['GET'])
def index():
    try:
        session = Session()
        if 'token' in request.args:
            token = request.args.getlist('token')
            auth = session.query(Auth).filter(Auth.id == token).first()
            if auth:
                session.delete(auth)
                session.commit()
                flask_session['user_id'] = auth.user_id
        if 'user_id' in flask_session:
            user = session.query(User).filter(User.id == flask_session['user_id']).first()
            if user:
                return render_template("index.html", user=user.username)
        return render_template('403.html')
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/403')
def not_authorized():
    return render_template('403.html')


@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')


def get_squads():
    try:
        all_squads = Session().query(Squad).join(SquadMember, SquadMember.squad_id == Squad.chat_id).all()
        squads = []
        for squad in all_squads:
            squads.append(squad)
        return squads
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/users')
@requires_auth
@requires_bauth
def get_usernames():
    try:
        session = Session()
        sub_query = session.query(Character.user_id, func.max(Character.date)).group_by(Character.user_id).subquery()
        characters = session.query(Character, User).filter(tuple_(Character.user_id, Character.date)
                                                           .in_(sub_query))\
            .join(User, User.id == Character.user_id)

        if CASTLE:
            characters = characters.filter(Character.castle == CASTLE)
        characters = characters.all()
        return render_template('users.html', characters=characters)
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/player/<int:id>', methods=['GET'])
@requires_auth
def get_user(id):
    session = Session()
    try:
        user = session.query(User).filter_by(id=id).first()
        return render_template('player.html', output=user)
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/member-equip/<int:squad_id>', methods=['GET'])
@requires_auth
def get_member_equip(squad_id):
    allowed = False
    try:
        session = Session()
        id = flask_session['user_id']
        admins = session.query(Admin).filter(Admin.user_id == id).order_by(Admin.admin_type).all()
        for adm in admins:
            where_admin = adm.admin_group
            admin_type = adm.admin_type
            if admin_type == 0 or admin_type == 1:
                allowed = True
            else:
                if where_admin == squad_id:
                    allowed = True
        if allowed:
            try:
                sub_query_1 = session.query(Character.user_id, func.max(Character.date)).group_by(Character.user_id).subquery()
                sub_query_2 = session.query(Equip.user_id, func.max(Equip.date)).group_by(Equip.user_id).subquery()
                members = session.query(Character, User, Equip.equip) \
                    .filter(tuple_(Character.user_id, Character.date).in_(sub_query_1)) \
                    .join(User, User.id == Character.user_id) \
                    .outerjoin(Equip, User.id == Equip.user_id) \
                    .join(SquadMember, SquadMember.user_id == Character.user_id) \
                    .filter((tuple_(Equip.user_id, Equip.date).in_(sub_query_2)) | (Equip.user_id.is_(None))) \
                    .filter(SquadMember.squad_id == squad_id) \
                    .order_by(Character.level.desc())
                if CASTLE:
                    members = members.filter(Character.castle == CASTLE)
                members = members.all()
                members_new = []
                total_attack = 0
                total_defence = 0
                total_lvl = 0
                for character, user, equip in members:
                    member_equip = []
                    total_attack += character.attack
                    total_defence += character.defence
                    total_lvl += character.level
                    if equip:
                        equip_lines = equip.split('\n')
                        for part in EQUIP_PARTS:
                            flag = False
                            for item, grade, alias in STUFF[part]:
                                for line in equip_lines:
                                    if item in line:
                                        mod_str = line.split(item)[0]
                                        if alias:
                                            member_equip.append([mod_str + alias, COLORS[grade]])
                                        else:
                                            member_equip.append([mod_str + item, COLORS[grade]])
                                        flag = True
                                        break
                                if flag:
                                    break
                            if not flag:
                                member_equip.append([' ', None])
                    else:
                        member_equip = [[' ', None], [' ', None], [' ', None], [' ', None],
                                        [' ', None], [' ', None], [' ', None]]

                    if character.date > (datetime.now() - timedelta(days=7)):
                        fresh = PROFILE_FRESH
                    else:
                        fresh = PROFILE_NOT_FRESH
                    members_new.append([character, user, member_equip, fresh])

                if len(members) > 0:
                    avg_lvl = total_lvl/len(members)
                else:
                    avg_lvl = 0
                squad = session.query(Squad).filter(Squad.chat_id == squad_id)
                squad = squad.first()
                return render_template('squad_member_equip.html', members=members_new, squad=squad, avg_lvl=round(avg_lvl, 1),
                                       total_attack=total_attack, total_defence=total_defence)
            except SQLAlchemyError:
                Session.rollback()
                return flask.Response(status=400)
        else:
            return render_template('forbidden.html')
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/squads')
@requires_auth
def squads_function():
    return render_template('squads.html', output=get_squads())


@app.route('/top')
@requires_auth
def top():
    return render_template('top.html', output=MSG_UNDER_CONSTRUCTION)


@app.route('/build')
@requires_auth
def build():
    return render_template('build.html', output=MSG_UNDER_CONSTRUCTION)


@app.route('/reports')
@requires_auth
def reports():
    return render_template('reports.html', output=MSG_UNDER_CONSTRUCTION)


@app.route('/squad_craft')
@requires_auth
def squad_craft():
    return render_template('squad_craft.html', output=MSG_UNDER_CONSTRUCTION)
