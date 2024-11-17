from models import db

class District(db.Model):
    __tablename__ = 'districts'
    districtId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    provinceId = db.Column(db.Integer, db.ForeignKey('provinces.provinceId'), nullable=False)
    
    # Relationships
    province = db.relationship('Province', back_populates='districts')
