from app.models import Product, Price
from app.utils.functions import scraper, send_mail, send_multiple_products_mail, send_no_products_mail
from app import app, db
from app.utils.classes import Product as Prod

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

    products = scraper(d)

    """ UPDATE DATABASE AND FIND INTERESTING PRODUCTS """
    """
        Which are the interesting products?
        - That below the max amount with the biggest sale
        - That one with the biggest sale overall 
        - Those that changed their price since the last time -> DONE
        - Cheapest -> DONE
    """
    interesting = {}
    found_sth = False
    for search in products:

        interesting[search] = []
        cheapest_product = Prod("", "", "", "", "")
        best_deal_product = Prod("", "", "", "", "")
        best_deal_affordable_product = Prod("", "", "", "", "")

        for product in products[search][:-1]:

            asin = product.asin
            new_price = Price(asin, product.price)
            db.session.add(new_price)
            exists = Product.query.filter_by(asin = asin).first() is not None

            if not exists: 
                # PRODUCT NOT IN DATABASE
                new_product = Product(search, product.asin, product.link, product.name, product.prev_price, product.price)
                db.session.add(new_product)
                if product.price <= products[search][-1]:
                    interesting[search].append({"Product" : product, "Last Price" : product.price})
                    found_sth = True
            else:
                # PRODUCT ALREADY IN DATABASE
                update_data_product = Product.query.filter_by(asin = asin).first()
                update_data_product.link = product.link
                update_data_product.name = product.name
                if update_data_product.last_price != product.price:
                    # OJO, nou preu -> Tractarho com vulguis
                    if update_data_product.last_price > product.price:
                        # Price has changed since the last time -> INTERESTING
                        interesting[search].append({"Product" : product, "Last Price" : update_data_product.last_price})
                        if product.price <= products[search][-1]:
                            # PRICE < 
                        found_sth = True
                    update_data_product.last_price = product.price
            
            if cheapest_product.price == "" or cheapest_product.price > product.price:
                cheapest_product = product
            elif cheapest_product.price == product.price: # Get the one with biggest discount
                if cheapest_product.prev_price < product.prev_price:
                    cheapest_product = product

            
    db.session.commit()

    if found_sth:
        send_multiple_products_mail(interesting)
    else:
        send_no_products_mail()

search()