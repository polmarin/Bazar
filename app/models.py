from datetime import datetime
from app import db

class Product(db.Model):
    search = db.Column(db.String(100), db.ForeignKey('search.name'), nullable=False)
    asin = db.Column(db.String(30), nullable=False, primary_key = True)
    link = db.Column(db.String(500), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    prev_price = db.Column(db.Float, nullable=False)
    last_price = db.Column(db.Float, nullable = False)

    # A constructor function where we will pass the name and email of a user and it gets add as a new entry in the table.
    def __init__(self, search, asin, link, name, prev_price, price):
        self.search = search
        self.asin = asin
        self.link = link
        self.name = name
        self.prev_price = prev_price
        self.last_price = price

    def __repr__(self):
        return '<Product {}>'.format(self.asin)

class Price(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    asin = db.Column(db.String(30), db.ForeignKey('product.asin'),
        nullable=False)
    price = db.Column(db.Float, nullable = False)
    date = db.Column(db.DateTime, nullable=False,
        default=datetime.now)

    def __init__(self, asin, price):
        self.asin = asin
        self.price = price

class Search(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable = False)
    category = db.Column(db.String(100), nullable = False)
    max_price = db.Column(db.Float, nullable = False)

    def __init__(self, name, cat, max_price):
        self.name = name
        self.category = cat
        self.max_price = max_price