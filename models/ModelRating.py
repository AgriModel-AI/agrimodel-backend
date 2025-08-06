from models import db
from datetime import datetime

class ModelRating(db.Model):
    """Stores user ratings for specific model versions"""
    __tablename__ = 'model_ratings'
    
    ratingId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelId = db.Column(db.String(36), db.ForeignKey('model_versions.modelId'), nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    feedback = db.Column(db.Text, nullable=True)
    diagnosisCorrect = db.Column(db.Boolean, nullable=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "ratingId": self.ratingId,
            "modelId": self.modelId,
            "userId": self.userId,
            "rating": self.rating,
            "feedback": self.feedback,
            "diagnosisCorrect": self.diagnosisCorrect,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None
        }
