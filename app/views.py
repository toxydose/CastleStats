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


@app.route('/')
def index():
    return render_template("index.html")


@app.route('/robots.txt')
def robots():
    return render_template('robots.txt')


def get_squads():
    try:
        squads = Session().query(Squad).all()
        return squads
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


@app.route('/users')
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
def get_user(id):
    session = Session()
    try:
        user = session.query(User).filter_by(id=id).first()
        return render_template('player.html', output=user)
    except SQLAlchemyError:
        Session.rollback()
        return flask.Response(status=400)


stuff = {'pri': [
                 ['Меч Ученика', 'grade0'], ['Короткий меч', 'grade0'], ['Длинный меч', 'grade0'],
                 ['Меч Вдовы', 'grade0'], ['Меч Рыцаря', 'grade0'],
                 ['Короткое копье', 'grade0'], ['Длинное копье', 'grade0'],
                 ['Эльфийское копье', 'grade1'], ['Эльфийский меч', 'grade1'], ['Рапира', 'grade1'],
                 ['Кирка шахтера', 'grade2'], ['Кузнечный молот', 'grade3'],
                 ['Молот гномов', 'grade3'], ['Костолом', 'grade4'],
                 ['Меч берсеркера', 'grade2'], ['Экскалибур', 'grade3'], ['Нарсил', 'grade4'],
                 ['Хранитель', 'grade2'], ['Трезубец', 'grade3'], ['Алебарда', 'grade4']
                ],
         'sec': [
                 ['Кухонный нож', 'grade0'], ['Боевой нож', 'grade0'],
                 ['Деревянный щит ', 'grade0'], ['Щит скелета', 'grade0'],
                 ['Бронзовый щит', 'grade0'], ['Серебряный щит', 'grade0'],
                 ['Мифриловый щит', 'grade1'],
                 ['Клещи', 'grade3'],
                 ['Кинжал охотника', 'grade2'], ['Кинжал демона', 'grade3'], ['Кинжал триумфа', 'grade4'],
                 ['Щит хранителя', 'grade2'], ['Щит паладина', 'grade3'], ['Щит крестоносца', 'grade4'],
                 ['Кинжал', 'grade1']
                ],
         'head': [
                  ['Шляпа', 'grade0'], ['Стальной шлем', 'grade0'], ['Серебряный шлем', 'grade0'],
                  ['Мифриловый шлем', 'grade1'],
                  ['Шапка охотника', 'grade2'], ['Шапка демона', 'grade3'], ['Шапка триумфа', 'grade4'],
                  ['Шлем хранителя', 'grade2'], ['Шлем паладина', 'grade3'], ['Шлем крестоносца', 'grade4']
                 ],
         'arms': [
                  ['Кожаные перчатки', 'grade0'], ['Стальные перчатки', 'grade0'],
                  ['Серебряные перчатки', 'grade0'],
                  ['Мифриловые перчатки', 'grade1'],
                  ['Рукавицы', 'grade3'],
                  ['Браслеты охотника', 'grade2'], ['Браслеты демона', 'grade3'], ['Браслеты триумфа', 'grade4'],
                  ['Перчатки хранителя', 'grade2'], ['Перчатки паладина', 'grade3'], ['Перчатки крестоносца', 'grade4'],
                  ['Браслеты', 'grade0'],
                 ],
         'armor': [
                   ['Плотная куртка', 'grade0'], ['Кожаный доспех', 'grade0'], ['Стальная броня', 'grade0'],
                   ['Мифриловая броня', 'grade1'],
                   ['Кузнечная роба', 'grade3'],
                   ['Куртка охотника', 'grade2'], ['Куртка демона', 'grade3'], ['Куртка триумфа', 'grade4'],
                   ['Броня хранителя', 'grade2'], ['Броня паладина', 'grade3'], ['Броня крестоносца', 'grade4']
                  ],
         'legs': [
                  ['Сандалии', 'grade0'], ['Кожаные сапоги', 'grade0'], ['Стальные сапоги', 'grade0'],
                  ['Серебряные сапоги', 'grade0'],
                  ['Мифриловые сапоги', 'grade1'],
                  ['Ботинки охотника', 'grade2'], ['Ботинки демона', 'grade3'], ['Ботинки триумфа', 'grade4'],
                  ['Сапоги хранителя', 'grade2'], ['Сапоги паладина', 'grade3'], ['Сапоги крестоносца', 'grade4']
                 ]
         }

equip_parts = ['pri', 'sec', 'head', 'arms', 'armor', 'legs']

colors = {'grade0': None,
          'grade1': 'e81224',   # red
          'grade2': '16c60c',   # green
          'grade3': '3a96dd',   # blue
          'grade4': 'f7630c'    # orange
          }


@app.route('/member-equip/<int:squad_id>', methods=['GET'])
@requires_auth
def get_member_equip(squad_id):
    session = Session()
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
        for character, user, equip in members:
            member_equip = []
            if equip:
                for part in equip_parts:
                    flag = False
                    for item, grade in stuff[part]:
                        if item in equip:
                            member_equip.append([item, colors[grade]])
                            flag = True
                            break
                    if not flag:
                        member_equip.append([' ', None])
            else:
                member_equip = [[' ', None], [' ', None], [' ', None], [' ', None], [' ', None], [' ', None]]
            members_new.append([character, user, member_equip])

        squad = session.query(Squad).filter(Squad.chat_id == squad_id)
        squad = squad.first()
        return render_template('squad_member_equip.html', members=members_new, squad=squad)
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