from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager

# One shared database object for the entire project
db = SQLAlchemy()

# One shared migration system
migrate = Migrate()

# One shared JWT manager
jwt = JWTManager()
