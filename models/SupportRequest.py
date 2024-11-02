from datetime import datetime
from models import db
from sqlalchemy import Enum
import enum

# Enum for Support Request Status
class SupportRequestStatus(enum.Enum):
    OPEN = 'OPEN'
    IN_PROGRESS = 'IN_PROGRESS'
    RESOLVED = 'RESOLVED'
    CLOSED = 'CLOSED'

# Enum for Support Request Type (Adjusted for Agrimodal AI)
class SupportRequestType(enum.Enum):
    TECHNICAL = 'Technical Issue'            # For app-related technical issues
    PREDICTION_ISSUE = 'Prediction Issue'    # Issues with crop diagnosis or predictions
    USAGE_HELP = 'Usage Help'                # Users needing help with how to use the app
    FEEDBACK = 'Feedback or Suggestions'     # User feedback or suggestions for improvement
    OTHER = 'Other'                          # Catch-all for other types of requests

# SupportRequest Model
class SupportRequest(db.Model):
    __tablename__ = 'support_requests'
    
    # Fields
    requestId = db.Column(db.BigInteger, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)  # Foreign key to User table
    subject = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=False)
    type = db.Column(Enum(SupportRequestType), nullable=False)  # New field for request type
    status = db.Column(Enum(SupportRequestStatus), default=SupportRequestStatus.OPEN, nullable=False)
    createdAt = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updatedAt = db.Column(db.DateTime, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', backref='support_requests', lazy=True)

    def __repr__(self):
        return f"<SupportRequest {self.requestId} - {self.status} - {self.type}>"
