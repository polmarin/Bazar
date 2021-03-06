import requests
import json
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from bs4 import BeautifulSoup
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import COMMASPACE, formatdate

from .web_driver_conf import get_web_driver_options, get_chrome_web_driver, set_ignore_certificate_error, set_browser_as_incognito, set_automation_as_head_less, set_ignore_console_messages
from .classes import Product
#from app.models import Product, Price
""" ONLY FOR HEROKU 
GOOGLE_CHROME_PATH = '/app/.apt/usr/bin/google-chrome'
CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'
"""

"""
searches = [
    ("21:9 monitor", "Monitores", 300),
    ("B006CZ0LGA", "", 27),  # Catan
    ("B083ZJQXB2", "", 140)  # GHD Carla
]"""

def convert_price_toNumber(price):
    price = price.split("€")[0]
    price = price.replace(".", "").replace(",", ".")

    return float(price)

def prettify_rating(rating):
    """
        rating is always like: X,Y de Z estrellas (or it can be an empty string)
    """
    if rating != "":
        rating = rating.split(" de ")[0] # X,Y
        rating = float(rating.replace(",", "."))
    else:
        rating = 0
    return rating

def scraper(d, searches):

    print(len(searches))

    URL = "https://www.amazon.es"
    NUMBER_OF_PAGES_TO_SEARCH = 1

    j = 0
    search = True
    products = {}

    while search:
        try:
            search_term = searches[j][0]
        except:
            raise Exception("Couldn't get search_term")

        try:
            MAX_PRICE = searches[j][2]
        except:
            raise Exception("Couldn't get MAX_PRICE for search " + search_term)

        try:
            MIN_PRICE = searches[j][3]
        except:
            raise Exception("Couldn't get MIN_PRICE for search " + search_term)
        
        try:
            BLACK_LIST = searches[j][4].split(",")
        except:
            raise Exception("Couldn't get BLACK_LIST for search " + search_term)

        print("Search: " + search_term)

        products[search_term] = []
        search_terms = search_term.split(" ")

        options = get_web_driver_options()
        # set_automation_as_head_less(options)
        set_ignore_console_messages(options)
        set_browser_as_incognito(options)
        driver = get_chrome_web_driver(options)
        try:
            driver.get(URL)
            element = driver.find_element_by_xpath(
                '//*[@id="twotabsearchtextbox"]')
            element.send_keys(search_term)
            element.send_keys(Keys.ENTER)
        except Exception as e:
            raise Exception("Couldn't search for " + search_term + "\n" + str(e))

        """ Get departments so the user can choose """
        try:
            category = searches[j][1]
        except:
            raise Exception("Couldn't get category")
        time.sleep(1)

        if category != "":
            try:
                expand = driver.find_element_by_xpath("//div[@id='departments']/ul/li/span/div/a[@class='a-expander-header a-declarative a-expander-extend-header s-expander-text']")
                expand.click()
            except:
                print("Couldn't expand categories menu")
            time.sleep(1)
            categories = driver.find_elements_by_xpath(("//div[@id='departments']/ul/li"))
            categories = [cat.text for cat in categories]
            if category in categories:
                categoryElement = driver.find_element_by_xpath(
                    "//div[@id='departments']/ul/li/span/a/span[text() = '" + category + "']")
                categoryElement.click()
            else:
                print("Couldn't click on category " + category + " for search " + search_term)
                j += 1
                if j >= len(searches):
                    search = False
                continue

        url = driver.current_url
        driver.get(url)
        results = driver.find_elements_by_xpath(
            "//*[@class='s-main-slot s-result-list s-search-results sg-row']/div")
        content = driver.page_source
        soup = BeautifulSoup(content, 'html.parser')

        for i in range(1, len(results)):
            time.sleep(1)
            if category == "":
                prod = soup.find('div', {"data-asin": search_term})
                asin = search_term
            else:
                prod = soup.find('div', {"data-index": str(i)})
                asin = prod.get('data-asin')
            h2 = prod.find('h2')
            should_add = True
            price = prod.find('span', {'class': 'a-price'})
            prev_price = prod.find('span', {'class': 'a-price a-text-price'})
            try:
                rating = prod.find('div', {'class' : 'a-section a-spacing-none a-spacing-top-micro'}).find('div', {'class' : 'a-row a-size-small'}).find('span').get('aria-label')
            except:
                rating = ""
            
            rating = prettify_rating(rating)

            try:
                if prev_price is None:
                    prev_price = price

                name = h2.get_text().strip()
                price = price.get_text()
                prev_price = prev_price.get_text()
                link = 'https://www.amazon.es' + h2.find('a').get("href")

                product = Product(
                    str(asin), 
                    name, 
                    convert_price_toNumber(price), 
                    convert_price_toNumber(prev_price), 
                    link,
                    rating
                )

                if searches[j][0] != asin:  # If the search term isn't the ASIN
                    for word in search_terms:
                        if word.lower() not in name.lower():
                            should_add = False
                    for black_term in BLACK_LIST:
                        if black_term.lower() in name.lower():
                            should_add = False

                # if product.price > MAX_PRICE:
                #    should_add = False

            except Exception as e:
                print(e)
                should_add = False

            if should_add:
                # print(product)
                products[search_term].append(product)
            
            if asin == search_term:
                break
        driver.close()
        products[search_term].append((MAX_PRICE, MIN_PRICE))
        j += 1
        print(j)

        if j >= len(searches):
            print("Stopping search")
            search = False

    return products

