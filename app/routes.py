from flask import render_template, flash, redirect, url_for, request
from app import app, db
from datetime import datetime
import pytz
from .forms import AddSearchForm, LoginForm, RegistrationForm
from .models import Product, Price, Search, User
from .utils.functions import scraper, send_last_hour_mail, send_multiple_products_mail, send_no_products_mail, get_interesting 
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse

@app.route("/index")
def home():
    return redirect(url_for('index'))

@app.route("/index")
@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    print(current_user.id)
    searches = Search.query.filter_by(user_id = current_user.id).all()
    search_terms = [s.name for s in searches] # List of search terms for current user
    print(search_terms)
    product_data = Product.query.filter(Product.search.in_(search_terms)).all()
    prods = [p.asin for p in product_data] # List of ASIN for current user

    #product_data = Product.query.all()
    price_data = Price.query.all()
    last = Price.query.filter(Price.asin.in_(prods)).order_by(Price.date.desc()).first()
    now = datetime.now(pytz.timezone("Europe/Madrid")).replace(tzinfo=None)
    try:
        last_time = int((now - last.date).total_seconds() / 60)
    except: 
        last_time = 0

    interesting, send = get_interesting(product_data, price_data, searches)

    # passes user_data variable into the index.html file.
    #return render_template("index.html", product_data=product_data, last_time = last_time)
    return render_template("index.html", interesting=interesting, last_time = last_time)


@app.route("/all-products")
@login_required
def show_all():
    searches = Search.query.filter_by(user_id = current_user.id).all()
    search_terms = [s.name for s in searches] # List of search terms for current user
    product_data = Product.query.filter(Product.search.in_(search_terms)).all()
    prods = [p.asin for p in product_data] # List of ASIN for current user
    last = Price.query.filter(Price.asin.in_(prods)).order_by(Price.date.desc()).first()
    now = datetime.now(pytz.timezone("Europe/Madrid")).replace(tzinfo=None)

    try:
        last_time = int((now - last.date).total_seconds() / 60)
    except: 
        last_time = 0
    num_prices = len(Price.query.filter(Price.asin.in_(prods)).all())

    return render_template("products.html", product_data=product_data, last_time = last_time, num_prices = num_prices)

@app.route("/manage-search-terms", methods=["GET", "POST"])
@login_required
def manage_search_terms():
    form = AddSearchForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            data = request.form
            name = data["name"]
            category = data["category"] or ''
            max_price = data["max_price"]
            min_price = data["min_price"] or 0
            black_list = data["black_list"] or ''
            
            exists = Search.query.filter_by(name = name, user_id = current_user.id).first() is not None
            if not exists: 
                new_search = Search(name, category, max_price, current_user.id, min_price, black_list)
                db.session.add(new_search)
            elif exists:
                update_data_search = Search.query.filter_by(name = name, user_id = current_user.id).first()
                if update_data_search.max_price != max_price:
                    update_data_search.max_price = max_price
                if update_data_search.min_price != min_price:
                    update_data_search.min_price = min_price
                if update_data_search.black_list != black_list:
                    update_data_search.black_list = black_list

            db.session.commit()
            return redirect(url_for("manage_search_terms"))
        else:
            print("Error validating")

    search_data = Search.query.filter_by(user_id = current_user.id).all()

    return render_template("searches.html", search_data = search_data, form = form)

@app.route("/delete", methods=["GET"])
@login_required
def delete_search_term():
    id = request.args.get('id')
    delete = Search.query.filter_by(id = id).first()
    db.session.delete(delete)
    db.session.commit()

    return redirect(url_for('manage_search_terms'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('index')
        #return redirect(url_for(next_page))
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)