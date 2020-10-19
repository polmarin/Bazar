from flask import render_template, flash, redirect, url_for, request
from app import app, db
from .models import Product, Price
from .utils.functions import scraper, send_mail, send_multiple_products_mail, send_no_products_mail, get_best_ones

@app.route("/")
def home():
    return redirect(url_for('index'))

@app.route("/")
@app.route("/index", methods=["GET", "POST"])
def index():
    # When a user clicks submit button it will come here.
    if request.method == 'POST':
        data = request.form  # request the data from the form in index.html file
        search = data["search"]
        asin = data["asin"]
        link = data["link"]
        name = data["name"]
        prev_price = data["prev_price"]
        price = data["price"]

        new_data_price = Price(asin, price)
        db.session.add(new_data_price)

        exists = Product.query.filter_by(asin = asin).first() is not None
        print(exists)
        if not exists:
            new_data_product = Product(search, asin, link, name, prev_price, price)
            db.session.add(new_data_product)
        if exists:
            update_data_product = Product.query.filter_by(asin = asin).first()
            # SHOULD WE UPDATE OTHER VALUES LIKE NAME AND LINK?
            if update_data_product.last_price != price:
                # OJO, nou preu -> Tractarho com vulguis
                update_data_product.last_price = price

        db.session.commit()

        product_data = Product.query.all()
        price_data = Price.query.all()

        products = get_best_ones(product_data)

    if request.method == "GET":
        product_data = Product.query.all()
        price_data = Price.query.all()

    # passes user_data variable into the index.html file.
    return render_template("index.html", product_data=product_data, price_data = price_data)

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

        products = scraper(d)

        interesting = {}
        found_sth = False
        for search in products:
            interesting[search] = []
            for product in products[search][:-1]:
                asin = product.asin
                new_price = Price(asin, product.price)
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