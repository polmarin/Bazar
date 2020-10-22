from app.models import Product, Price, Search
from app.utils.functions import scraper, send_mail, send_multiple_products_mail, send_no_products_mail, get_interesting
from app import app, db
from datetime import datetime
import pytz
from app.utils.classes import Product as Prod

print("Hi")

def search():
    """ GET STORED PRODUCTS """
    product_data = Product.query.all()
    d = {}
    for product in product_data:
        prices = Price.query.filter_by(asin = product.asin).all()
        if product.search not in d:
            d[product.search] = {product.asin : prices[-1].price}
        else:
            d[product.search][product.asin] = prices[-1].price

    """ GET STORED SEARCH TERMS """
    search_data = Search.query.all()
    searches = []
    for search in search_data:
        searches.append((search.name, search.category, search.max_price))
    
    """ SCRAPE DATA """
    products = {}
    while products == {}:
        try:
            products = scraper(d, searches)
        except:
            print("Error, trying to get products again")

    """ UPDATE DATABASE """
    for search in products:
        for product in products[search][:-1]:

            asin = product.asin
            exists = Product.query.filter_by(asin = asin).first() is not None

            if not exists: 
                # PRODUCT NOT IN DATABASE
                if product.rating != "":
                    new_product = Product(search, product.asin, product.link, product.name, product.prev_price, product.price, product.rating)
                else:
                    new_product = Product(search, product.asin, product.link, product.name, product.prev_price, product.price)
                db.session.add(new_product)
                db.session.commit()
            else:
                # PRODUCT ALREADY IN DATABASE
                update_data_product = Product.query.filter_by(asin = asin).first()
                update_data_product.link = product.link
                update_data_product.name = product.name
                update_data_product.rating = product.rating
                update_data_product.last_price = product.price
            

            new_price = Price(asin, product.price, datetime.now(pytz.timezone("Europe/Madrid")).replace(tzinfo=None))
            db.session.add(new_price)
        db.session.commit()


    product_data = Product.query.all()
    price_data = Price.query.all()
    searches = Search.query.all()
    interesting = get_interesting(product_data, price_data, searches)
    #print(interesting)
    #send_multiple_products_mail(interesting)

search()