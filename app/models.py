from . import db

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(50), nullable=True)
    big_link = db.Column(db.String(255), nullable=True)
    email = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    access_code = db.Column(db.String(50), nullable=True) 
