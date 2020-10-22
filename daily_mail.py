from app.models import Product, Price, Search
from app.utils.functions import send_multiple_products_mail, get_interesting
from app import app, db

product_data = Product.query.all()
price_data = Price.query.all()
searches = Search.query.all()
interesting = get_interesting(product_data, price_data, searches)
#print(interesting)
send_multiple_products_mail(interesting)