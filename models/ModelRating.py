from models import db
from datetime import datetime

class ModelRating(db.Model):
    """Stores user ratings for specific model versions"""
    __tablename__ = 'model_ratings'
    
    ratingId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modelId = db.Column(db.String(36), db.ForeignKey('model_versions.modelId'), nullable=False)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    offlineId = db.Column(db.String(36), nullable=True, unique=True)  # For identifying ratings created offline
    rating = db.Column(db.Integer, nullable=False)  # 1-5 stars
    feedback = db.Column(db.Text, nullable=True)
    diagnosisResult = db.Column(db.String(100), nullable=True)  # What disease was diagnosed
    diagnosisCorrect = db.Column(db.Boolean, nullable=True)  # User feedback on correctness
    cropType = db.Column(db.String(50), nullable=True)  # Just the crop name
    deviceInfo = db.Column(db.Text, nullable=True)  # Device information
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            "ratingId": self.ratingId,
            "modelId": self.modelId,
            "userId": self.userId,
            "offlineId": self.offlineId,
            "rating": self.rating,
            "feedback": self.feedback,
            "diagnosisResult": self.diagnosisResult,
            "diagnosisCorrect": self.diagnosisCorrect,
            "cropType": self.cropType,
            "deviceInfo": self.deviceInfo,
            "createdAt": self.createdAt.isoformat() if self.createdAt else None
        }
