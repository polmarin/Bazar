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
    dropped_prices = {}
    for search in products:
        for product in products[search][:-1]:

            asin = product.asin
            exists = Product.query.filter_by(asin = asin).first() is not None

            if not exists: 
                # PRODUCT NOT IN DATABASE
                if product.rating != "":
                    new_product = Product(search, product.asin, product.link, product.name, product.prev_price, product.last_price, product.rating)
                else:
                    new_product = Product(search, product.asin, product.link, product.name, product.prev_price, product.last_price)
                db.session.add(new_product)
                db.session.commit()
            else:
                # PRODUCT ALREADY IN DATABASE
                update_data_product = Product.query.filter_by(asin = asin).first()
                update_data_product.link = product.link
                update_data_product.name = product.name
                update_data_product.rating = product.rating
                if product.last_price < update_data_product.last_price:
                    if search not in dropped_prices:
                        dropped_prices[search] = {"Price Drop Since Last Query": [product]}
                    else:
                        dropped_prices[search]["Price Drop Since Last Query"].append(product)
                update_data_product.last_price = product.last_price

            new_price = Price(asin, product.last_price, datetime.now(pytz.timezone("Europe/Madrid")).replace(tzinfo=None))
            db.session.add(new_price)
        db.session.commit()


    if dropped_prices != {}:
        send_multiple_products_mail(dropped_prices, subject="Price Drop", title="These prices changed within an hour")


do = True
while do:
    try:
        search()
        do = False
    except:
        print("PROBLEMS WITH SEARCH, TRYING AGAIN")
        do = True # I don't need this here but it doesn't harm anybody
