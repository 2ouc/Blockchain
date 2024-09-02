from flask_login import UserMixin
from __init__ import db

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True) # primary keys are required by SQLAlchemy
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(1000))
    phonenumber = db.Column(db.String(1000))
    dateofbirth = db.Column(db.String(1000))
    IBAN = db.Column(db.String(1000))
    amount = db.Column(db.Integer)