from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
import pytz
from app import db, login

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return '<User {}>'.format(self.username) 

class Product(db.Model):
    search = db.Column(db.String(100), db.ForeignKey('search.name', ondelete="cascade"), nullable=False)
    asin = db.Column(db.String(30), nullable=False, primary_key = True)
    link = db.Column(db.String(1000), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    prev_price = db.Column(db.Float, nullable=False)
    last_price = db.Column(db.Float, nullable = False)
    rating = db.Column(db.Float, nullable = True)

    # A constructor function where we will pass the name and email of a user and it gets add as a new entry in the table.
    def __init__(self, search, asin, link, name, prev_price, price, rating = 0):
        self.search = search
        self.asin = asin
        self.link = link
        self.name = name
        self.prev_price = prev_price
        self.last_price = price
        self.rating = rating

    def __repr__(self):
        return '<Product {}>'.format(self.asin)

class Price(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asin = db.Column(db.String(30), db.ForeignKey('product.asin', ondelete="cascade"),
        nullable=False)
    price = db.Column(db.Float, nullable = False)
    default = datetime.now(pytz.timezone("Europe/Madrid"))
    date = db.Column(db.DateTime, nullable=False,
        default=default)

    def __init__(self, asin, price, date):
        self.asin = asin
        self.price = price
        self.date = date

class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable = False, unique=True)
    category = db.Column(db.String(100), nullable = False)
    max_price = db.Column(db.Float, nullable = False)
    min_price = db.Column(db.Float, nullable=True, default = 0)
    black_list = db.Column(db.String(500), nullable=True, default = "")
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete="cascade"), default=0)


    def __init__(self, name, cat, max_price, user, min_price, black_list):
        self.name = name
        self.category = cat
        self.max_price = max_price
        self.user_id = user
        self.min_price = min_price
        self.black_list = black_list.split(",")



@login.user_loader
def load_user(id):
    return User.query.get(int(id))