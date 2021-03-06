#!/usr/bin/env python


from __future__ import print_function

# Core
from functools import wraps
import logging
import pprint
import random
import time
import ConfigParser

# Third-Party
import argh

from clint.textui import progress
import funcy
from PIL import Image
from splinter import Browser
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import \
    TimeoutException, UnexpectedAlertPresentException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.support.ui as ui

# Local
import match_image4
import smallcrop


logging.basicConfig(
    format='%(lineno)s %(message)s',
    level=logging.WARN
)

random.seed()

pp = pprint.PrettyPrinter(indent=4)

base_url = 'http://www.mobrabus.com/'

action_path = dict(
    login='account/login',
    viewads='members/ads/rotator',
    dashboard='Dot_MembersPage.asp',
    withdraw='DotwithdrawForm.asp',
    buy_pack='members/sales/packages'
)

one_minute = 60
three_minutes = 3 * one_minute
ten_minutes = 10 * one_minute
one_hour = 3600


def url_for_action(action):
    return "{0}/{1}".format(base_url, action_path[action])


def loop_forever():
    while True:
        pass


def clear_input_box(box):
    box.type(Keys.CONTROL + "e")
    for i in xrange(100):
        box.type(Keys.BACKSPACE)
    return box


# http://stackoverflow.com/questions/16807258/selenium-click-at-certain-position
def click_element_with_offset(driver, elem, x, y):
    action = ActionChains(driver)
    echo_print("Moving to x position", x)
    echo_print("Moving to y position", y)
    action.move_to_element_with_offset(elem, x, y)
    print("OK now see where the mouse is...")
    action.click()
    action.perform()


def page_source(browser):
    document_root = browser.driver.page_source
    return document_root


def wait_visible(driver, locator, by=By.XPATH, timeout=300):
    try:
        if ui.WebDriverWait(driver, timeout).until(EC.visibility_of_element_located((by, locator))):
            return driver.find_element(by, locator)
    except TimeoutException:
        return False


def trap_unexpected_alert(func):
    @wraps(func)
    def wrapper(self):
        try:
            return func(self)
        except UnexpectedAlertPresentException:
            print("Caught unexpected alert.")
            return 254
        except WebDriverException:
            print("Caught webdriver exception.")
            return 254

    return wrapper


def trap_any(func):
    @wraps(func)
    def wrapper(self):
        try:
            return func(self)
        except:
            print("Caught exception.")
            return 254

    return wrapper


def trap_alert(func):
    @wraps(func)
    def wrapper(self):
        try:
            return func(self)
        except UnexpectedAlertPresentException:
            print("Caught UnexpectedAlertPresentException.")
            return 254
        except WebDriverException:
            print("Caught webdriver exception.")
            return 253

    return wrapper


def get_element_html(driver, elem):
    return driver.execute_script("return arguments[0].innerHTML;", elem)


def echo_print(text, elem):
    print("{0}={1}.".format(text, elem))

# https://stackoverflow.com/questions/10848900/how-to-take-partial-screenshot-frame-with-selenium-webdriver/26225137#26225137?newreg=8807b51813c4419abbb37ab2fe696b1a


def element_screenshot(driver, element, filename):
    t = type(element).__name__

    if t == 'WebDriverElement':
        element = element._element
    bounding_box = (
        element.location['x'],  # left
        element.location['y'],  # upper
        (element.location['x'] + element.size['width']),  # right
        (element.location['y'] + element.size['height'])  # bottom
    )
    bounding_box = map(int, bounding_box)
    echo_print('Bounding Box', bounding_box)
    return bounding_box_screenshot(driver, bounding_box, filename)


def bounding_box_screenshot(driver, bounding_box, filename):
    driver.save_screenshot(filename)
    base_image = Image.open(filename)
    cropped_image = base_image.crop(bounding_box)
    base_image = base_image.resize(
        [int(i) for i in cropped_image.size])
    base_image.paste(cropped_image, (0, 0))
    base_image.save(filename)
    return base_image


