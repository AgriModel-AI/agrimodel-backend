from models import db


class UserDetails(db.Model):
    __tablename__ = 'user_details'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    userId = db.Column(db.Integer, db.ForeignKey('users.userId'), nullable=False)  # Assuming 'userId' is the primary key in User model
    names = db.Column(db.String(255), nullable=False)
    national_id = db.Column(db.String(50), nullable=False, unique=True)
    city = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    dob = db.Column(db.Date, nullable=True)
    gender = db.Column(db.String(10), nullable=True)
