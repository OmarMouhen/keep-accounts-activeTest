import sys

sys.dont_write_bytecode = True

from datetime import datetime, timezone
import logging
import csv
import io
import os


def get_datetime():
    datetimestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S:%f")
    return datetimestamp


def get_datestamp():
    datestamp = get_datetime().split()[0]
    return datestamp


def get_timestamp():
    timestamp = get_datetime().split()[1]
    return timestamp


def get_year():
    year = get_datestamp().split("-")[0]
    return year


Year = get_year()


# Inspired by this discussion topic:
# https://stackoverflow.com/questions/19765139/what-is-the-proper-way-to-do-logging-in-csv-file
class CsvFormatter(logging.Formatter):
    def __init__(self, filename="temp"):
        super().__init__()  # calls the init method of the Formatter class
        self.output = io.StringIO()
        self.filename = filename
        self.fieldnames = ["Date", "Time", "Level", "Message"]
        self.csvfile = None

        # Serves as FileHandler
        # ----------------------------- #
        if os.path.isfile(self.filename):
            self.csvfile = open(self.filename, "a+", newline="", encoding="utf-8")
            self.file_writer = csv.DictWriter(
                self.csvfile,
                quoting=csv.QUOTE_ALL,
                fieldnames=self.fieldnames,
                extrasaction="ignore",
            )
        else:
            self.csvfile = open(self.filename, "w+", newline="", encoding="utf-8")
            self.file_writer = csv.DictWriter(
                self.csvfile,
                quoting=csv.QUOTE_ALL,
                fieldnames=self.fieldnames,
                extrasaction="ignore",
            )
            self.file_writer.writeheader()
        # ----------------------------- #

        # Serves as StreamHandler
        self.console_writer = csv.writer(
            self.output, quoting=csv.QUOTE_MINIMAL, delimiter="\t"
        )

    def format(self, record):
        # Store datetime objects as variables to synchronise timestamps on both writers
        Date = get_datestamp()
        Time = get_timestamp()
        self.file_writer.writerow(
            dict(
                Date=Date,
                Time=Time,
                Level=record.levelname,
                Message=record.msg,
            )
        )
        self.console_writer.writerow([Date, Time, record.levelname, record.msg])
        data = self.output.getvalue()
        self.output.truncate(0)
        self.output.seek(0)
        return data.strip()
