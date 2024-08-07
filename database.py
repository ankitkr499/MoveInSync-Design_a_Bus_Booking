from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.ext.hybrid import hybrid_property
import datetime

db = SQLAlchemy()

class Bus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    bus_name = db.Column(db.String(80), nullable=False)
    total_seats = db.Column(db.Integer, nullable=False)
    current_occupancy = db.Column(db.Integer, default=0)
    operation_days = db.Column(db.String(200), nullable=False)
    source = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    distance = db.Column(db.Integer, nullable=False)
    eta = db.Column(db.String(50), nullable=False)
    seat_plan = db.relationship('Seat', backref='bus', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    booked_seats = db.relationship('Seat', backref='user', lazy=True)

class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)

class Seat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.Integer, nullable=False)
    is_booked = db.Column(db.Boolean, default=False)
    bus_id = db.Column(db.Integer, db.ForeignKey('bus.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)

@hybrid_property
def occupancy_percentage(self):
    return (self.current_occupancy / self.total_seats) * 100





