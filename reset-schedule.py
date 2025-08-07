# This script only works within Github Actions
# pip install ruamel.yaml
# ---


from csv import DictReader
import os
from ruamel.yaml import YAML


# import env variables from runner's bash shell
folder = os.environ["folder"]


default_cron = []
wf_cron = []


with open("default-schedule.csv", mode="r") as csv_file:
    reader = DictReader(csv_file)
    for row in reader:
        if row["Folder"] == folder:
            default_cron.append(row["Cron"])

print(f"\n\nDefault cron times for login-{folder}-auto are:\n{default_cron}\n\n")


yaml = YAML()  # defaults to round-trip (typ="rt")

workflow_file = f"./.github/workflows/login-{folder}-auto.yml"

with open(workflow_file, "r") as file:
    wf = yaml.load(file)
    schedules = wf["on"]["schedule"]
    for schedule in schedules:
        wf_cron.append(schedule["cron"])

print(f"Current cron times are:\n{wf_cron}\n\n")


if wf_cron == default_cron:
    print("\nNo reset needed.\n\n")

else:
    for schedule, Cron in zip(schedules, default_cron):
        if schedule["cron"] != Cron:
            schedule["cron"] = Cron
    print("\nSchedule has been reset.\n\n")


with open(workflow_file, "w") as file:
    yaml.dump(wf, file)


print(wf)
