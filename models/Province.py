from models import db

class Province(db.Model):
    __tablename__ = 'provinces'
    provinceId = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    districts = db.relationship('District', back_populates='province', lazy=True)
