import uuid
from models import db
from datetime import datetime
        
class ModelVersion(db.Model):
    """Stores information about each model version"""
    __tablename__ = 'model_versions'
    
    modelId = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    version = db.Column(db.String(20), nullable=False)
    fileSize = db.Column(db.Integer, nullable=False)  # Size in KB
    fileHash = db.Column(db.String(64), nullable=False)  # For integrity verification
    filePath = db.Column(db.String(255), nullable=False)
    
    # Add configuration file information
    configPath = db.Column(db.String(255), nullable=False)
    configHash = db.Column(db.String(64), nullable=False)
    configSize = db.Column(db.Integer, nullable=False)
    
    accuracy = db.Column(db.Float, nullable=True)
    releaseDate = db.Column(db.DateTime, default=datetime.utcnow)
    isActive = db.Column(db.Boolean, default=True)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    ratings = db.relationship('ModelRating', backref='model', lazy=True)
    
    def to_dict(self):
        return {
            "modelId": self.modelId,
            "version": self.version,
            "fileSize": self.fileSize,
            "fileHash": self.fileHash,
            "configSize": self.configSize,
            "configHash": self.configHash,
            "accuracy": self.accuracy,
            "releaseDate": self.releaseDate.isoformat(),
            "isActive": self.isActive
        }
