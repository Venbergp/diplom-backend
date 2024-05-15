from flask import Flask
from flask_pymongo import PyMongo
from .auth import auth
from .profile import profile
from .routes import main


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile('..\\instance\\config.py')

    # Инициализация MongoDB
    mongo = PyMongo(app)
    app.mongo = mongo

    # Регистрация Blueprints
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(profile, url_prefix='/profile')
    app.register_blueprint(main, url_prefix='/main')

    return app
