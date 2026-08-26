from typing import Optional, Dict, Any
from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt
from app.api import api_bp
from app.orchestrator.routes import orchestrator_bp
from app.auth.routes import auth_bp

# Member 2 Blueprints
from app.appointments import appointments_bp
from app.beds import beds_bp

# Other Members Blueprints
from app.ai.routes import ai_bp
from app.doctors.routes import doctors_bp
from app.tokens.routes import tokens_bp

def create_app(config_override=None) -> Flask:

    app = Flask(__name__)



    app.config.from_object(Config)

    # Allow configuration override (e.g., for testing)
    if config_override:
        if isinstance(config_override, dict):
            app.config.from_mapping(config_override)
        else:
            app.config.from_object(config_override)

    # Set default SQLAlchemy engine options if not configured
    if "SQLALCHEMY_ENGINE_OPTIONS" not in app.config or not app.config["SQLALCHEMY_ENGINE_OPTIONS"]:
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "pool_pre_ping": True,
            "pool_recycle": 300,
        }

    # Disable ASCII encoding to display Hindi/Marathi natively
    app.json.ensure_ascii = False

    # Initialize shared extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register shared API blueprint
    app.register_blueprint(api_bp)
    app.register_blueprint(orchestrator_bp, url_prefix="/api/v1")
    
    # Register Member 2 module blueprints (Ensuring v1 prefix convention)
    app.register_blueprint(appointments_bp, url_prefix="/api/v1/appointments")
    app.register_blueprint(beds_bp, url_prefix="/api/v1/beds")

    # Register other module blueprints
    app.register_blueprint(ai_bp, url_prefix='/api/v1/ai')
    app.register_blueprint(doctors_bp, url_prefix="/api/v1/doctors")
    app.register_blueprint(tokens_bp)

    app.register_blueprint(auth_bp, url_prefix='/api/v1')

    return app
