from typing import Optional, Dict, Any
from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt
from app.api import api_bp
from app.ai.routes import ai_bp
from app.doctors.routes import doctors_bp


def create_app(config_override: Optional[Dict[str, Any]] = None) -> Flask:
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

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

    # Register shared API blueprint
    app.register_blueprint(api_bp)

    # Register AI blueprint
    app.register_blueprint(ai_bp, url_prefix="/api/ai")

    # Register Member 3 Doctors blueprint
    app.register_blueprint(doctors_bp, url_prefix="/api/v1/doctors")

    return app
