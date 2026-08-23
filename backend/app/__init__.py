from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt
from app.api import api_bp
from app.appointments import appointments_bp
from app.beds import beds_bp


def create_app(config_object=Config):
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_object)

    # Initialize shared extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register shared API blueprint and module blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(appointments_bp, url_prefix="/api/appointments")
    app.register_blueprint(beds_bp, url_prefix="/api/beds")

    return app