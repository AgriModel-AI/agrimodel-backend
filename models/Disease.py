from models import db

from datetime import datetime
from sqlalchemy.orm import relationship

class Disease(db.Model):
    __tablename__ = 'diseases'
    diseaseId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    treatment = db.Column(db.Text)
    prevention = db.Column(db.Text)
    images = db.Column(db.Text)  # Can store comma-separated URLs
    relatedDiseases = db.Column(db.Text)  # Can store comma-separated disease IDs
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    diagnosisResults = relationship('DiagnosisResult', backref='disease', lazy=True)
    
    def serialize(self):
        return {
            "diseaseId": self.diseaseId,
            "name": self.name,
            "description": self.description,
            "symptoms": self.symptoms,
            "treatment": self.treatment,
            "prevention": self.prevention,
            "images": self.images.split(",") if self.images else [],
            "relatedDiseases": self.relatedDiseases.split(",") if self.relatedDiseases else [],
            "createdAt": self.createdAt.isoformat(),
        }