from marshmallow import Schema, fields
from datetime import datetime

class UserSchema(Schema):
    id = fields.Int()
    fname = fields.Str()
    lname = fields.Str()
    email = fields.Str()
    password = fields.Str()
    phone = fields.Str()
    address = fields.Str()
    role = fields.Str()
    join_date = fields.DateTime()

class ProductSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    category = fields.Str()
    brand = fields.Str()
    base_value = fields.Float()
    current_value = fields.Float()
    discount = fields.Int()
    flavours = fields.List(fields.Str())
    weight = fields.Int()
    update_date = fields.DateTime()
    images = fields.List(fields.Str())
    description = fields.Str()
    benefits = fields.Str()
    how_to_use = fields.Str()
    nutrition_table = fields.Str()
    top_sale = fields.Bool()
    most_sold = fields.Bool()

class OrderSchema(Schema):
    id = fields.Int()
    user_id = fields.Int()
    order_date = fields.DateTime()
    total_value = fields.Float()
    status = fields.Str()
    address = fields.Str()

class OrderItemSchema(Schema):
    id = fields.Int()
    order_id = fields.Int()
    product_id = fields.Int()
    amount = fields.Int()

class ReviewSchema(Schema):
    id = fields.Int()
    user_id = fields.Int()
    product_id = fields.Int()
    rating = fields.Float()
    review = fields.Str()
    update_date = fields.DateTime()
    fname = fields.Str()
    lname = fields.Str()

