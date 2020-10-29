from app.models import Product, Price, Search, User
from app.utils.functions import scraper, send_last_hour_mail, send_multiple_products_mail, send_no_products_mail, get_interesting
from app import app, db
from datetime import datetime
import time
import pytz
from app.utils.classes import Product as Prod

print("Hi")

def search():
    for user in User.query.all():
        """ GET STORED PRODUCTS """
        search_data = Search.query.filter_by(user_id = user.id).all()
        search_terms = [s.name for s in search_data] # List of search terms for current user
        product_data = Product.query.filter(Product.search.in_(search_terms)).all()
        d = {}
        for product in product_data:
            prices = Price.query.filter_by(asin = product.asin).all()
            if product.search not in d:
                d[product.search] = {product.asin : prices[-1].price}
            else:
                d[product.search][product.asin] = prices[-1].price

        """ GET STORED SEARCH TERMS """
        searches = []
        for search in search_data:
            searches.append((search.name, search.category, search.max_price))
        
        """ SCRAPE DATA """
        products = {}
        while products == {} or len(products[list(products.keys())[0]]) <= 1:
            try:
                products = scraper(d, searches)
            except Exception as e:
                print("ERROR scraping data:")
                print("User: " + str(user.id) + "(" + user.email + ")")
                print("Exception: " + str(e))

        print(products)

        """ UPDATE DATABASE """
        dropped_prices = {} # { "search" : [( prod , preu), (prod , preu)] }
        for search in products:
            for product in products[search][:-1]:

                asin = product.asin
                if asin != "":
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
                                dropped_prices[search] = [(product, update_data_product.last_price)]
                            else:
                                dropped_prices[search].append((product, update_data_product.last_price))
                        update_data_product.last_price = product.last_price

                    new_price = Price(asin, product.last_price, datetime.now(pytz.timezone("Europe/Madrid")).replace(tzinfo=None))
                    db.session.add(new_price)
                    db.session.commit()


        if dropped_prices != {}:
            send_multiple_products_mail(dropped_prices, mail = user.email)


do = True
while do:
    try:
        search()
        do = False
    except Exception as e:
        print("PROBLEMS WITH SEARCH, TRYING AGAIN")
        print(e)
        time.sleep(1)
        do = True # I don't need this here but it doesn't harm anybody