def send_multiple_products_mail(interesting, mail = "12polmarin12@gmail.com"):
    # MAIL CONFIG
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()

    server.login('12polmarin12@gmail.com', 'rkknrblesbgxulky')

    me = '12polmarin12@gmail.com'
    you = mail

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Today's most interesting products"
    msg['From'] = me
    msg['To'] = you

    html = f"""
    <html>
        <head>
            <link href="https://fonts.googleapis.com/css?family=Cardo:400,700|Oswald" rel="stylesheet">
        </head>
        <body style="background-color: #101820FF;padding: 20px 10px; text-align:center">
            <div style="max-width:800px; margin:0 auto; text-align:center; font;color: #FEE715FF">
                <h1 style="font-family:'Oswald', sans-serif;text-transform:uppercase;color: #FEE715FF;text-align:center">Today's <i>juiciest</i></h1>"""

    for search in interesting:
        html += f"""
                <br>
                <h2 style="font-family:'Oswald', sans-serif;text-transform:uppercase;color: #FEE715FF">{search}</h2>
        """
        for n in interesting[search]:
            html += f"""
                <h3 style="font-family:'Oswald', sans-serif;text-transform:uppercase;color: #FEE715FF;margin-bottom:10px">{n}</h3>
                <table style="font-family:'Oswald', sans-serif; color: #FEE715FF;">
                    <tr style="font-family:'Oswald', sans-serif; color: #FEE715FF;text-align: center">
                        <th>Name</th>
                        <th>Rating</th>
                        <th>Original Price</th>
                        <th>Actual Price</th>
                    </tr>
                    
            """
            for product in interesting[search][n]:
                html += f"""
                    <tr style="font-family:'Oswald', sans-serif; color: #FEE715FF;">
                        <td><a href="{product.link}">{product.name}</a></td>
                        <td>{product.rating}</td>
                        <td>{product.prev_price}€</td>
                        <td>{product.last_price}€</td>
                    </tr>
                """
            html += """
                </table>
            """
    html += """
            </div>
        </body>
    </html>
    """
    wholemsg = MIMEText(html, 'html')
    msg.attach(wholemsg)
    server.sendmail(me, you, msg.as_string())
    server.quit()
    print("Sent")

def send_no_products_mail(mail = "12polmarin12@gmail.com"):
    # MAIL CONFIG
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()

    server.login('12polmarin12@gmail.com', 'rkknrblesbgxulky')

    me = '12polmarin12@gmail.com'
    you = mail

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "NO TENIM RES BO"
    msg['From'] = me
    msg['To'] = you

    html = """
        <html>
            <head>
                <link href="https://fonts.googleapis.com/css?family=Cardo:400,700|Oswald" rel="stylesheet">
            </head>
            <body style="background-color: #101820FF;padding: 20px 10px; text-align:center">
                <div style="max-width:800px; margin:0 auto; text-align:center; font;color: #FEE715FF">
                    <h1 style="font-family:'Oswald', sans-serif;text-transform:uppercase;color: #FEE715FF;text-align:center">No hem trobat cap producte nou ni ningun que hagi baixat de preu</h1>
                    <p style="font-family : 'Cardo', serif;color: #FEE715FF;text-align:center">Seguirem buscant!</p>
                </div>
            </body>
        </html>
    """

    wholemsg = MIMEText(html, 'html')
    msg.attach(wholemsg)
    server.sendmail(me, you, msg.as_string())
    server.quit()
    print("Sent")

