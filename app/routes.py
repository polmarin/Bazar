from flask import render_template, flash, redirect, url_for, request
from app import app, db
from datetime import datetime
import pytz
from .forms import AddSearchForm
from .models import Product, Price, Search
from .utils.functions import scraper, send_mail, send_multiple_products_mail, send_no_products_mail, get_best_ones

@app.route("/index")
def home():
    return redirect(url_for('index'))

@app.route("/index")
@app.route("/", methods=["GET", "POST"])
def index():
    product_data = Product.query.all()
    last = Price.query.order_by(Price.date.desc()).first()
    now = datetime.now(pytz.timezone("Europe/Madrid")).replace(tzinfo=None)
    print(now, last.date)
    last_time = int((now - last.date).total_seconds() / 60)

    # passes user_data variable into the index.html file.
    return render_template("index.html", product_data=product_data, last_time = last_time)

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

        products = scraper(d, searches)

        interesting = {}
        found_sth = False
        for search in products:
            interesting[search] = []
            for product in products[search][:-1]:
                asin = product.asin
                new_price = Price(asin, product.price, datetime.now(pytz.timezone("Europe/Madrid")).replace(tzinfo=None))
                db.session.add(new_price)

                exists = Product.query.filter_by(asin = asin).first() is not None
                if not exists:
                    new_product = Product(search, product.asin, product.link, product.name, product.prev_price, product.price)
                    db.session.add(new_product)
                    if product.price <= products[search][-1]:
                        interesting[search].append({"Product" : product, "Last Price" : product.price})
                        found_sth = True
                else:
                    update_data_product = Product.query.filter_by(asin = asin).first()
                    # SHOULD WE UPDATE OTHER VALUES LIKE NAME AND LINK?
                    if update_data_product.last_price != product.price:
                        # OJO, nou preu -> Tractarho com vulguis
                        if update_data_product.last_price > product.price and product.price <= products[search][-1]:
                            interesting[search].append({"Product" : product, "Last Price" : update_data_product.last_price})
                            found_sth = True
                        update_data_product.last_price = product.price
                
        db.session.commit()

        if found_sth:
            send_multiple_products_mail(interesting)
        else:
            send_no_products_mail()

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