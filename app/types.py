# -*- coding: utf-8 -*-
from datetime import datetime
from enum import Enum
import logging

from sqlalchemy import (
    create_engine,
    Column, Integer, DateTime, Boolean, ForeignKey, UnicodeText, BigInteger
)
from sqlalchemy.dialects.mysql import DATETIME
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session

from config import DB


class AdminType(Enum):
    SUPER = 0
    FULL = 1
    GROUP = 2

    NOT_ADMIN = 100


ENGINE = create_engine(DB,
                       echo=False,
                       pool_size=200,
                       max_overflow=50,
                       isolation_level="READ UNCOMMITTED")

# FIX: имена констант?
LOGGER = logging.getLogger('sqlalchemy.engine')
Base = declarative_base()
Session = scoped_session(sessionmaker(bind=ENGINE))


class Group(Base):
    __tablename__ = 'groups'

    id = Column(BigInteger, primary_key=True)  # FIX: invalid name
    username = Column(UnicodeText(250))
    title = Column(UnicodeText(250))
    welcome_enabled = Column(Boolean, default=False)
    allow_trigger_all = Column(Boolean, default=False)
    allow_pin_all = Column(Boolean, default=False)
    bot_in_group = Column(Boolean, default=True)

    group_items = relationship('OrderGroupItem', back_populates='chat')
    squad = relationship('Squad', back_populates='chat')
    orders = relationship('Order', back_populates='chat')


class User(Base):
    __tablename__ = 'users'

    id = Column(BigInteger, primary_key=True)
    username = Column(UnicodeText(250))
    first_name = Column(UnicodeText(250))
    last_name = Column(UnicodeText(250))
    date_added = Column(DateTime, default=datetime.now())

    character = relationship('Character',
                             back_populates='user',
                             order_by='Character.date.desc()',
                             uselist=False)

    orders_confirmed = relationship('OrderCleared', back_populates='user')
    member = relationship('SquadMember', back_populates='user', uselist=False)
    equip = relationship('Equip',
                         back_populates='user',
                         order_by='Equip.date.desc()',
                         uselist=False)

    stock = relationship('Stock',
                         back_populates='user',
                         order_by='Stock.date.desc()',
                         uselist=False)

    report = relationship('Report',
                          back_populates='user',
                          order_by='Report.date.desc()')

    build_report = relationship('BuildReport',
                                back_populates='user',
                                order_by='BuildReport.date.desc()')

    def __repr__(self):
        user = ''
        if self.first_name:
            user += self.first_name + ' '
        if self.last_name:
            user += self.last_name + ' '
        if self.username:
            user += '(@' + self.username + ')'
        return user

    def __str__(self):
        user = ''
        if self.first_name:
            user += self.first_name + ' '
        if self.last_name:
            user += self.last_name
        return user


class WelcomeMsg(Base):
    __tablename__ = 'welcomes'

    chat_id = Column(BigInteger, primary_key=True)
    message = Column(UnicodeText(2500))


class Wellcomed(Base):
    __tablename__ = 'wellcomed'

    user_id = Column(BigInteger, ForeignKey(User.id), primary_key=True)
    chat_id = Column(BigInteger, ForeignKey(WelcomeMsg.chat_id), primary_key=True)


class Trigger(Base):
    __tablename__ = 'triggers'

    id = Column(Integer, primary_key=True, autoincrement=True)
    trigger = Column(UnicodeText(2500))
    message = Column(UnicodeText(2500))
    message_type = Column(Integer, default=0)


class Admin(Base):
    __tablename__ = 'admins'

    user_id = Column(BigInteger, ForeignKey(User.id), primary_key=True)
    admin_type = Column(Integer)
    admin_group = Column(BigInteger, primary_key=True, default=0)


class OrderGroup(Base):
    __tablename__ = 'order_groups'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(UnicodeText(250))

    items = relationship('OrderGroupItem', back_populates='group', cascade="save-update, merge, delete, delete-orphan")


class OrderGroupItem(Base):
    __tablename__ = 'order_group_items'

    group_id = Column(Integer, ForeignKey(OrderGroup.id, ondelete='CASCADE'), primary_key=True)
    chat_id = Column(BigInteger, ForeignKey(Group.id), primary_key=True)

    group = relationship('OrderGroup', back_populates='items')
    chat = relationship('Group', back_populates='group_items')


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, autoincrement=True)
    chat_id = Column(BigInteger, ForeignKey(Group.id))
    text = Column(UnicodeText(2500))
    confirmed_msg = Column(BigInteger)
    date = Column(DATETIME(fsp=6), default=datetime.now())

    cleared = relationship('OrderCleared', back_populates='order')
    chat = relationship('Group', back_populates='orders')


