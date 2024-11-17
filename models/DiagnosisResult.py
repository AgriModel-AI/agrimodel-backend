from models import db

class DiagnosisResult(db.Model):
    __tablename__ = 'diagnosis_results'
    resultId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    diseaseId = db.Column(db.Integer, db.ForeignKey('diseases.diseaseId'), nullable=True)
    districtId = db.Column(db.Integer, db.ForeignKey('districts.districtId'), nullable=True)  # New field
    date = db.Column(db.DateTime, nullable=False)
    image_path = db.Column(db.Text)
    detected = db.Column(db.Boolean)
    
    # Relationships
    district = db.relationship('District', backref='diagnosis_results')
