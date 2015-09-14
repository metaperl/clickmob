#!/usr/bin/env python


from __future__ import print_function

# core
from datetime import datetime, timedelta
from functools import wraps
import logging
import pprint
import random
import sys
import time

# pypi
import argh
from captcha_solver import CaptchaSolver


from clint.textui import progress
import funcy
from PIL import Image
from splinter import Browser
from selenium.common.exceptions import \
    TimeoutException, UnexpectedAlertPresentException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import selenium.webdriver.support.expected_conditions as EC
import selenium.webdriver.support.ui as ui

# local
import conf  # it is used. Even though flymake cant figure that out.

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
    withdraw='DotwithdrawForm.asp'
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


def page_source(browser):
    document_root = browser.driver.page_source
    return document_root


def wait_visible(driver, locator, by=By.XPATH, timeout=30):
    try:
        return ui.WebDriverWait(driver, timeout).until(
            EC.visibility_of_element_located((by, locator)))
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
    element = element._element
    bounding_box = (
        element.location['x'],  # left
        element.location['y'],  # upper
        (element.location['x'] + element.size['width']),  # right
        (element.location['y'] + element.size['height'])  # bottom
    )
    return bounding_box_screenshot(driver, bounding_box, filename)


def bounding_box_screenshot(driver, bounding_box, filename):
    driver.save_screenshot(filename)
    base_image = Image.open(filename)
    cropped_image = base_image.crop(bounding_box)
    base_image = base_image.resize(cropped_image.size)
    base_image.paste(cropped_image, (0, 0))
    base_image.save(filename)
    return base_image


class Entry(object):
    def __init__(
            self, loginas, browser, surf_amount, buy_pack
    ):
        modobj = sys.modules['conf']
        print(modobj)
        d = getattr(modobj, loginas)

        self._username = d['username']
        self._password = d['password']
        self._pin = d['pin']
        self.browser = browser
        self._surf_amount = surf_amount
        self._buy_pack = buy_pack

    def login(self):
        print("Logging in...")

        self.browser_visit('login')

        self.browser.find_by_name('username').type(self._username)
        self.browser.find_by_name('password').type(self._password)

        print("Enter the CAPTCHA manually please")
        wait_time = 10
        for i in progress.bar(range(wait_time)):
            time.sleep(1)

        captcha_elem = self.browser.find_by_id('captcha').first
        captcha_file = 'captcha.png'
        element_screenshot(self.browser.driver, captcha_elem, captcha_file)

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
            alert = self.driver.switch_to_alert()
            alert.dismiss()
            return 254
        except WebDriverException:
            print("Caught webdriver exception.")
            return 253

    def view_ads(self):
        for i in xrange(1, self._surf_amount + 1):
            while True:
                print("Viewing ad {0}".format(i))
                result = self.view_ad()
                if result == 0:
                    break

        self.calc_account_balance()
        self.calc_time(stay=False)
        if self._buy_pack:
            self.buy_pack()


    @trap_alert
    def view_ad(self):
        logging.warn("Visiting viewads")
        self.browser_visit('viewads')
        time.sleep(random.randrange(2, 5))

        loop_forever()

        return 0


    def wait_on_ad(self):
        time_to_wait_on_ad = random.randrange(40, 50)
        for i in progress.bar(range(time_to_wait_on_ad)):
            time.sleep(1)


    def buy_pack(self):
        self.calc_account_balance()
        print("Balance: {}".format(self.account_balance))
        if self.account_balance >= 49.99:
            self.buy_pack_internal()

    def buy_pack_internal(self):
        a = self.browser.find_by_xpath(
            '//a[@href="Dot_CreditPack.asp"]'
        )
        print("A: {0}".format(a))
        a.click()

        button = wait_visible(self.browser.driver, 'Preview', by=By.NAME)
        button.click()

        button = wait_visible(self.browser.driver, 'Preview', by=By.NAME)
        button.click()


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


def main(loginas, random_delay=False, surf=False, stayup=False, surf_amount=10,
        buy_pack=False
):
    if random_delay:
        random_delay = random.randint(1, 15)
        print("Random delay = {0}".format(random_delay))
        time.sleep(one_minute * random_delay)

    with Browser() as browser:

        browser.driver.set_window_size(1200, 1100)

        e = Entry(loginas, browser, surf_amount, buy_pack)

        e.login()

        if surf:
            e.view_ads()
        if action == 'time':
            e.time_macro()
        if action == 'buy':
            e.buy_pack()
        if action == 'withdraw':
            e.withdraw()
        if action == 'check':
            if clicked < 10:
                e.view_ads()
            if e._buy_pack:
                e.buy_pack()

        if stayup:
            e.time_macro()
            loop_forever()


def conda_main():
    argh.dispatch_command(main)


if __name__ == '__main__':
    argh.dispatch_command(main)
