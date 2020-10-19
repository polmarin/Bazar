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

searches = [
    ("21:9 monitor", "Monitores", 300),
    ("B006CZ0LGA", "", 27),  # Catan
    ("B083ZJQXB2", "", 140)  # GHD Carla
]

def convert_price_toNumber(price):
    price = price.split("€")[0]
    price = price.replace(".", "").replace(",", ".")

    return float(price)

def scraper(d):

    URL = "https://www.amazon.es"
    NUMBER_OF_PAGES_TO_SEARCH = 1

    j = 0
    search = True
    products = {}

    while search:
        #chepest_product = Product("", "", "", "", "")
        #best_deal_product = Product("", "", "", "", "")

        if j < len(searches):
            search_term = searches[j][0]
            MAX_PRICE = searches[j][2]
        else:
            QUESTION_PRODUCT = "What are you looking for?\n:"
            search_term = str(input(QUESTION_PRODUCT))
            QUESTION_PRICE = "Which is the highest price you're willing to pay?\n:"
            MAX_PRICE = float(input(QUESTION_PRICE))

        products[search_term] = []
        search_terms = search_term.split(" ")

        options = get_web_driver_options()
        # set_automation_as_head_less(options)
        set_ignore_console_messages(options)
        set_browser_as_incognito(options)
        driver = get_chrome_web_driver(options)

        driver.get(URL)
        element = driver.find_element_by_xpath(
            '//*[@id="twotabsearchtextbox"]')
        element.send_keys(search_term)
        element.send_keys(Keys.ENTER)

        """ Get departments so the user can choose """
        departments = driver.find_elements_by_xpath(
            "//div[@id='departments']/ul/li")
        categories = []
        for cat in departments:
            categories.append(cat.text)

        if j < len(searches):
            category = searches[j][1]
        else:
            MSG = "Which of these categories is your product in? " + \
                str(categories)
            category = str(input(MSG))

        if category != "":
            categoryElement = driver.find_element_by_xpath(
                "//div[@id='departments']/ul/li/span/a/span[contains(text(), '" + category + "')]")
            categoryElement.click()

        url = driver.current_url
        driver.get(url)
        results = driver.find_elements_by_xpath(
            "//*[@class='s-main-slot s-result-list s-search-results sg-row']/div")
        content = driver.page_source
        soup = BeautifulSoup(content, 'html.parser')

        for i in range(1, len(results)):
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
                    link
                )

                if searches[j][0] != asin:  # If the search term isn't the ASIN
                    for word in search_terms:
                        if word.lower() not in name.lower():
                            should_add = False

                # if product.price > MAX_PRICE:
                #    should_add = False

            except Exception as e:
                #print(e)
                should_add = False
 
            if should_add:
                # print(product)
                products[search_term].append(product)
            
            if asin == search_term:
                break
        driver.close()
        products[search_term].append(MAX_PRICE)
        j += 1

        """ FOR HEROKU TO STOP """
        if j == len(searches):
            search = False
        """
        if j >= len(searches):
            cont = input(
                "If you want to search for more products, type 1, else otherwise: ")
            if cont != "1":
                search = False
        """

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
    msg['Subject'] = "TENIM PRODUCTES INTERESSANTS"
    msg['From'] = me
    msg['To'] = you

    html = f"""
    <html>
        <head>
            <link href="https://fonts.googleapis.com/css?family=Cardo:400,700|Oswald" rel="stylesheet">
        </head>
        <body style="background-color: #101820FF;padding: 20px 10px; text-align:center">
            <div style="max-width:800px; margin:0 auto; text-align:center; font;color: #FEE715FF">
                <h1 style="font-family:'Oswald', sans-serif;text-transform:uppercase;color: #FEE715FF;text-align:center">Hem trobat diferents productes interessants</h1>"""

    for search in interesting:
        html += f"""
            <br>
            <h2>{search}</h2>
            <table>
                <thead>
                    <th>Name</th>
                    <th>Original Price</th>
                    <th>Last Price</th>
                    <th>Actual Price</th>
                </thead>
                <tbody>
        """
        for product in interesting[search]:
            html += f"""
                <td>{product["Product"].name}</td>
                <td>{product["Product"].prev_price}</td>
                <td>{product["Last Price"].name}</td>
                <td>{product["Product"].price}</td>
            """
        html += """
                </tbody>
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

def send_mail(link, mail="12polmarin12@gmail.com", d_info = {}):
    # MAIL CONFIG
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.ehlo()
    server.starttls()
    server.ehlo()

    server.login('12polmarin12@gmail.com', 'rkknrblesbgxulky')

    me = '12polmarin12@gmail.com'
    you = mail

    msg = MIMEMultipart('alternative')
    msg['Subject'] = "EL TEU PRODUCTE HA BAIXAT DE PREU"
    msg['From'] = me
    msg['To'] = you

    html = f"""
    <html>
        <head>
            <link href="https://fonts.googleapis.com/css?family=Cardo:400,700|Oswald" rel="stylesheet">
        </head>
        <body style="background-color: #101820FF;padding: 20px 10px; text-align:center">
            <div style="max-width:800px; margin:0 auto; text-align:center; font;color: #FEE715FF">
                <h1 style="font-family:'Oswald', sans-serif;text-transform:uppercase;color: #FEE715FF;text-align:center">El producto que buscas ha bajado de precio</h1>
                <p style="font-family : 'Cardo', serif;color: #FEE715FF;text-align:center">
                    Hello darling. <br>
                    Si has rebut això és perquè el producte que em vas demanar que vigilés ha baixat de preu per sota del limit que t'havies posat.
                </p>
                <a href='{link}' style="color:#101820FF; text-decoration: none">
                    <h3 style="display: inline-block; font-family:'Oswald', sans-serif;text-align:center;background-color: #FEE715FF; border: 2px solid; box-shadow: 5px 10px white; padding:25px 10px">
                        Fes click aquí i compra
                    </h3>
                </a>
            </div>
        </body>
    </html>
    """

    wholemsg = MIMEText(html, 'html')
    msg.attach(wholemsg)
    server.sendmail(me, you, msg.as_string())
    server.quit()
    print("Sent")

def get_best_ones(product_data):
    """
    Which are the best products?
        - That below the max amount with the biggest sale
        - That one with the biggest sale overall
        - 
    """
    products = {} # dict {cat, [products]}
    for product in product_data:
        if product.search not in products:
            products[product.search] = product
        else:
            pass
            #if products[product.search].last_price < 