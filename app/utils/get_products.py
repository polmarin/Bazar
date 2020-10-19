import json
from functions import scraper, send_mail, get_current_data
from web_driver_conf import get_web_driver_options
from web_driver_conf import get_chrome_web_driver
from web_driver_conf import set_ignore_certificate_error
from selenium.webdriver.common.keys import Keys
import matplotlib.pyplot as plt
import time
from app import app, db

from .models import Product, Price

def main():
    d = get_current_data()
    products = scraper(d)

    for search in products:
        for product in products[search][:-1]:
            asin = product.asin
            exists = Product.query.filter_by(asin = asin).first() is not None
            if not exists:
                new_product = Product(search, product.asin, product.link, product.name, product.prev_price, product.price)
                db.session.add(new_product)
            else:
                update_data_product = Product.query.filter_by(asin = asin).first()
                # SHOULD WE UPDATE OTHER VALUES LIKE NAME AND LINK?
                if update_data_product.last_price != product.price:
                    # OJO, nou preu -> Tractarho com vulguis
                    update_data_product.last_price = product.price
            new_price = Price(asin, product.price)
            db.session.add(new_price)
    db.session.commit()

main()