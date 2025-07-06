from enum import Enum
from sqlalchemy.dialects.postgresql import ENUM  # Use this if you're using PostgreSQL
from sqlalchemy import Enum as SQLAlchemyEnum
from models import db
from datetime import datetime

class ExploreType(Enum):
    UPDATES = "UPDATES"
    ONLINE_SERVICES = "ONLINE-SERVICES"
    DISEASE_LIBRARY = "DISEASE-LIBRARY"

class Explore(db.Model):
    __tablename__ = 'explore'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    type = db.Column(SQLAlchemyEnum(ExploreType), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(255), nullable=False)
    otherImages = db.Column(db.Text)  # Comma-separated URLs
    link = db.Column(db.String(255))  # Required for certain types
    date = db.Column(db.DateTime, default=datetime.utcnow)
    isActive = db.Column(db.Boolean, default=True)
    
    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type.value,
            "title": self.title,
            "content": self.content,
            "image": self.image,
            "otherImages": self.otherImages,
            "link": self.link,
            "date": self.date.isoformat() if self.date else None,
            "isActive": self.isActive
        }