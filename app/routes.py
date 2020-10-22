from flask import render_template, flash, redirect, url_for, request
from app import app, db
from datetime import datetime
import pytz
from .forms import AddSearchForm
from .models import Product, Price, Search
from .utils.functions import scraper, send_mail, send_multiple_products_mail, send_no_products_mail, get_interesting 

@app.route("/index")
def home():
    return redirect(url_for('index'))

@app.route("/index")
@app.route("/", methods=["GET", "POST"])
def index():
    product_data = Product.query.all()
    price_data = Price.query.all()
    searches = Search.query.all()
    last = Price.query.order_by(Price.date.desc()).first()
    now = datetime.now(pytz.timezone("Europe/Madrid")).replace(tzinfo=None)
    last_time = int((now - last.date).total_seconds() / 60)

    interesting = get_interesting(product_data, price_data, searches)

    # passes user_data variable into the index.html file.
    #return render_template("index.html", product_data=product_data, last_time = last_time)
    return render_template("index.html", interesting=interesting, last_time = last_time)


@app.route("/all-products")
def show_all():
    product_data = Product.query.all()
    last = Price.query.order_by(Price.date.desc()).first()
    now = datetime.now(pytz.timezone("Europe/Madrid")).replace(tzinfo=None)
    last_time = int((now - last.date).total_seconds() / 60)
    num_prices = len(Price.query.all())

    return render_template("products.html", product_data=product_data, last_time = last_time, num_prices = num_prices)

@app.route("/search", methods=["GET", "POST"])
def search():
    if request.method == 'GET':
        product_data = Product.query.all()
        d = {}
        for product in product_data:
            prices = Price.query.filter_by(asin = product.asin).all()
            if product.search not in d:
                d[product.search] = {product.asin : prices[-1].price}
            else:
                d[product.search][product.asin] = prices[-1].price

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
        send_multiple_products_mail(interesting)

    return redirect(url_for('index'))


@app.route("/manage-search-terms", methods=["GET", "POST"])
def manage_search_terms():
    form = AddSearchForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            data = request.form
            name = data["name"]
            category = data["category"]
            max_price = data["max_price"]
            
            exists = Search.query.filter_by(name = name).first() is not None
            if not exists: 
                new_search = Search(name, category, max_price)
                db.session.add(new_search)
            elif exists:
                update_data_search = Search.query.filter_by(name = name).first()
                if update_data_search.max_price != max_price:
                    update_data_search.max_price = max_price

            db.session.commit()
            return redirect(url_for("manage_search_terms"))

    search_data = Search.query.all()

    return render_template("searches.html", search_data = search_data, form = form)

@app.route("/delete", methods=["GET"])
def delete_search_term():
    id = request.args.get('id')
    delete = Search.query.filter_by(id = id).first()
    db.session.delete(delete)
    db.session.commit()

    return redirect(url_for('manage_search_terms'))