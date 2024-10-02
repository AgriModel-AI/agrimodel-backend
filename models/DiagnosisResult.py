from models import db

class DiagnosisResult(db.Model):
    __tablename__ = 'diagnosis_results'
    resultId = db.Column(db.Integer, primary_key=True)
    dateDiagnosed = db.Column(db.DateTime, nullable=False)
    symptoms = db.Column(db.Text, nullable=False)
    treatmentRecommended = db.Column(db.Text)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)
    diseaseId = db.Column(db.Integer, db.ForeignKey('diseases.diseaseId'), nullable=False)