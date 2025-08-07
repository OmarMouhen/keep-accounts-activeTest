import sys
from urllib import response

sys.dont_write_bytecode = True

import os
import logging
from logging_formatter import CsvFormatter
from time import sleep
import json
import re


class LoginLogger:
    def __init__(
        self, base_url, login_url, usr_sel, usr, pwd_sel, pwd, homepage, filename
    ):
        # --- From params --- #
        self.url = base_url
        self.login_url = login_url
        self.usr_sel = usr_sel
        self.usr = usr
        self.pwd_sel = pwd_sel
        self.pwd = pwd
        self.homepage = homepage  # landing page upon logging in
        self.filename = filename
        # ------------------- #

        self.dashboard_url = None
        self.tab = None  # To store playwright Page class instance

        self.formatter = CsvFormatter(self.filename)
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.DuoHandler = logging.StreamHandler()
        self.DuoHandler.setFormatter(self.formatter)
        self.logger.addHandler(self.DuoHandler)

    def one_step_login(self, playwright, button=None):
        logger = self.logger
        logger.info("Launching browser")
        browser = playwright.firefox.launch(args=["--start-maximized"], headless=True)
        page = browser.new_page(no_viewport=True)
        page.route(
            "**/*",
            lambda route: route.abort()
            if (
                route.request.resource_type == "image"
                or route.request.resource_type == "media"
            )
            else route.continue_(),
        )
        page.goto(self.login_url)
        logger.info(f"Retrieving login page '{self.login_url}'")
        page.fill(self.usr_sel, self.usr)
        page.fill(self.pwd_sel, self.pwd)
        if button is not None:
            page.wait_for_selector(button)
            if page.locator(button).is_enabled():
                try:
                    page.click(button)
                    page.keyboard.press("Enter")
                    page.keyboard.press("Enter")
                    logger.info("Logging in")
                except:
                    logger.error("Login button error")
            else:
                page.keyboard.press("Enter")
                page.keyboard.press("Enter")
                logger.info("Logging in")
        else:
            page.keyboard.press("Enter")
            page.keyboard.press("Enter")
            logger.info("Logging in")
        page.wait_for_url(self.homepage, wait_until="domcontentloaded", timeout=120_000)
        logger.info("Logged in successfully")
        self.tab = page

    def two_step_login(self, playwright, captcha_page=None, pwd_page=None):
        logger = self.logger
        logger.info("Launching browser")
        browser = playwright.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(self.login_url)
        logger.info(f"Retrieving login page '{self.login_url}'")
        page.fill(self.usr_sel, self.usr)
        page.keyboard.press("Enter")
        if captcha_page is not None:
            try:
                logger.info(f"Waiting for captcha page '{captcha_page}'")
                page.wait_for_url(
                    captcha_page + "**", wait_until="domcontentloaded", timeout=10_000
                )
                logger.info("Attempting to skip captcha")
                page.keyboard.press("Tab")
                page.keyboard.press("Tab")
                page.keyboard.press("Tab")
                page.keyboard.press("Enter")
                page.keyboard.press("Tab")
                page.keyboard.press("Tab")
                page.keyboard.press("Tab")
                page.keyboard.press("Enter")
            except:
                logger.warning("Captcha page not loaded")
                pass
        if pwd_page is not None:
            try:
                logging.info(f"Waiting for password page '{pwd_page}'")
                page.wait_for_url(
                    pwd_page + "**", wait_until="domcontentloaded", timeout=10_000
                )
                logging.info("Password page loaded")
            except:
                logger.error("Password page not loaded")
                pass
        page.fill(self.pwd_sel, self.pwd, timeout=10_000)
        page.keyboard.press("Enter")
        logger.info("Logging in")
        page.wait_for_url(self.homepage + "**")
        page.wait_for_load_state("domcontentloaded")
        logger.info("Logged in successfully")
        self.tab = page

    def iframe_login(self, playwright, frame_locator, **kwargs):
        logger = self.logger
        logger.info("Launching browser")
        browser = playwright.firefox.launch(headless=True)
        page = browser.new_page()
        page.goto(self.login_url)
        logger.info(f"Retrieving login page '{self.login_url}'")
        page.wait_for_url(self.login_url, wait_until="domcontentloaded")
        frame = page.frame_locator(frame_locator).locator(self.usr_sel)
        frame.fill(self.usr)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2529)
        # --- Email confirmation bypass --- #
        if (page.get_by_role("button").get_by_text("Use your password").is_enabled) or \
            (page.locator("input#proof-confirmation-email-input").count() > 0 \
            and page.locator("h1[data-testid=title]").inner_text().lower() == "verify your email"):
                page.get_by_role("button").get_by_text("Use your password").click()

        # --------------------------------- #
        page.fill(self.pwd_sel, self.pwd)
        page.keyboard.press("Enter")
        page.wait_for_timeout(2529)
        page.locator("button[data-testid=primaryButton]").click()
        # page.keyboard.press("Enter")
        logger.info("Logging in")
        try:
            page.wait_for_url(self.homepage + "**", wait_until="domcontentloaded")
        except:
            page.wait_for_url(re.compile(rf"{self.url}"))
        logger.info("Logged in successfully")
        self.tab = page

    def redirect(self, **kwargs):
        logger = self.logger
        page = self.tab
        if "button_sel" in kwargs:
            page.locator(kwargs.get("button_sel")).click()
            page.wait_for_load_state("domcontentloaded")
            self.dashboard_url = page.url
            return 0
        if "href_sel" in kwargs:
            self.dashboard_url = self.url + page.locator(
                kwargs.get("href_sel")
            ).get_attribute("href")
        elif "url" in kwargs:
            self.dashboard_url = kwargs.get("url")
        self.dashboard_url.replace("#", "?")
        page.goto(self.dashboard_url)
        page.wait_for_timeout(2529)


# def rename_file(new_name):
#     year = Year

#     # open("temp.csv").close()  # file was kept open while writing logs
#     new_filename = f"[{year}] {new_name}.csv"
#     cols = ["Date", "Time", "Level", "Message"]

#     def execute(action):
#         with open("temp.csv", "r") as infile, open(
#             new_filename, action, newline=""
#         ) as outfile:
#             writer = DictWriter(outfile, fieldnames=cols, extrasaction="ignore")
#             reader = DictReader(infile)
#             for row in reader:
#                 if "Using selector:" not in row["Message"]:
#                     writer.writerow(row)
#                     print(row)

#     if os.path.isfile(new_filename):
#         execute("a")
#         os.remove("temp.csv")
#     else:
#         execute("w")
#         os.remove("temp.csv")
