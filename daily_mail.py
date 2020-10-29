from app.models import Product, Price, Search, User
from app.utils.functions import send_multiple_products_mail, get_interesting
from app import app, db
import time

for user in User.query.all():
    searches = Search.query.filter_by(user_id = user.id).all()
    search_terms = [s.name for s in searches] # List of search terms for current user
    product_data = Product.query.filter(Product.search.in_(search_terms)).all()
    prods = [p.asin for p in product_data] # List of ASIN for current user
    price_data = Price.query.all()

    interesting = get_interesting(product_data, price_data, searches)
    #print(interesting)
    send_multiple_products_mail(interesting, mail = user.email)
    time.sleep(5)