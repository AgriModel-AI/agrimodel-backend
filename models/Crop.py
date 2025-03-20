from models import db

from datetime import datetime
from sqlalchemy.orm import relationship

class Crop(db.Model):
    __tablename__ = 'crops'
    cropId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    growingConditions = db.Column(db.Text)
    harvestTime = db.Column(db.String(120))
    images = db.Column(db.Text)  # Can store comma-separated URLs
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship - one crop can have many diseases
    diseases = relationship('Disease', backref='crop', lazy=True)
    
    def serialize(self):
        return {
            "cropId": self.cropId,
            "name": self.name,
            "description": self.description,
            "growingConditions": self.growingConditions,
            "harvestTime": self.harvestTime,
            "images": self.images.split(",") if self.images else [],
            "createdAt": self.createdAt.isoformat(),
        }