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
        time.sleep(2)
        print("User: " + str(user.id) + "(" + user.email + ")")
        """ GET STORED PRODUCTS """
        search_data = Search.query.filter_by(user_id = user.id).all()
        search_terms = [s.name for s in search_data] # List of search terms for current user
        product_data = Product.query.filter(Product.search.in_(search_terms)).all()
        d = {}
        if product_data != []:
            for product in product_data:
                prices = Price.query.filter_by(asin = product.asin).all()
                if product.search not in d:
                    d[product.search] = {product.asin : prices[-1].price}
                else:
                    d[product.search][product.asin] = prices[-1].price

        """ GET STORED SEARCH TERMS """
        search_list = []
        for search in search_data:
            search_list.append((search.name, search.category, search.max_price, search.min_price, search.black_list))
        
        """ SCRAPE DATA """
        products = {}
        while products == {} or len(products[list(products.keys())[0]]) <= 1:
            products = scraper(d, search_list)

            #print("ERROR scraping data:")
            #print("User: " + str(user.id) + "(" + user.email + ")")
            #print("Exception: " + str(e))
            #print("--------------------- Restarting ---------------------")
            time.sleep(2)

        print(products)

        print("SCRAPED")

        """ UPDATE DATABASE """
        dropped_prices = {} # { "search" : [( prod , preu), (prod , preu)] }
        for search in products:
            for product in products[search][:-1]:

                asin = product.asin
                print("----------------")
                print(asin)
                if asin != "":
                    exists = Product.query.filter_by(asin = asin).first() is not None

                    if not exists: 
                        # PRODUCT NOT IN DATABASE
                        if product.rating != "":
                            new_product = Product(search, product.asin, product.link, product.name, product.prev_price, product.last_price, product.rating)
                        else:
                            new_product = Product(search, product.asin, product.link, product.name, product.prev_price, product.last_price)
                        print(product)
                        db.session.add(new_product)
                        db.session.commit()
                        print("Added!")
                    else:
                        # PRODUCT ALREADY IN DATABASE
                        update_data_product = Product.query.filter_by(asin = asin).first()
                        update_data_product.link = product.link
                        update_data_product.name = product.name
                        update_data_product.rating = product.rating
                        if product.last_price < update_data_product.last_price:
                            print("Price drop")
                            if search not in dropped_prices:
                                dropped_prices[search] = [(product, update_data_product.last_price)]
                            else:
                                dropped_prices[search].append((product, update_data_product.last_price))
                        update_data_product.last_price = product.last_price

                    new_price = Price(asin, product.last_price, datetime.now(pytz.timezone("Europe/Madrid")).replace(tzinfo=None))
                    db.session.add(new_price)
                    db.session.commit()


        if dropped_prices != {}:
            print(user.email + " should receive a mail with the products that just drpped their price.")
            send_last_hour_mail(dropped_prices, mail = user.email)


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
