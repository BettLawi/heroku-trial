from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_serializer import SerializerMixin
from datetime import datetime
import pytz

db = SQLAlchemy()

eat_timezone = pytz.timezone('Africa/Nairobi')

class Transaction(db.Model, SerializerMixin):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    product_name = db.Column(db.String, nullable=False)
    product_quantity = db.Column(db.Integer, nullable=False)
    product_price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(tz=eat_timezone))

class Product(db.Model, SerializerMixin):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, nullable=False)
    quantity = db.Column(db.Integer,nullable=False)
    price = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now(tz=eat_timezone))