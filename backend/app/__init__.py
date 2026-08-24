from flask import Flask

from app.config import Config
from app.extensions import db, migrate, jwt
from app.api import api_bp
from app.ai.routes import ai_bp  # <-- 1. Import your AI blueprint

def create_app():
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # ADD THIS LINE: Disable ASCII encoding to display Hindi/Marathi natively
    app.json.ensure_ascii = False 

    # Initialize shared extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Register shared API blueprint
    app.register_blueprint(api_bp)
    
    # Register AI blueprint
    # Using /api/ai matches your M1 exact API requirements
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    

    return app
