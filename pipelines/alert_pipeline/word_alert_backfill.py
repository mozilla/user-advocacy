#!/usr/local/bin/python

import sys
from os import path, environ
from lib.database.backend_db import Db
import csv
import json
import requests
import datetime as dt
from lib.general.simplewarn import warn
import smtplib
from email.mime.text import MIMEText
from sqlalchemy import sql
from textwrap import dedent
from math import log, floor
import httplib
httplib.HTTPConnection.debuglevel = 1
from sqlalchemy.exc import OperationalError
from pytz import timezone as tz
from pipelines.alert_pipeline.word_alert import WordDeltaCounter, safe_log, process_alerts

import operator

from collections import defaultdict
from lib.language.word_types import tokenize

_DEBUG = 0
_DEBUG_OUT_FILE = 'alert_backfill.txt'
_START_DATE = '2015-01-01'


def main():
    date = dt.datetime.strptime(_START_DATE, '%Y-%m-%d')
    now = dt.datetime.now()
    increment = dt.timedelta(days = 1)
    times = [dt.time(0), dt.time(6), dt.time(12), dt.time(18)]
    if _DEBUG:
        file = open(_DEBUG_OUT_FILE, 'a')
        print >> file, "end_time,word,base_pct,after_pct,base_count,after_count,severity\n"
    while(date < now):
        for time in times:
            dt_to_run = dt.datetime.combine(date.date(), time)
            if (dt_to_run < now):
                # print dt_to_run.isoformat()
                process_alerts(dt_to_run, debug = _DEBUG, debug_file = file, 
                                email = False)
        date += increment
    if _DEBUG:
        file.close()



if __name__ == '__main__':
    main()
