# pip install playwright
# playwright install firefox
# pip install python-dotenv

import sys

sys.dont_write_bytecode = True

import os
from playwright.sync_api import sync_playwright, TimeoutError
from logging_formatter import Year
from login_logger import LoginLogger
from log_concat import update_logs
from dotenv import load_dotenv

load_dotenv()


# ----------------------------------- #
# Initialising Yahoo Mail instances
# Enclose them in functions to be called later
# Instantiate only at runtime to prevent concurrent runs

yahoo = "mail.yahoo.com"
yahoo_signin = "https://login.yahoo.com/?src=ym"
yahoo_usr_sel = "input#login-username"
yahoo_pwd_sel = "input#login-passwd"
yahoo_homepage = "https://mail.yahoo.com/d/folders/1"


def mkfilename(a):
    filename = f"[{Year}] {a} log.csv"
    return filename


def yahoo_1():
    instance = LoginLogger(
        base_url=yahoo,
        login_url=yahoo_signin,
        usr_sel=yahoo_usr_sel,
        usr=os.getenv("USR_YAHOO_1"),
        pwd_sel=yahoo_pwd_sel,
        pwd=os.getenv("PWD_YAHOO_1"),
        homepage=yahoo_homepage,
        filename=mkfilename("yahoo_1"),
    )
    return instance
    #
    # ----------------------------------- #


#    ================================================================== #
#    Optional scraper script
#
def query_yahoo_storage(instance):
    page = instance.tab
    logger = instance.logger

    logger.info(f"Getting storage details from '{instance.dashboard_url}'")

    # ----------------------------------------------------------- #
    # JavaScript functions to modify selected elements in the DOM
    page.eval_on_selector(
        selector="div#ybarAccountMenuBody > ul > li > div > span:nth-child(1)",
        expression="(element) => element.style.visibility = 'visible'",
    )
    page.eval_on_selector(
        selector="div#ybarAccountMenuBody > ul > li > div > span:nth-child(2)",
        expression="(element) => element.style.visibility = 'visible'",
    )
    # ----------------------------------------------------------- #

    name = page.query_selector(
        "div#ybarAccountMenuBody > ul > li > div > span:nth-child(1)"
    ).inner_text()
    email = page.query_selector(
        "div#ybarAccountMenuBody > ul > li > div > span:nth-child(2)"
    ).inner_text()
    # storage_name = page.query_selector("p.M_0.A_6DUj.C_Z1YRXYn > span").inner_text()
    storage_name = page.query_selector(
        "div.X_6Fd5 > div > p:nth-child(1) > span"
    ).inner_text()
    # storage_used = page.query_selector("p.M_0.u_b > span").inner_text()
    storage_used = page.query_selector(
        "div.X_6Fd5 > div > p:nth-child(2) > span"
    ).inner_text()

    logger.debug(f"Profile name: {name}")
    logger.debug(f"Email: {email}")
    logger.debug(f"{storage_name}: {storage_used}")
    #
    # ============================================================== #


def yahoo_login(instance):
    # Browser session to generate new csv log file
    with sync_playwright() as pw:
        logger = instance.logger
        cap_page = "https://login.yahoo.com/account/challenge/recaptcha?src=ym"
        pwd_page = "https://login.yahoo.com/account/challenge/password?src=ym"
        instance.two_step_login(pw, cap_page, pwd_page)
        instance.redirect(url="https://mail.yahoo.com/d/settings/0")
        query_yahoo_storage(instance)
        logger.info("Tasks complete. Closing browser")

    # Remove FileHandlder to prevent reopening the previous instance's file in the next instance
    # due to the Class Variable getting recreated during "self.logger.addHandler(self.DuoHandler)"
    logger.removeHandler(instance.DuoHandler)

    # Close csv file in current instance when done with writing logs
    instance.formatter.csvfile.close()


if __name__ == "__main__":
    yahoo_login(yahoo_1())
    update_logs(yahoo_1())
