from models import db

class UserDetails(db.Model):
    __tablename__ = 'user_details'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)  # Assuming 'userId' is the primary key in User model
    names = db.Column(db.String(255), nullable=False)
    national_id = db.Column(db.String(50), nullable=True, unique=True)
    districtId = db.Column(db.Integer, db.ForeignKey('districts.districtId'), nullable=True)  # Replacing city
    address = db.Column(db.String(255), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)

    # Relationships
    district = db.relationship('District', backref='user_details')  # Establishing relationship with District model
