from models import db

from datetime import datetime
from sqlalchemy.orm import relationship

class Disease(db.Model):
    __tablename__ = 'diseases'
    diseaseId = db.Column(db.Integer, primary_key=True)
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