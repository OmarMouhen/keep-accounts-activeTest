# pip install playwright
# playwright install firefox
# pip install python-dotenv

import sys
sys.dont_write_bytecode = True

import os
import json
import time
import atexit
from datetime import datetime
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright
from logging_formatter import Year
from login_logger import LoginLogger
from log_concat import update_logs

load_dotenv()

cred_dict = json.loads(os.getenv("MEGA"))

# Load completed users if checkpoint exists
completed_file = "completed.txt"
completed_users = set()
if os.path.exists(completed_file):
    with open(completed_file, "r") as f:
        completed_users = {line.strip() for line in f}

# Filter out already completed accounts
cred_dict = {user: pwd for user, pwd in cred_dict.items() if user not in completed_users}

mega = "https://mega.nz/"
mega_signin = mega + "login"
mega_usr_sel = "input#login-name2"
mega_pwd_sel = "input#login-password2"
mega_homepage = "https://mega.nz/fm/recents"

def mkfilename(base="mega_session"):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return f"[{Year}] {base}_{timestamp}.csv"

def query_mega_storage(instance):
    page = instance.tab
    logger = instance.logger
    page.wait_for_selector("div.account.left-pane.info-block.backup-button")
    name = page.query_selector("div.membership-big-txt.name").inner_text()
    email = page.query_selector("div.membership-big-txt.email").inner_text()
    plan = page.query_selector("div.account.membership-plan").inner_text()
    logger.info(f"Getting storage details from '{instance.dashboard_url}'")
    logger.debug(f"Profile name: {name}")
    logger.debug(f"Email: {email}")
    logger.debug(f"Plan: {plan}")
    for category in page.query_selector_all("div.account.item-wrapper"):
        label = category.query_selector("div.account.progress-title > span").inner_text()
        value = category.query_selector("div.account.progress-size.small").inner_text()
        logger.debug(f"{label}: {value}")

def mega_login(instance):
    with sync_playwright() as pw:
        logger = instance.logger
        try:
            instance.one_step_login(pw, "#login_form button.login-button")
            instance.redirect(href_sel="a.mega-component.to-my-profile.nav-elem.text-only.link")
            query_mega_storage(instance)
            logger.info("Tasks complete. Closing browser.")
        except Exception as e:
            logger.error(f"Exception during login flow: {e}")
        finally:
            instance.logger.removeHandler(instance.DuoHandler)
            instance.formatter.csvfile.close()
            update_logs(instance)  # Consolidate partial logs

# === MAIN === #
success_list = []
failure_list = []
session_log_filename = mkfilename("mega_session")

summary_lines = []

try:
    for i, user in enumerate(cred_dict, 1):
        print(f"\n===> [{i}] Logging in as: {user}")
        instance = None
        try:
            instance = LoginLogger(
                base_url=mega,
                login_url=mega_signin,
                usr_sel=mega_usr_sel,
                usr=user,
                pwd_sel=mega_pwd_sel,
                pwd=cred_dict[user],
                homepage=mega_homepage,
                filename=session_log_filename,
            )
            atexit.register(lambda inst=instance: inst.formatter.csvfile.close() if inst else None)

            mega_login(instance)
            print(f"===> [{i}] ✅ Login completed for: {user}")
            success_list.append(user)

            # Save to checkpoint
            with open(completed_file, "a") as f:
                f.write(f"{user}\n")

        except Exception as e:
            print(f"===> [{i}] ❌ Failed login for {user}: {e}")
            failure_list.append(user)
        time.sleep(5)

except KeyboardInterrupt:
    print("\n🛑 Script interrupted by user.")

finally:
    # === Final Summary === #
    summary_lines = []
    summary_lines.append("=" * 60)
    summary_lines.append("✅ Successfully logged in to:")
    summary_lines += [f"   - {acc}" for acc in success_list] if success_list else ["   (none)"]

    summary_lines.append("\n❌ Failed to log in to:")
    if failure_list:
        for acc, reason in failure_list:
            summary_lines.append(f"   - {acc} → Reason: {reason}")
    else:
        summary_lines.append("   (none)")

    summary_lines.append("=" * 60)

    print("\n" + "\n".join(summary_lines))

    with open("summary.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(summary_lines))

    print("\n📄 Summary saved to 'summary.txt'")
    print(f"📁 Logs saved to: {session_log_filename}")
