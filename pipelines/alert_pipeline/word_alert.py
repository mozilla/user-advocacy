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
from textwrap import dedent
from math import log, floor
import httplib
httplib.HTTPConnection.debuglevel = 1

import operator

from collections import defaultdict
from lib.general.counters import ItemCounterDelta
from lib.language.word_types import tokenize

_TIMEFRAME = 12 # Hours
_PAST_TIMEFRAME = 3 # Weeks
# Constants for calculation severity
_DIFF_PCT_MIN = 10 # Percentage increase for which we absolutely don't want to return sev.
_DIFF_ABS_MIN = 0.5 # Percentage point change for which we absolutely ignore
_DIFF_ABS_SCALE = 70 # Scaling factor between rel and abs diff
_SEV_SCALE = 10 # Factor by which to expand the log of the product of the logs.
_SEV_SUB = 3.3 # Magic. Just magic. Deal

_MIN_COUNT_THRESHOLD = 3
_MIN_DENOM_THRESHOLD = 20

_EMAIL_SEV_MIN = 5 # Severity level above which we send email
_ALERT_SEV_MIN = 0 # Severity level above which we send alerts (-1 = send everything)

ALERT_EMAIL_FROM = environ['ALERT_EMAIL_FROM']
ALERT_EMAIL = environ['ALERT_EMAIL']

ALERT_TOKEN = environ['ALERT_TOKEN']

def main():
    input_db = Db('input')
    
    delta = defaultdict(WordDeltaCounter)
    base_total = 0
    after_total = 0
    
    old_data_sql = """
        SELECT description, MIN(id) as id
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
        GROUP BY 1
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
        SELECT description, MIN(id) as id
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
        GROUP BY 1
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
    
    if (after_total < _MIN_DENOM_THRESHOLD or base_total < _MIN_DENOM_THRESHOLD):
        warn("NOT ENOUGH FEEDBACK %d before and %d after" % (base_total, after_total))
        print "NOT ENOUGH FEEDBACK %d before and %d after" % (base_total, after_total)
        return
    
    #Generate alerts
    
    alert_count = 0
    
    for (k,v) in delta.iteritems():
        v.set_thresholds(diff_pct = _DIFF_PCT_MIN, diff_abs = _DIFF_ABS_MIN)
        v.set_potentials(base = base_total, after = after_total)
        if (v.is_significant and v.severity >= _ALERT_SEV_MIN 
            and v.after.count >= _MIN_COUNT_THRESHOLD):
            print "Emitting alert for %s" % v.after.sorted_metadata[0]
            alert_count += 1
            emit_alert(v)
    
    if alert_count <= 0:
        print "No alerts today"
            
    # Now send an email, looking up each piece of feedback.
    email_list = set()
    
    for (k,v) in delta.iteritems():
        v.set_thresholds(diff_pct = _DIFF_PCT_MIN, diff_abs = _DIFF_ABS_MIN)
        if (v.is_significant and v.severity >= _EMAIL_SEV_MIN
            and v.after.count >= _MIN_COUNT_THRESHOLD):
            email_list.add(v)
    email_results(email_list)

def email_results(email_list):
    input_db = Db('input')
    email_body = ''
    shortwords = []
    
    rfr = input_db.get_table('remote_feedback_response')
        
    for v in email_list:
        email_body += "===== Lvl %d ALERT FOR %s: =====\n" % (
            v.severity,
            v.after.sorted_metadata[0]
            )
        email_body += "Words: " + ", ".join(v.after.sorted_metadata)
        email_body += "\n\n"
        email_body += "Before: %.2f/1000; After %.2f/1000; Diff: %.2f; %%diff: %.2f"\
            % (                
                v.base_pct * 10,
                v.after_pct * 10,
                v.diff_abs * 10,
                v.diff_pct
            )
        email_body += "\n\nInput Links:"
        for link_id in v.after.link_list :
            comment_sql = sql.select([rfr.c.description]).where(rfr.c.id == link_id)
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

        msg = MIMEText(email_body)
        msg['Subject'] = "Alert for: " + ", ".join(shortwords)
        msg['From'] = ALERT_EMAIL_FROM
        msg['To'] = ALERT_EMAIL
        server = smtplib.SMTP('localhost')
        server.sendmail(ALERT_EMAIL_FROM, ALERT_EMAIL.split(','), msg.as_string())
        server.quit()


def emit_alert (v):
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json; indent=4',
        'Fjord-Authorization': 'Token ' + ALERT_TOKEN,
    }
    links = []
    for link_id in v.after.link_list:
        links.append({
            'name'  : 'Input Link',
            'url'   : 'http://input.mozilla.org/dashboard/response/'+str(link_id)
        })
    description = dedent("""
    
        Trending words: %s
    
        Before: %.2f/1000
        After %.2f/1000
        Absolute Difference: %.2f %%age points
        Percent Difference: %.2f %%
        
    """%(
        ", ".join(v.after.sorted_metadata),
        v.base_pct * 10,
        v.after_pct * 10,
        v.diff_abs * 10,
        v.diff_pct
    )).strip()
    payload = {
        'severity': v.severity,
        'summary': '%s is trending up by %.2f'%(v.after.sorted_metadata[0], v.diff_pct),
        'description': description,
        'flavor': 'word-based',
        'emitter_name': 'input_word_alert',
        'emitter_version': 0,
        'links': links
    }  
    print "Headers", headers
    resp = requests.post(
        'https://input.mozilla.org/api/v1/alerts/alert/',
        data=json.dumps(payload),
        headers=headers
    )
    if resp.status_code == 201:
        print "All systems good. Submitted alert for %s" % (v.after.sorted_metadata[0])
    else:
        print "Failed to submit alert for %s" % (v.after.sorted_metadata[0])
        print resp.json()['detail']
    
class WordDeltaCounter (ItemCounterDelta):
    @property
    def severity (self):
        """
        This function is magic. I don't know if it's the right one or if we should
        make a better one but whatever.
        """
        pct_part = safe_log(self.diff_pct - _DIFF_PCT_MIN)
        abs_part = safe_log((self.diff_abs - _DIFF_ABS_MIN)*_DIFF_ABS_SCALE)
        value = _SEV_SCALE * (safe_log(abs_part * pct_part) - _SEV_SUB)
        if value < -1:
            return -1
        if value > 10:
            return 10
        return floor(value)
        
def safe_log (value):
    if value <= 0:
        return 0
    return log(value)
    
if __name__ == '__main__':

    main()

