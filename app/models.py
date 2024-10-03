from app import db
from datetime import datetime
from sqlalchemy.dialects.postgresql import ARRAY
import json

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(100), nullable=False)
    lname = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(100), default="user")
    join_date = db.Column(db.DateTime, default=datetime.now)

    orders = db.relationship('Orders', backref='user', lazy=True)
    reviews = db.relationship('Reviews', backref='user', lazy=True)

## Postgre model
# class Products(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String(100), nullable=False)
#     category = db.Column(db.String(100), nullable=False)
#     brand = db.Column(db.String(100), nullable=False)
#     base_value = db.Column(db.Float, nullable=False)
#     current_value = db.Column(db.Float, nullable=False)
#     discount = db.Column(db.Integer, default=0)
#     flavours = db.Column(ARRAY(db.String(100)), nullable=False)
#     weight = db.Column(db.String(100), nullable=False)
#     update_date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
#     images = db.Column(ARRAY(db.String(255)), nullable=True)
#     description = db.Column(db.Text, nullable=True)
#     benefits = db.Column(db.Text, nullable=True)
#     how_to_use = db.Column(db.Text, nullable=True)
#     top_sale = db.Column(db.Boolean, default=False)
#     most_sold = db.Column(db.Boolean, default=False)
#
#     order_items = db.relationship('OrdersItem', backref='product', lazy=True)
#     reviews = db.relationship('Reviews', backref='product', lazy=True)

# SQLite Model
class Products(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    brand = db.Column(db.String(100), nullable=False)
    base_value = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float, nullable=False)
    discount = db.Column(db.Integer, default=0)
    weight = db.Column(db.String(100), nullable=False)
    update_date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    description = db.Column(db.Text, nullable=True)
    benefits = db.Column(db.Text, nullable=True)
    how_to_use = db.Column(db.Text, nullable=True)
    top_sale = db.Column(db.Boolean, default=False)
    most_sold = db.Column(db.Boolean, default=False)

    # Use String to store JSON for flavours and images
    _flavours = db.Column('flavours', db.Text, nullable=False)  # JSON string
    _images = db.Column('images', db.Text, nullable=True)  # JSON string

    order_items = db.relationship('OrdersItem', backref='product', lazy=True)
    reviews = db.relationship('Reviews', backref='product', lazy=True)

    @property
    def flavours(self):
        # Deserialize JSON string back to list
        return json.loads(self._flavours) if self._flavours else []

    @flavours.setter
    def flavours(self, value):
        # Serialize list to JSON string
        self._flavours = json.dumps(value)

    @property
    def images(self):
        # Deserialize JSON string back to list
        return json.loads(self._images) if self._images else []

    @images.setter
    def images(self, value):
        # Serialize list to JSON string
        self._images = json.dumps(value)

class Orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    order_date = db.Column(db.DateTime, default=datetime.now)
    total_value = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(255), nullable=False)

    order_items = db.relationship('OrdersItem', backref='order', lazy=True)

class OrdersItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    flavour = db.Column(db.String(100))

class Reviews(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    rating = db.Column(db.Float(1), nullable=False)
    review = db.Column(db.Text, nullable=False)
    update_date = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
