# pip install playwright
# playwright install firefox
# pip install python-dotenv

"""
Ensure that Home page is set to "Recents" in Settings
before executing this script
"""

import sys

sys.dont_write_bytecode = True

import os
from playwright.sync_api import sync_playwright, TimeoutError
from logging_formatter import Year
from login_logger import LoginLogger
from log_concat import update_logs
from dotenv import load_dotenv
import json

load_dotenv()


# ----------------------------------- #
# Pulling Mega.NZ login credentials from GitHub secrets
# {user1: password1, user2: password2, user3: password3}

# Converting JSON string to python dictionary,
# will be looped through
cred_dict = json.loads(os.getenv("MEGA"))


mega = "https://mega.nz/"
mega_signin = mega + "login"
mega_usr_sel = "input#login-name2"
mega_pwd_sel = "input#login-password2"
mega_homepage = "https://mega.nz/fm/recents"


def mkfilename(a):
    filename = f"[{Year}] {a} log.csv"
    return filename


#
# ----------------------------------- #


# =================================== #
# Optional scraper script
#
def query_mega_storage(instance):
    page = instance.tab
    logger = instance.logger

    page.wait_for_selector("div.account.left-pane.info-block.backup-button")
    # page.wait_for_load_state("networkidle")

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
    #
    # =================================== #


def mega_login(instance):
    # Browser session to generate new csv log file
    with sync_playwright() as pw:
        logger = instance.logger
        instance.one_step_login(pw, "#login_form button.login-button")
        instance.redirect(href_sel="a.mega-component.to-my-profile.nav-elem.text-only.link")
        query_mega_storage(instance)
        logger.info("Tasks complete. Closing browser")

    # Remove FileHandlder to prevent reopening the previous instance's file in the next instance
    # due to the Class Variable getting recreated during "self.logger.addHandler(self.DuoHandler)"
    logger.removeHandler(instance.DuoHandler)

    # Close csv file in current instance when done with writing logs
    instance.formatter.csvfile.close()


if __name__ == "__main__":
    i = 1
    for user in cred_dict:
        instance = LoginLogger(
            base_url=mega,
            login_url=mega_signin,
            usr_sel=mega_usr_sel,
            usr=user,
            pwd_sel=mega_pwd_sel,
            pwd=cred_dict[user],
            homepage=mega_homepage,
            filename=mkfilename(f"mega_{i}"),
        )
        mega_login(instance)
        update_logs(instance)
        i += 1