class OrderCleared(Base):
    __tablename__ = 'order_cleared'

    order_id = Column(Integer, ForeignKey(Order.id), primary_key=True)
    user_id = Column(BigInteger, ForeignKey(User.id), primary_key=True)
    date = Column(DATETIME(fsp=6), default=datetime.now())

    order = relationship('Order', back_populates='cleared')
    user = relationship('User', back_populates='orders_confirmed')


class Stock(Base):
    __tablename__ = 'stock'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey(User.id))
    stock = Column(UnicodeText(2500))
    date = Column(DATETIME(fsp=6), default=datetime.now())
    stock_type = Column(Integer)

    user = relationship('User', back_populates='stock')


class Character(Base):
    __tablename__ = 'characters'

    user_id = Column(BigInteger, ForeignKey(User.id), primary_key=True)
    date = Column(DATETIME(fsp=6), primary_key=True)
    name = Column(UnicodeText(250))
    prof = Column(UnicodeText(250))
    pet = Column(UnicodeText(250), nullable=True, default=None)
    petLevel = Column(Integer, default=0)
    maxStamina = Column(Integer, default=5)
    level = Column(Integer)
    attack = Column(Integer)
    defence = Column(Integer)
    exp = Column(Integer)
    needExp = Column(Integer, default=0)
    castle = Column(UnicodeText(100))
    gold = Column(Integer, default=0)
    donateGold = Column(Integer, default=0)

    user = relationship('User', back_populates='character')


class BuildReport(Base):
    __tablename__ = 'build_reports'

    user_id = Column(BigInteger, ForeignKey(User.id), primary_key=True)
    date = Column(DATETIME(fsp=6), primary_key=True)
    building = Column(UnicodeText(250))
    progress_percent = Column(Integer)
    report_type = Column(Integer)

    user = relationship('User', back_populates='build_report')


class Report(Base):
    __tablename__ = 'reports'

    user_id = Column(BigInteger, ForeignKey(User.id), primary_key=True)
    date = Column(DATETIME(fsp=6), primary_key=True)
    name = Column(UnicodeText(250))
    level = Column(Integer)
    attack = Column(Integer)
    defence = Column(Integer)
    castle = Column(UnicodeText(100))
    earned_exp = Column(Integer)
    earned_gold = Column(Integer)
    earned_stock = Column(Integer)

    user = relationship('User', back_populates='report')


class Squad(Base):
    __tablename__ = 'squads'

    chat_id = Column(BigInteger, ForeignKey(Group.id), primary_key=True)
    invite_link = Column(UnicodeText(250), default='')
    squad_name = Column(UnicodeText(250))
    thorns_enabled = Column(Boolean, default=True)
    hiring = Column(Boolean, default=False)

    members = relationship('SquadMember', back_populates='squad')
    chat = relationship('Group', back_populates='squad')


class SquadMember(Base):
    __tablename__ = 'squad_members'

    squad_id = Column(BigInteger, ForeignKey(Squad.chat_id))
    user_id = Column(BigInteger, ForeignKey(User.id), primary_key=True)
    approved = Column(Boolean, default=False)

    squad = relationship('Squad', back_populates='members')
    user = relationship('User', back_populates='member')


class Equip(Base):
    __tablename__ = 'equip'

    user_id = Column(BigInteger, ForeignKey(User.id), primary_key=True)
    date = Column(DATETIME(fsp=6), primary_key=True)

    equip = Column(UnicodeText(250))

    user = relationship('User', back_populates='equip')


class LocalTrigger(Base):
    __tablename__ = 'local_triggers'

    id = Column(BigInteger, autoincrement=True, primary_key=True)
    chat_id = Column(BigInteger, ForeignKey(Group.id))
    trigger = Column(UnicodeText(2500))
    message = Column(UnicodeText(2500))
    message_type = Column(Integer, default=0)


class Ban(Base):
    __tablename__ = 'banned_users'

    user_id = Column(BigInteger, ForeignKey(User.id), primary_key=True)
    reason = Column(UnicodeText(2500))
    from_date = Column(DATETIME(fsp=6))
    to_date = Column(DATETIME(fsp=6))


Base.metadata.create_all(ENGINE)
