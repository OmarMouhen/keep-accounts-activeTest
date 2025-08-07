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
import json

load_dotenv()


# ----------------------------------- #
# Pulling OneDrive login credentials from GitHub secrets
# {user1: password1, user2: password2, user3: password3}

# Converting JSON string to python dictionary,
# will be looped through
cred_dict = json.loads(os.getenv("ONEDRIVE"))


onedrive = "https://onedrive.live.com"
onedrive_signin = "https://onedrive.live.com/login/"
onedrive_usr_sel = "//input[@type='email']"
onedrive_pwd_sel = "//input[@type='password']"
onedrive_homepage = "https://onedrive.live.com/?id=root"
iframe_sel = "//iframe[@class='signInFrame']"


def mkfilename(a):
    filename = f"[{Year}] {a} log.csv"
    return filename


#
# ----------------------------------- #

# =================================== #
# Optional scraper script
#
def query_onedrive_storage(instance):
    page = instance.tab
    logger = instance.logger

    logger.info(f"Getting storage details from '{instance.dashboard_url}'")
    page.wait_for_timeout(2529)

    name = page.query_selector(
        "div#O365_HeaderRightRegion span[style='display: none;']"
    ).inner_text()

    email = instance.usr

    plan = page.query_selector(
        """div:nth-child(5) > table > tbody > tr:nth-child(1) > td[class*='storageInfoPlansTypeTextCell'] > span > span"""
    ).inner_text().strip()

    storage_name = page.query_selector(
        'div[class*="storageInfoTotalUsed"]'
    ).inner_text().strip()

    storage_used = page.query_selector(
        'div[class*=quotaUsage] > div[class*=quotaUsed]'
    ).inner_text().strip()

    storage_total = page.query_selector(
        'div[class*=quotaUsage] > div[class*=quotaTotal]'
    ).inner_text().strip()

    # Future work: Scraping info from API endpoint instead of rendered webpage
    #
    # except:
    #     context_uri = ""
    #     context_headers = {"accept": "application/json"}
    #     storage_uri = "https://skyapi.onedrive.live.com/API/2/GetStorageInfo?planDetails=true&quotaForDisabled=true"
    #     storage_headers = {
    #         "appid": "1141147648",
    #         "referer": "https://onedrive.live.com/",
    #     }

    logger.debug(f"Profile name: {name}")
    logger.debug(f"Email: {email}")
    logger.debug(f"Plan: {plan}")
    logger.debug(f"{storage_name}: {storage_used} {storage_total}")
    #
    # =================================== #


def onedrive_login(instance):
    with sync_playwright() as pw:
        # Browser session to generate new csv log file
        logger = instance.logger
        instance.iframe_login(pw, iframe_sel)
        instance.redirect(href_sel="//a[contains(@class, 'usedQuotaText')]")
        query_onedrive_storage(instance)
        logger.info("Tasks complete. Closing browser")

    # Remove FileHandler to prevent reopening the previous instance's file in the next instance
    # due to the Class Variable getting recreated during "self.logger.addHandler(self.DuoHandler)"
    logger.removeHandler(instance.DuoHandler)

    # Close csv file in current instance when done with writing logs
    instance.formatter.csvfile.close()


if __name__ == "__main__":
    i = 1
    for user in cred_dict:
        instance = LoginLogger(
            base_url=onedrive,
            login_url=onedrive_signin,
            usr_sel=onedrive_usr_sel,
            usr=user,
            pwd_sel=onedrive_pwd_sel,
            pwd=cred_dict[user],
            homepage=onedrive_homepage,
            filename=mkfilename(f"onedrive_{i}"),
        )
        onedrive_login(instance)
        update_logs(instance)
        i += 1
