# keep-mega-active.py (debug version)

# pip install playwright
# playwright install firefox
# pip install python-dotenv

"""
Ensure that Mega home page is set to "Recents" before running this.
Make sure `.env` contains properly escaped JSON credentials for MEGA.
"""

import sys
sys.dont_write_bytecode = True

import os
from playwright.sync_api import sync_playwright, TimeoutError
from logging_formatter import Year
# from login_logger import LoginLogger
from log_concat import update_logs
from dotenv import load_dotenv
import json

load_dotenv()

# Load credentials from .env
cred_dict = json.loads(os.getenv("MEGA"))

mega = "https://mega.nz/"
mega_signin = mega + "login"
mega_usr_sel = "input#login-name2"
mega_pwd_sel = "input#login-password2"
mega_homepage = "https://mega.nz/fm/recents"

def mkfilename(a):
    return f"[{Year}] {a} log.csv"

def query_mega_storage(instance):
    page = instance.tab
    logger = instance.logger

    page.wait_for_selector("div.account.left-pane.info-block.backup-button")
    name = page.query_selector("div.membership-big-txt.name").inner_text()
    page.wait_for_selector("div.account.membership-plan")
    email = page.query_selector("div.membership-big-txt.email").inner_text()
    plan = page.query_selector("div.account.membership-plan").inner_text()

    logger.info(f"Getting storage details from '{instance.dashboard_url}'")
    logger.debug(f"Profile name: {name}")
    logger.debug(f"Email: {email}")
    logger.debug(f"Plan: {plan}")

    storage_categories = page.query_selector_all("div.account.item-wrapper")
    for category in storage_categories:
        name = category.query_selector("div.account.progress-title > span").inner_text()
        num = category.query_selector("div.account.progress-size.small").inner_text()
        logger.debug(f"{name}: {num}")

def mega_login(instance):
    with sync_playwright() as pw:
        logger = instance.logger
        logger.info("Launching browser")

        # Launch with GUI for debugging
        browser = pw.firefox.launch(headless=False, slow_mo=100, args=["--start-maximized"])
        page = browser.new_page(no_viewport=True)

        # Block unnecessary resources
        page.route("**/*", lambda route: route.abort() if route.request.resource_type in ["image", "media"] else route.continue_())

        logger.info(f"Retrieving login page '{instance.login_url}'")
        page.goto(instance.login_url)

        logger.info("Filling username")
        page.fill(instance.usr_sel, instance.usr)

        logger.info("Filling password")
        page.fill(instance.pwd_sel, instance.pwd)

        login_btn = "button.red-button.login-button"
        logger.info("Waiting for login button")
        page.wait_for_selector(login_btn)

        logger.info("Clicking login button")
        page.click(login_btn)
        page.keyboard.press("Enter")

        logger.info("Waiting for dashboard...")
        try:
            page.wait_for_url(instance.homepage, wait_until="domcontentloaded", timeout=120_000)
            logger.info("Login successful, at homepage")
        except TimeoutError:
            logger.error("Login likely failed or took too long.")

        instance.tab = page
        query_mega_storage(instance)
        logger.info("Closing browser")
        browser.close()

        # Finalize logs
        logger.removeHandler(instance.DuoHandler)
        instance.formatter.csvfile.close()

if __name__ == "__main__":
    for i, account in enumerate(cred_dict, 1):
        usr = account["USR"]
        pwd = account["PWD"]
        instance = LoginLogger(
            base_url=mega,
            login_url=mega_signin,
            usr_sel=mega_usr_sel,
            usr=usr,
            pwd_sel=mega_pwd_sel,
            pwd=pwd,
            homepage=mega_homepage,
            filename=mkfilename(f"mega_{i}")
        )
        mega_login(instance)
        update_logs(instance)