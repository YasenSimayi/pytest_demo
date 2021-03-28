from __future__ import division

import sys
import os
import traceback
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.common.alert import Alert

#import logging
#from selenium.webdriver.remote.remote_connection import LOGGER

import lxml.html # for table parsing - much quicker than selenium (x20)
import lxml.etree

import pprint

HOME_URL = 'http://www.imdb.com/' # initial page to start our web scrape journey :)

QUERY = "startrek discovery"

HEADLESS = False # When using a SAML based login, you must use Xvfb or a GUI

# the size of the desktop /virtual window we want to use
# This is very IMPORTANT or you will get Element not visible errors
#   selenium.common.exceptions.ElementNotVisibleException: Message: element not visible
my_window = {
    'width': 1920,
    'height': 1024
}

# timeouts
PAGELOAD_TIMEOUT = 30

# save output to where ?
SOURCEOUTFILE = "./err_source.html"
BROWSER_LOG = "./browser.log"
CHROME_DATA = "./chrome-data/"

#webdriver
driver = None

# where is the binary browser - store locally so we can update it manually v2.33 inuse
chrome_driver = './chromedriver'

# dict of timing stats
timing_stats = {} # dict of lists

###################################################################################
def show_timing_stats():
    """ Print out the timing stats """
    print "*** STATS ***"
    print "\t", "function", "min", "avg", "max", "total"

    for ts in sorted(timing_stats):
        lst = timing_stats[ts]
        max_value = round(max(lst), 2)
        min_value = round(min(lst), 2)
        avg_value = round(sum(lst) / len(lst), 2)
        tot_value = round(sum(lst), 2)
        print "\t", ts, min_value, avg_value, max_value, tot_value

def timing(f):
    """ decorator to time function calls """
    def wrap(*args):
        """ wrapper """
        global timing_stats
        time1 = time.time()
        ret = f(*args)
        time2 = time.time()

        diff = (time2-time1)*1000.0
        func = f.func_name

        if f.func_name not in timing_stats:
            timing_stats[func] = []

        timing_stats[func].append(diff)

        print '%s function took %0.3f ms' % (func, diff)
        return ret
    return wrap

#@timing
def webdriver_setup():
    """ Set up the webdriver """
    global driver

    options = webdriver.ChromeOptions()
    if HEADLESS:
        options.add_argument('headless') # this doesnt work as SAML sends a blank page
    options.add_argument('start-maximized')
    options.add_argument('window-size=' + str(my_window['width']) + 'x' + str(my_window['height'])) # or the login a href is not found and throws error
    options.add_argument("user-data-dir="+CHROME_DATA)
#    options.add_argument('disable-gpu')
#    options.add_argument('disable-infobars')
#    options.add_argument('disable-extensions')
#    options.add_argument("user-agent="+user_agent) # hide headless browser

    # disable images = 2 - quicker load # but breaks image buttons (selenium cant see it)
    # if you mess with this, it will save to disk, so you need to overwrite with = 1 again to get images back
    prefs = {"profile.managed_default_content_settings.images":1}
    options.add_experimental_option("prefs", prefs)

    #
    # set up debug logging if required
    #
    #LOGGER.setLevel(logging.DEBUG)
    #logging.basicConfig(level=logging.DEBUG)
    #logger = logging.getLogger(__name__)

    # initialize the chrome web driver
    driver = webdriver.Chrome(
        executable_path=chrome_driver,  # important to point to the driver exe
        chrome_options=options,         # all the options we adjusted above
        service_args=["--verbose", "--log-path="+BROWSER_LOG]
    )

    driver.implicitly_wait(30) # max 30sec wait per action - SAML login takes ~10-26secs

    # this seems to be be the only way to set the XVFB + chrome window size - on a desktop this is not needed
    driver.set_window_size(my_window['width'], my_window['height'])  # this is IMPORTANT must set windows size this way

    #driver.maximize_window() # errors with window set to 'normal'
    sz = driver.get_window_size()
    print "** Window Size", sz # our check
    if (sz['width'] < my_window['width'] - 1) or (sz['height'] < my_window['height'] - 1): # why is the reported view 1 pixel smaller?
        print "Error: Window size is not optimal",sz['width'],'x',sz['height']
        sys.exit(1)

def save_source(outfile=SOURCEOUTFILE):
    """ save current page to file """

    with open(outfile, 'w') as html_file:
        html_file.write(driver.page_source.encode('utf8'))
    html_file.close()

def exit_failed():
    """ general exit routine """

    save_source() # save page we errored on
    driver.quit()
    sys.exit(1)

###############################################################################
#
# wait for element functions
#
# https://selenium-python.readthedocs.io/waits.html

#@timing
def wait_for_alert(err_msg,accept=True):
    """ wait_for_alert """
    # https://www.guru99.com/alert-popup-handling-selenium.html
    try:
        WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.alert_is_present()
        )
        alert = driver.switch_to.alert
        if accept:
            alert.accept()
        else:
            alert.dismiss()
    except Exception:
        print err_msg
        #exit_failed()

#@timing
def wait_for_element_by_name(el_name, err_msg):
    """ wait_for_element_by_name """
    try:
        element = WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.NAME, el_name))
        )
        return element
    except Exception:
        print err_msg
        exit_failed()

#@timing
def wait_for_element_by_class(cl_name, err_msg):
    """ wait_for_element_by_class """
    try:
        element = WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.CLASS_NAME, cl_name))
        )
        return element
    except Exception:
        print err_msg
        exit_failed()

