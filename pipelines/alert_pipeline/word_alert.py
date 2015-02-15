#!/usr/local/bin/python

import sys
from os import path, environ
from lib.database.backend_db import Db
import csv
import json
import requests
import datetime
from warnings import warn
import smtplib
from email.mime.text import MIMEText
from sqlalchemy import sql

import operator

from collections import defaultdict
from lib.general.counters import ItemCounterDelta
from lib.language.word_types import tokenize

_TIMEFRAME = 12 # Hours
_PAST_TIMEFRAME = 3 # Weeks
_DIFF_PERCENT = 100 # Percentage increase (0 for any increase)
_DIFF_ABS = 5 # Percentage point change

def main():
    input_db = Db('input')
    
    delta = defaultdict(ItemCounterDelta)
    base_total = 0
    after_total = 0
    
    old_data_sql = """
        SELECT description, id
        FROM remote_feedback_response fr
        WHERE
        created > DATE_SUB(NOW(), INTERVAL :old WEEK) AND
        created < DATE_SUB(NOW(), INTERVAL :new HOUR)
        AND product LIKE 'firefox'
        AND locale = 'en-US'
        AND happy = 0
        AND (campaign IS NULL or campaign = '')
        AND (source IS NULL or source = '')
        AND (version NOT RLIKE '[^a.0-9]')
        AND (platform LIKE 'Windows%' OR platform LIKE 'OS X' OR platform LIKE 'Linux')
    """
    try:
        results = input_db.execute_sql(old_data_sql, old=_PAST_TIMEFRAME, new=_TIMEFRAME)
    except (OperationalError):
        print "Database timed out executing base sql."
        return
    
    for row in results:
        (word_dict, value) = tokenize(row.description)
        if value == 0:
            continue
        for (key, word_set) in word_dict.iteritems():
            delta[key].base.insert(key = key, link = row.id, meta = word_set)
        base_total += 1

    new_data_sql = """
        SELECT description, id
        FROM remote_feedback_response fr
        WHERE
        created > DATE_SUB(NOW(), INTERVAL :new HOUR) AND
        created < NOW()
        AND product LIKE 'firefox'
        AND locale = 'en-US'
        AND happy = 0
        AND (campaign IS NULL or campaign = '')
        AND (source IS NULL or source = '')
        AND (version NOT RLIKE '[^a.0-9]')
        AND (platform LIKE 'Windows%' OR platform LIKE 'OS X' OR platform LIKE 'Linux')
    """
    
    try:
        results = input_db.execute_sql(new_data_sql, new=_TIMEFRAME)
    except (OperationalError):
        print "Database timed out executing after sql."
        return

    for row in results:
        (word_dict, value) = tokenize(row.description)
        if value == 0:
            continue
        for (key, word_set) in word_dict.iteritems():
            delta[key].after.insert(key = key, link = row.id, meta = word_set)
        after_total += 1
    
    email_list = set()
    
    for (k,v) in delta.iteritems():
        v.set_thresholds(diff_pct = _DIFF_PERCENT, diff_abs = _DIFF_ABS)
        v.set_potentials(base = base_total, after = after_total)
        if v.is_significant:
            print "ALERT FOR %s: Before: %.2f/1000; After %.2f/1000; "\
                  "Diff: %.2f; %%diff: %.2f" % (
                ', '.join(v.after.sorted_metadata[0:3]),
                v.base_pct * 10,
                v.after_pct * 10,
                v.diff_abs * 10,
                v.diff_pct
            )
            email_list.add(v)
    
    email_body = ''
    shortwords = []
    
    rfr = input_db.get_table('remote_feedback_response')
    comment_sql = sql.select([rfr.c.description]).where(rfr.c.id == link_id)
        
    for v in email_list:
        email_body += "===== ALERT FOR %s: =====\n" % (v.after.sorted_metadata[0])
        email_body += "Words: " + ", ".join(v.after.sorted_metadata)
        email_body += "Before: %.2f/1000; After %.2f/1000; Diff: %.2f; %%diff: %.2f\n"\
            % (                
                v.base_pct * 10,
                v.after_pct * 10,
                v.diff_abs * 10,
                v.diff_pct
            )
        email_body += "Input Links:"
        for link_id in v.after.link_list :
            email_body += "\n<https://input.mozilla.org/dashboard/response/%s>:\n" % \
                (str(link_id))
            try:
                rows = input_db.execute(comment_sql)
                for item in rows:
                if len(item.description) < 500:
                    email_body += item.description
                else:
                    email_body += item.description[:450] + "..."
                rows.close()

            except (OperationalError):
                email_body = "<DB timeout fetching this input.>"
                
        email_body += "\n\n"
        shortwords.append(v.after.sorted_metadata[0])
    
    if len(email_list) > 0:
        email_from = environ['ALERT_EMAIL_FROM']
        email_to = environ['ALERT_EMAIL']
    
        msg = MIMEText(email_body)
        msg['Subject'] = "Alert for: " + ", ".join(shortwords)
        msg['From'] = email_from
        msg['To'] = email_to
        server = smtplib.SMTP('localhost')
        server.sendmail(email_from, email_to.split(','), msg.as_string())
        server.quit()
    
    print "Run complete. %d alerts issued. %d before and %d after comments processed." % \
        (len(email_list), before_total, after_total)
    

if __name__ == '__main__':

    main()

