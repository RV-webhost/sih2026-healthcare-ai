from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt
from app.api import api_bp


def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Initialize shared extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register shared API blueprint
    app.register_blueprint(api_bp)

    return app