class Entry(object):
    def __init__(self, username, password, browser):
        self._username = username
        self._password = password
        self.browser = browser

    def login(self):
        print("Logging in...")

        self.browser_visit('login')

        self.browser.find_by_name('username').type(self._username)
        self.browser.find_by_name('password').type(self._password)

        # wait_time = 10
        # for i in progress.bar(range(wait_time)):
        #     time.sleep(1)

        # captcha_elem = self.browser.find_by_id('captcha').first
        # captcha_file = 'captcha.png'
        # element_screenshot(self.browser.driver, captcha_elem, captcha_file)

        self.browser.find_by_name('submit').click()

        # solver = CaptchaSolver('browser')
        # with open(captcha_file, 'rb') as inp:
        #     raw_data = inp.read()
        # print(solver.solve_captcha(raw_data))


    def browser_visit(self, action_label):
        try:
            logging.debug("Visiting URL for {0}".format(action_label))
            self.browser.visit(url_for_action(action_label))
            return 0
        except UnexpectedAlertPresentException:
            print("Caught UnexpectedAlertPresentException.")
            logging.warn("Attempting to dismiss alert")
            alert = self.browser.driver.switch_to_alert()
            alert.dismiss()
            return 254
        except WebDriverException:
            print("Caught webdriver exception.")
            return 253

    def view_ads(self, surf_amount):
        for i in xrange(1, surf_amount + 1):
            while True:
                print("Viewing ad {0}".format(i))
                result = self.view_ad()
                if result == 0:
                    break

    @trap_alert
    def view_ad(self):
        logging.warn("Visiting viewads")
        self.browser_visit('viewads')

        image_to_match_elem = wait_visible(self.browser.driver, '//*[@id="view"]/table/tbody/tr/td[1]/img')
        self.browser.driver.execute_script("arguments[0].setAttribute('style', '')", image_to_match_elem)
        self.browser.driver.execute_script("arguments[0].setAttribute('width', '56')", image_to_match_elem)
        self.browser.driver.execute_script("arguments[0].setAttribute('height', '40')", image_to_match_elem)

        candidate_images_elem = self.browser.find_by_xpath('//*[@id="view"]/table/tbody/tr/td[3]/img').first

        if not all([image_to_match_elem, candidate_images_elem]):
            raise Exception("All required images not located")

        query_image = 'image_to_match.gif'
        element_screenshot(self.browser.driver, image_to_match_elem, query_image)
        element_screenshot(self.browser.driver, candidate_images_elem, 'candidate_images.gif')

        sectioned_image = smallcrop.horizontal_sections('candidate_images.gif', 4)
        match = match_image4.closest(query_image, sectioned_image['filenames'])
        echo_print('closest image', match)
        i = sectioned_image['filenames'].index(match)

        area_elems = self.browser.find_by_xpath("//area")
        js_to_execute = area_elems[i]['onclick']
        self.browser.execute_script(js_to_execute)

        # x_offset = sectioned_image['offsets'][i]
        # candidate_images_elem.click()
        # click_element_with_offset(self.browser.driver, candidate_images_elem._element, x_offset+3, 3)
        return 0

    def wait_on_ad(self):
        time_to_wait_on_ad = random.randrange(40, 50)
        for i in progress.bar(range(time_to_wait_on_ad)):
            time.sleep(1)

    def buy_pack(self):
        self.browser_visit('buy_pack')
        self.browser.find_by_name('qty[18]').first.type("1")
        self.browser.select('processor[18]', "2")  # STP=4, Payza=2
        time.sleep(5)
        self.browser.execute_script("buy_sales_package(18)")
        with self.browser.get_alert() as alert:
            alert.accept()

    def calc_account_balance(self):
        time.sleep(1)

        logging.warn("visiting dashboard")
        self.browser_visit('dashboard')

        logging.warn("finding element by xpath")
        elem = self.browser.find_by_xpath(
            '/html/body/table[2]/tbody/tr/td[2]/table/tbody/tr/td[2]/table[6]/tbody/tr/td/table/tbody/tr[2]/td/h2[2]/font/font'
        )

        print("Elem Text: {}".format(elem.text))

        self.account_balance = float(elem.text[1:])

        print("Available Account Balance: {}".format(self.account_balance))

    def calc_credit_packs(self):
        time.sleep(1)

        logging.warn("visiting dashboard")
        self.browser_visit('dashboard')

        logging.warn("finding element by xpath")
        elem = self.browser.find_by_xpath(
            "//font[@color='#009900']"
        )

        print("Active credit packs = {0}".format(elem[0].text))
        # for i, e in enumerate(elem):
        #     print("{0}, {1}".format(i, e.text))

    def solve_captcha(self):
        time.sleep(3)

        t = page_source(self.browser).encode('utf-8').strip()
        # print("Page source {0}".format(t))

        captcha = funcy.re_find(
            """ctx.strokeText\('(\d+)'""", t)

        # print("CAPTCHA = {0}".format(captcha))

        self.browser.find_by_name('codeSb').fill(captcha)

        time.sleep(6)
        button = self.browser.find_by_name('Submit')
        button.click()


def main(conf, surf=False, buy_pack=False, stay_up=False, surf_amount=10):
    config = ConfigParser.ConfigParser()
    config.read(conf)
    username = config.get('login', 'username')
    password = config.get('login', 'password')

    with Browser() as browser:
        browser.driver.set_window_size(1200, 1100)
        e = Entry(username, password, browser)

        e.login()

        if buy_pack:
            e.buy_pack()

        if surf:
            e.view_ads(surf_amount)

        if stay_up:
            loop_forever()

if __name__ == '__main__':
    argh.dispatch_command(main)
