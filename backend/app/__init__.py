from typing import Optional, Dict, Any
import os
from dotenv import load_dotenv
from flask import Flask
from app.extensions import db
from app.doctors.routes import doctors_bp

load_dotenv()


def create_app(config_override: Optional[Dict[str, Any]] = None) -> Flask:
    """Application factory for the Flask backend."""
    app = Flask(__name__)

    database_url = os.getenv("DATABASE_URL", "sqlite:///sih_healthcare.db")
    if database_url == "REPLACE_ME" or not database_url:
        database_url = "sqlite:///sih_healthcare.db"
    elif database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    if config_override:
        app.config.update(config_override)

    # Initialize extensions
    db.init_app(app)


    # Register Blueprints
    app.register_blueprint(doctors_bp)

    return app
