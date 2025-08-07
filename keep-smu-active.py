# pip install playwright
# playwright install firefox
# pip install python-dotenv

import json
from dotenv import load_dotenv
from log_concat import update_logs
from login_logger import LoginLogger
from logging_formatter import Year
from playwright.sync_api import sync_playwright, TimeoutError
import os
import sys

sys.dont_write_bytecode = True


load_dotenv()


# ----------------------------------- #
# Pulling SMU login credentials from GitHub secrets
# {user1: password1, user2: password2, user3: password3}

# Converting JSON string to python dictionary,
# will be looped through
cred_dict = json.loads(os.getenv("SMU"))


smu = "https://academylearn.smu.edu.sg"
smu_signin = smu + "/index"
smu_signin_elem = "a#tl-cms-nav-login"
smu_usr_sel = "input#tl-shared-username"
smu_pwd_sel = "input.tl-form-password-field"
smu_homepage = smu + "/dashboard"
# logout_button = "li#tl-navbar-logout > a#navbar-logout"
logout_button = "i.icon-logout.nav-logout"


def mkfilename(a):
    filename = f"[{Year}] {a} log.csv"
    return filename


def smu_login(instance):
    with sync_playwright() as pw:
        logger = instance.logger
        logger.info("Launching browser")
        browser = pw.firefox.launch(args=["--start-maximized"], headless=True)
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
        page.goto(instance.login_url)
        logger.info(f"Retrieving login page '{instance.login_url}'")
        page.click(smu_signin_elem)
        page.fill(instance.usr_sel, instance.usr)
        page.fill(instance.pwd_sel, instance.pwd)
        page.keyboard.press("Enter")
        logger.info("Logging in")
        page.wait_for_url(instance.homepage,
                          wait_until="networkidle", timeout=120_000)
        logger.info("Logged in successfully")
        points = page.query_selector(
            "//div[text()='points']//preceding-sibling::div"
        ).get_attribute("data-value")
        # {:,} to add commas (thousands separator) to numbers
        logger.debug(f"Points: {int(points):,}")
        logger.info("Tasks complete. Closing browser")
        # try:
        #     page.click(logout_button)
        # except Exception as e:
        #     for line in str(e).split("\n"):
        #         logger.error(line)

    # Remove FileHandlder to prevent reopening the previous instance's file in the next instance
    # due to the Class Variable getting recreated during "self.logger.addHandler(self.DuoHandler)"
    logger.removeHandler(instance.DuoHandler)

    # Close csv file in current instance when done with writing logs
    instance.formatter.csvfile.close()


if __name__ == "__main__":
    i = 1
    for user in cred_dict:
        instance = LoginLogger(
            base_url=smu,
            login_url=smu_signin,
            usr_sel=smu_usr_sel,
            usr=user,
            pwd_sel=smu_pwd_sel,
            pwd=cred_dict[user],
            homepage=smu_homepage,
            filename=mkfilename(f"smu_{i}"),
        )
        smu_login(instance)
        update_logs(instance)
        i += 1
