"""
Run this script in your local machine.

Ideally have one source file for each platform

Please ensure your source files are in this
comma-delimited format before continuing:

,,USR,PWD
1,user@example.com,password1
2,user2@example.com,password2
3,abc@xyz.com,password3

Outputs:
A text file containing a single JSON string in the format
{"user@example.com": "password1", "user2@example.com": "password2", "abc@xyz.com": "password3"}
for each platform
"""


from os import listdir
import json
from csv import DictReader


def find_csv_filenames(path_to_dir=".", suffix=".csv"):
    filenames = listdir(path_to_dir)
    return [filename for filename in filenames if filename.endswith(suffix)]


source_files = find_csv_filenames()

print(
    f"""
    >>> Will read from {source_files}"""
)

for source_file in source_files:
    dest_file = f'{source_file.split(".")[0]}.txt'

    cred_dict = {}
    with open(source_file, mode="r") as csv_file:
        reader = DictReader(csv_file)
        for row in reader:
            cred_dict[(row["USR"]).strip()] = row["PWD"].strip()

    cred_str = json.dumps(cred_dict)

    with open(dest_file, "w") as text_file:
        text_file.write(cred_str)

    print(
        f"""
    >>> Opening {source_file}...
    >>> Written to {dest_file}:

    {cred_str}
    """
    )
