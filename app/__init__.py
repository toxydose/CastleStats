from flask import Flask
from werkzeug.routing import IntegerConverter as BaseIntegerConverter

app = Flask(__name__)


class IntegerConverter(BaseIntegerConverter):
    regex = r'-?\d+'


app.url_map.converters['int'] = IntegerConverter

from app import views