def send_last_hour_mail(interesting, mail="12polmarin12@gmail.com"):
    # MAIL CONFIG
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()

    server.login('12polmarin12@gmail.com', 'rkknrblesbgxulky')

    me = '12polmarin12@gmail.com'
    you = mail

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Price Drop"
    msg['From'] = me
    msg['To'] = you

    html = f"""
    <html>
        <head>
            <link href="https://fonts.googleapis.com/css?family=Cardo:400,700|Oswald" rel="stylesheet">
        </head>
        <body style="background-color: #101820FF;padding: 20px 10px; text-align:center">
            <div style="max-width:800px; margin:0 auto; text-align:center; font;color: #FEE715FF">
                <h1 style="font-family:'Oswald', sans-serif;text-transform:uppercase;color: #FEE715FF;text-align:center">These prices changed within an hour</h1>"""

    for search in interesting:
        html += f"""
            <br>
            <h2 style="font-family:'Oswald', sans-serif;text-transform:uppercase;color: #FEE715FF">{search}</h2>
            <table style="font-family:'Oswald', sans-serif; color: #FEE715FF;">
                <tr style="font-family:'Oswald', sans-serif; color: #FEE715FF;text-align: center">
                    <th>Name</th>
                    <th>Rating</th>
                    <th>Original Price</th>
                    <th>Last Price</th>
                    <th>Actual Price</th>
                </tr>
                
        """
        for product in interesting[search]:
            html += f"""
                <tr style="font-family:'Oswald', sans-serif; color: #FEE715FF;">
                    <td><a href="{product.link}">{product.name}</a></td>
                    <td>{product[0].rating}</td>
                    <td>{product[0].prev_price}</td>
                    <td>{product[1]}€</td>
                    <td>{product[0].last_price}€</td>
                </tr>
            """
        html += """
            </table>
            """
    html += """
            </div>
        </body>
    </html>
    """
    wholemsg = MIMEText(html, 'html')
    msg.attach(wholemsg)
    server.sendmail(me, you, msg.as_string())
    server.quit()
    print("Sent")

def get_interesting(product_data, price_data, searches):
    send = False
    print(product_data)
    """
    Which are the best products?
        - The cheapest one
        - That below the max amount with the biggest sale
        - That one with the biggest sale overall
        - Products that have lowered their price in the last 24 hours
        - Those with the best ratings (always above 4 out of 5 stars)


        products = {
            search : {
                "Cheapest" : prod,
                "Affordable biggest sales": [prods], # 3? 5?
                "Biggest sale" : prod,
                "Last sales" : [prods], # all
                "Affordable Best Rated" : [prods] # 3? 5?
            }
        }
    """
    products = {}
    for search in searches:
        name = search.name
        max_price = search.max_price
        min_price = search.min_price

        i = 0
        biggest_sales = [] # Order in the end
        last_sales = []
        best_rated = []
        single_product = False
        search_has_products = False
        for product in product_data:
            if product.search == name and product.asin != name:
                send = True
                search_has_products = True
                if i == 0:
                    cheapest = product
                    biggest = product
                else:
                    if product.last_price < cheapest.last_price:
                        cheapest = product 
                    if (product.prev_price - product.last_price) > (biggest.prev_price - biggest.last_price):
                        biggest = product
                if (product.prev_price - product.last_price) > 0 and product.last_price <= max_price:
                    biggest_sales.append(product)
                prices = []
                for price in price_data:
                    if price.asin == product.asin:
                        prices.append(price)

                if len(prices) >= 4:
                    if prices[-4].price > prices[-1].price: # Change to -4
                        last_sales.append(product)
                elif len(prices) >= 1:
                    if prices[0].price > prices[-1].price:
                        last_sales.append(product)

                if product.rating >= 4 and product.last_price <= max_price:
                    best_rated.append(product)
                i += 1

            elif product.asin == name:
                search_has_products = True
                single_product = True
                cheapest = product
                break

        if search_has_products:
            if not single_product:
                biggest_sales.sort(key=lambda x: (x.last_price - x.prev_price), reverse=True)
                #last_sales.sort(key=lambda x: x.last_price, reverse=True)
                best_rated.sort(key=lambda x: x.rating, reverse=True)
                products[name] = {
                    "Cheapest" : [cheapest],
                    "Biggest Affordable Sales" : biggest_sales[:4],
                    "Biggest Sale" : [biggest],
                    "Last Sales" : last_sales,
                    "Affordable Top Rated" : best_rated[:4]
                }
                print("General search")
                print(name)
            else:
                print("Single product")
                print(cheapest.name, cheapest)
                products[cheapest.name] = {
                    "" : [cheapest]
                }
    return products, send