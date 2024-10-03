from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_migrate import Migrate
from config import Config
from datetime import timedelta
from flask_jwt_extended import JWTManager
from flask_session import Session
import os

db = SQLAlchemy()
migrate = Migrate()
ma = Marshmallow()

def create_app(config_class=Config):
    """ Initialize Flask app and config JWT/Session. """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure JWT settings
    #app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    #app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
    app.config['SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)  # Token expiration time
    app.config['JWT_TOKEN_LOCATION'] = ['cookies']
    app.config['JWT_ACCESS_COOKIE_NAME'] = 'access_token'
    app.config['JWT_COOKIE_CSRF_PROTECT'] = False

    # Configure session settings
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'app_session:'
    app.config['SESSION_COOKIE_NAME'] = 'app_session'

    # Initialize extensions
    jwt = JWTManager(app)
    db.init_app(app)
    migrate.init_app(app, db)
    ma.init_app(app)

    # Initialize session
    Session(app)

    # Initialize routes
    from app.routes import init_routes
    init_routes(app)

    return app
