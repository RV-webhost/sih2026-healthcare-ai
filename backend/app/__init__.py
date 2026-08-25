from typing import Optional, Dict, Any
from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt
from app.api import api_bp
<<<<<<< HEAD
from app.appointments import appointments_bp
from app.beds import beds_bp


def create_app(config_object=Config):
=======
from app.ai.routes import ai_bp
from app.doctors.routes import doctors_bp
from app.tokens.routes import tokens_bp

def create_app(config_override: Optional[Dict[str, Any]] = None) -> Flask:
>>>>>>> origin/main
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(config_object)

    # Set default SQLAlchemy engine options if not configured
    if "SQLALCHEMY_ENGINE_OPTIONS" not in app.config or not app.config["SQLALCHEMY_ENGINE_OPTIONS"]:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }

    # Allow configuration override (e.g. for testing)
    if config_override:
        app.config.update(config_override)

    # Disable ASCII encoding to display Hindi/Marathi natively
    app.json.ensure_ascii = False

    # Initialize shared extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register shared API blueprint and module blueprints
    app.register_blueprint(api_bp)
    app.register_blueprint(appointments_bp, url_prefix="/api/appointments")
    app.register_blueprint(beds_bp, url_prefix="/api/beds")

    # Register M1 AI blueprint (Updated to v1 prefix)
    app.register_blueprint(ai_bp, url_prefix='/api/v1/ai')

    # Register Member 3 Doctors blueprint
    app.register_blueprint(doctors_bp, url_prefix="/api/v1/doctors")

    # Register token & queue blueprint (prefix is set on tokens_bp)
    app.register_blueprint(tokens_bp)

    return app