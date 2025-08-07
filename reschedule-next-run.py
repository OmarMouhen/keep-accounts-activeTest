# This script only works within Github Actions
# pip install ruamel.yaml
# ---


import os
from ruamel.yaml import YAML


# import env variable from runner's bash shell
folder = os.environ["folder"]

current_cron = []
new_cron = []

workflow_file = f"./.github/workflows/login-{folder}-auto.yml"
yaml = YAML()  # defaults to round-trip (typ="rt")

with open(workflow_file, "r") as file:
    wf = yaml.load(file)  # yaml contents loaded as a python dictionary
    schedules = wf["on"]["schedule"]

    # edit cron strings
    for schedule in schedules:
        current_cron.append(schedule["cron"])
        cron = (schedule["cron"]).split()
        new_hour = int(cron[1]) + 1
        if new_hour > 23:
            new_hour = f"0{new_hour - 24}"
        elif new_hour < 10:
            new_hour = f"0{new_hour}"
        else:
            new_hour = str(new_hour)
        cron[1] = new_hour
        cron[-1] = "*"
        cron = " ".join(cron)
        schedule["cron"] = cron
        new_cron.append(cron)

print(f"Current cron times are:\n{current_cron}\n\n")
print("\nAdding one hour...\n")
print(f"New cron times are:\n{new_cron}\n\n")

with open(workflow_file, "w") as file:
    yaml.dump(wf, file)


print(wf)