#@timing
def wait_for_element_by_xpath(x_path, err_msg):
    """ wait_for_element_by_xpath """
    try:
        element = WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.XPATH, x_path))
        )
        return element
    except Exception:
        print err_msg
        print traceback.format_exc()
        exit_failed()

#@timing
def wait_for_element_by_css(css, err_msg):
    """ wait_for_element_by_css """
    try:
        element = WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, css))
        )
        return element
    except Exception:
        print err_msg
        print traceback.format_exc()
        exit_failed()

#@timing
def wait_for_element_by_id(elid, err_msg):
    """ wait_for_element_by_id """
    try:
        element = WebDriverWait(driver, PAGELOAD_TIMEOUT).until(
            EC.presence_of_element_located((By.ID, elid))
        )
        return element
    except Exception:
        print err_msg
        print traceback.format_exc()
        exit_failed()

###############################################################################
#
# Data gathering and output functions
#

#@timing
def get_table_data():

    """ grab table data from page - selenium is very slow at this, so use lxml (underlying module on beautiful soup) """


# put the table rows into all_data
    global all_data

# this takes 17600ms to run on each page ~17secs  ouch!
#    table_id = driver.find_element(By.CLASS_NAME, 'fgnp-sortable')
#    rows = table_id.find_elements(By.TAG_NAME, "tr") # get all of the rows in the table
#    for row in rows:
#        tds = row.find_elements(By.TAG_NAME, "td")
#        data = []
#        for td in tds:
#            data.append(td.text) # a list of tds
#        all_data.append( data ) # list of lists

    # this code takes ~25ms !!!
    root = lxml.html.fromstring(driver.page_source)
    for row in root.xpath('.//table[contains(@class,"fgnp-sortable")]//tbody//tr'):
        cells = row.xpath('.//td/text()')
        all_data.append(cells[0:3]) # tail cells contain lots of whitespace and we only need the first few

#@timing
def write_simple_csv():
    """ save to file as a simple csv """

    with open(OUTFILE, 'w') as outfile:
        counter = 0
        for fields in all_data:
            counter = counter + 1
            outfile.write(','.join(fields))
            outfile.write('\n') # add a new line
    outfile.close()
    print "Wrote", counter, "rows"

###############################################################################
#
# page access functions
#

# we split these up so we can time how long each page takes to load and access

@timing
def open_homepage():
    """ open the initial page """
    driver.get(HOME_URL)

@timing
def select_login():
    """ find and click the login button/link """
    wait_for_element_by_class("signin-other-options-text", "Died waiting for login button")
    login_button = driver.find_element(By.CLASS_NAME, "signin-other-options-text")

    # scroll page to the button (if page is wider than view) - does not work with xvfb
    loc = login_button.location_once_scrolled_into_view
    time.sleep(5)
    login_button.click()

#@timing
def wait_for_login():
    """ wait for login fields to appear """
    wait_for_element_by_id("signin-notice", "Died waiting for login id")

#@timing
def fill_in_login():
    """ fill-in login page details """
    username = driver.find_element_by_name('username')
    password = driver.find_element_by_name('password')
    username.send_keys(USERNAME)
    password.send_keys(PASSWORD)

@timing
def submit_login():
    """ submit the login form """
    google_button = driver.find_element_by_class_name('google-logo')
    google_button.click()

@timing
def wait_for_navbar_and_search():
    """ wait for search field to appear """
    wait_for_element_by_id("navbar-query", "Died waiting for navbar query")
    query = driver.find_element_by_id('navbar-query')
    query.send_keys(QUERY)
    query.submit()

@timing
def wait_for_results_and_select():
    """ wait for search results to appear """
    wait_for_element_by_class("result_text", "Died waiting for results")

    #<td class="result_text"> <a href="/title/tt5171438/?ref_=fn_al_tt_1">Star Trek: Discovery</a> (2017) (TV Series) </td>

    results = driver.find_element_by_xpath(".//td[contains(@class,'result_text')]//a") # get first matching element
    results.click()

@timing
def set_rating():

    rating = driver.find_element_by_xpath(".//div[contains(@class,'star-rating-button')]//button") # set rating button
    rating.click()

    # <a class="" title="Click to rate: 10" rel="nofollow" data-reactid=".2.1.0.1.$10"><span data-reactid=".2.1.0.1.$10.0">10</span></a>
    ratingset = driver.find_element_by_xpath(".//a[contains(@title,'Click to rate: 10')]") # set rating button
    ratingset.click()




###################################################################################
#
##### MAIN #####
#

# get login data
PROXY = os.getenv('https_proxy')
USERNAME = os.getenv('OS_USERNAME')
PASSWORD = os.getenv('OS_PASSWORD')
CONTRACT = os.getenv('OS_USER_DOMAIN_NAME')

if USERNAME == None or PASSWORD == None or CONTRACT == None:
    print "Missing K5 auth env vars"
    sys.exit(1)

if PROXY is not None:
    print "Proxy is set, continue?"
    time.sleep(5)

DISPLAY = os.getenv('DISPLAY')
if DISPLAY == None:
    print "no DISPLAY env var"
    sys.exit(1)
else:
    print "DISPLAY =", DISPLAY

#
# the actual work - done in functions so that they can be timed
#

print "Web Portal Access Timings..."

webdriver_setup()
open_homepage()
#select_login()
#wait_for_login()
#submit_login()

wait_for_navbar_and_search()

wait_for_results_and_select()

#set_rating()

show_timing_stats()


time.sleep(10)

driver.quit()
# clean exit
sys.exit(0)

