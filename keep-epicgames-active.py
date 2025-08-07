# pip install playwright
# playwright install firefox
# pip install python-dotenv
# pip install rapidfuzz==2.0.11
# pip install requests

"""
Assumes that page upon login is the account profile page
https://www.epicgames.com/account/personal

What this script does
---------------------
1. Accesses the epicgames backend API to get information on free games
    Parses JSON and creates a dictionary for each game
    Example: game data for Runbow
        {'title': 'Runbow', 'namespace': 'aa7c3e6b5a2a4ca8962270c15bddb861', 'id': 'd98bc011d00a4323b2c49c7dc9d75969'}

2. Logs in to account and navigates to free games page

3. Only looks out for games free for a limited time (button with "Free Now" text)

4. Clicks each "Free Now" button and checks if game is available ("GET") or has already been claimed ("In Library")

5. If game is available in your region, script navigates to purchase page and clicks order button

    Purchase page URL format
        Base:
            https://store.epicgames.com/purchase
        Query parameters: 
            offers=1-<game namespace>-<game id>
            orderId
            purchaseToken
            showNavigation=true
        Slug:
            /purchase/payment-methods

    Example: purchase page for Runbow
        https://store.epicgames.com/purchase?offers=1-aa7c3e6b5a2a4ca8962270c15bddb861-d98bc011d00a4323b2c49c7dc9d75969&orderId&purchaseToken&showNavigation=true#/purchase/payment-methods
"""

import sys

sys.dont_write_bytecode = True

import os
import requests
from playwright.sync_api import sync_playwright
from logging_formatter import Year
from login_logger import LoginLogger
from log_concat import update_logs
from dotenv import load_dotenv
import json
from time import sleep
import traceback
from rapidfuzz.process import extractOne
from rapidfuzz.fuzz import ratio

load_dotenv()


# ----------------------------------- #
# Pulling Epic Games login credentials from GitHub secrets
# {user1: password1, user2: password2, user3: password3}

# Converting JSON string to python dictionary,
# will be looped through
cred_dict = json.loads(os.getenv("EPICGAMES"))


epic = "https://www.epicgames.com"
epic_signin = epic + "/id/login/epic?lang=en-US&noHostRedirect=true"
epic_usr_sel = "input#email"
epic_pwd_sel = "input#password"
epic_homepage = epic + "/account/personal"


def mkfilename(a):
    filename = f"[{Year}] {a} log.csv"
    return filename


#
# ----------------------------------- #


# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #
# Script to retrieve game data from API
#
# def get_game_data():
print()
print("=" * 50)
print("\nRetrieving game data before starting Playwright\n\n")

api = "https://store-site-backend-static-ipv4.ak.epicgames.com/freeGamesPromotions?locale=en-US"

headers = {
    "Access-Control-Allow-Origin": "https://store.epicgames.com",
    "Access-Control-Allow-Methods": "GET",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Max-Age": "86400",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.98 Safari/537.36",
    "Accept": "application/json; charset=utf-8",
}

response = requests.get(api, headers=headers).json()

games = response["data"]["Catalog"]["searchStore"]["elements"]

title_list = []
product_list = []

print("Games found in API\n")

j = 1
for game in games:
    product = {}
    product["title"] = game["title"]
    product["namespace"] = game["namespace"]
    product["id"] = game["id"]
    title_list.append(product["title"])
    product_list.append(product)
    print(f"\n{j}. {product}\n")
    j += 1

print()
print("=" * 50)
print()

# return (title_list, product_list)


# Function to search for game by name
# Pulls dictionary that contains title which matches keyword (fuzzy matching)
def query_game(keyword):
    name = extractOne(keyword, title_list, scorer=ratio, score_cutoff=75)[0]
    try:
        return next(item for item in product_list if item["title"] == name)
    except StopIteration:
        return "not found"

    #
    # ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~ #


# =================================== #
# Script to redeem free games
#
def redeem_free_games(instance):
    page = instance.tab
    logger = instance.logger

    page.wait_for_selector("//span[text()='Free Now']")
    page.wait_for_load_state("networkidle")
    name = page.query_selector("span.display-name").inner_text()
    logger.info(f"Getting free game details from '{instance.dashboard_url}'")
    logger.debug(f"Display name: {name}")
    free_games = page.query_selector_all("a[aria-label*='Free Now']")
    links = []

    for game in free_games:
        link = game.get_attribute("href")
        links.append(link)

    for link in links:
        page.goto("https://store.epicgames.com" + link)
        button = "button[data-testid='purchase-cta-button']"
        page.wait_for_selector(button)
        title = page.query_selector("h1 > div > span").inner_text()
        if page.query_selector(button).inner_text() == "GET":
            logger.debug(f"Getting game: {title}")
            game_dict = query_game(title)
            if "not found" in game_dict:
                logger.error(f"Game details not found for {title}")
            elif type(game_dict) is dict:
                # Clicking the GET button opens an iframe, which makes interaction more difficult
                # We can avoid that by directly navigating to the purchase page
                page.goto(
                    f"https://store.epicgames.com/purchase?offers=1-{game_dict['namespace']}-{game_dict['id']}&orderId&purchaseToken&showNavigation=true#/purchase/payment-methods"
                )
                order_button = "div.payment-order-confirm > button"
                page.click(order_button)

                sleep(10)

                # ++++++
                # Steps for clicking in iframe
                # try:
                #     page.keyboard.press("Tab")
                #     page.keyboard.press("Enter")
                #     page.focus("input#agree")
                #     page.keyboard.press("Enter")
                #     page.keyboard.press("Tab")
                #     page.keyboard.press("Enter")
                # except:
                #     print(
                #         f"""[1]

                #     {traceback.format_exc()}

                #     """
                #     )
                #     pass
                # try:
                #     iframe = "#webPurchaseContainer > iframe"
                #     frame = page.frame_locator(iframe)
                #     # frame = page.query_selector(iframe).content_frame()
                #     confirm = "#purchase-app div.payment-order-confirm"
                #     frame.locator(confirm).wait_for()  # defaults to state="visible"
                #     frame.locator(confirm).click("button")
                # except:
                #     print(
                #         f"""[2]

                #     {traceback.format_exc()}

                #     """
                #     )
                # ++++++
        elif "in library" in page.query_selector(button).inner_text().lower():
            logger.debug(f"Game already in library: {title}")

    #
    # =================================== #


def epic_login(instance):
    # Browser session to generate new csv log file
    with sync_playwright() as pw:
        logger = instance.logger
        instance.one_step_login(pw, "button#sign-in")
        sleep(3)
        instance.redirect(url=epic + "/store/free-games")
        redeem_free_games(instance)
        logger.info("Tasks complete. Closing browser")

    # Remove FileHandlder to prevent reopening the previous instance's file in the next instance
    # due to the Class Variable getting recreated during "self.logger.addHandler(self.DuoHandler)"
    logger.removeHandler(instance.DuoHandler)

    # Close csv file in current instance when done with writing logs
    instance.formatter.csvfile.close()


if __name__ == "__main__":
    # game_data = get_game_data()
    # title_list = game_data[0]
    # product_list = game_data[1]
    i = 1
    print("\n\nBegin logging\n")
    for user in cred_dict:
        instance = LoginLogger(
            base_url=epic,
            login_url=epic_signin,
            usr_sel=epic_usr_sel,
            usr=user,
            pwd_sel=epic_pwd_sel,
            pwd=cred_dict[user],
            homepage=epic_homepage,
            filename=mkfilename(f"epicgames_{i}"),
        )
        epic_login(instance)
        update_logs(instance)
        i += 1
