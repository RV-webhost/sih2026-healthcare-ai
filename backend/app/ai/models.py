import uuid
from datetime import datetime
from app.extensions import db

class AIRequest(db.Model):
    __tablename__ = 'ai_requests'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    message = db.Column(db.Text, nullable=False)
    intent = db.Column(db.String(50), nullable=False)
    entities = db.Column(db.JSON, nullable=True)
    confidence = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
