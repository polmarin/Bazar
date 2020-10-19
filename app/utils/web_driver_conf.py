from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.keys import Keys

""" ONLY FOR HEROKU """
GOOGLE_CHROME_PATH = '/app/.apt/usr/bin/google-chrome'
CHROMEDRIVER_PATH = '/app/.chromedriver/bin/chromedriver'


def get_chrome_web_driver(options):
    try:
        return webdriver.Chrome(ChromeDriverManager().install(), chrome_options=options)
    except:
        return webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, chrome_options=options)
        #return webdriver.Chrome(executable_path="/Users/polmarin/Documents/Coding/Python/Flask/buyCheap/app/utils/chromedriver", chrome_options=options)


def get_web_driver_options():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.binary_location = GOOGLE_CHROME_PATH
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument("--window-size=1920,1080")
    return chrome_options


def set_ignore_certificate_error(options):
    options.add_argument('--ignore-certificate-errors')


def set_browser_as_incognito(options):
    options.add_argument('--incognito')


def set_automation_as_head_less(options):
    options.add_argument('--headless')


def set_ignore_console_messages(options):
    options.add_argument("--log-level=3")
