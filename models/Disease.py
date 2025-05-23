from models import db

from datetime import datetime
from sqlalchemy.orm import relationship

class Disease(db.Model):
    __tablename__ = 'diseases'
    diseaseId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    label = db.Column(db.Text)
    symptoms = db.Column(db.Text)
    treatment = db.Column(db.Text)
    prevention = db.Column(db.Text)
    images = db.Column(db.Text)  # Can store comma-separated URLs
    relatedDiseases = db.Column(db.Text)  # Can store comma-separated disease IDs
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    cropId = db.Column(db.Integer, db.ForeignKey('crops.cropId'), nullable=False)

    # Relationships
    diagnosisResults = relationship('DiagnosisResult', backref='disease', lazy=True)
    
    # Relationship
    cropRel = relationship('Crop', backref='disease', uselist=False)
    
    def serialize(self):
        return {
            "diseaseId": self.diseaseId,
            "name": self.name,
            "description": self.description,
            "label": self.label,
            "symptoms": self.symptoms,
            "treatment": self.treatment,
            "prevention": self.prevention,
            "images": self.images.split(",") if self.images else [],
            "relatedDiseases": self.relatedDiseases.split(",") if self.relatedDiseases else [],
            "cropId": self.cropId,
            "cropName": self.cropRel.name,
            "createdAt": self.createdAt.isoformat(),
        }