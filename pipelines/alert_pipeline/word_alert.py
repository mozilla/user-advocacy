#!/usr/local/bin/python

import sys
from os import path, environ
from lib.database.backend_db import Db
import csv
import json
import requests
import datetime as dt
from warnings import warn
import smtplib
from email.mime.text import MIMEText
from sqlalchemy import sql
from textwrap import dedent
from math import log, floor
import httplib
httplib.HTTPConnection.debuglevel = 1
from pytz import timezone as tz

import operator

from collections import defaultdict
from lib.general.counters import ItemCounterDelta
from lib.language.word_types import tokenize

_TIMEFRAME = 12 # Hours
_PAST_TIMEFRAME = 3 # Weeks
# Constants for calculation of severity
_DIFF_PCT_MIN = 30 # Percentage increase for which we absolutely don't want to return sev.
_DIFF_ABS_MIN = 0.5 # Percentage point change for which we absolutely ignore
_DIFF_ABS_SCALE = 2 # Scaling factor between rel and abs diff
_SEV_SCALE = 8.5 # Factor by which to scale things up to fit the range.
_SEV_SUB = 2 # Reduce this to alert more, increase to alert less
_MAX_PCT_DIFF = 10000 # Infinity throws everything off, so we're capping things.

_MIN_COUNT_THRESHOLD = 3
_MIN_DENOM_THRESHOLD = 20

_EMAIL_SEV_MIN = 5 # Severity level above which we send email
_ALERT_SEV_MIN = 2 # Severity level above which we send alerts (-1 = send everything)

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
        #TODO: raise an alert instead of just printing.
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
        #TODO: raise an alert instead of just printing.
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
        #TODO: raise an alert instead of just printing.
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
            v.emit()
    
    if alert_count <= 0:
        print "No alerts today"
        #This is super fishy but technically valid usecase. I guess leave it for now.
            
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

    
class WordDeltaCounter (ItemCounterDelta):

    def __init__ (self, *args, **kwargs):
        super(WordDeltaCounter, self).__init__(*args, **kwargs)
        now = dt.datetime.utcnow()
        now = tz('UTC').localize(now)
        self.end_time = now - (dt.timedelta(microseconds=now.microsecond))

    @property
    def severity (self):
        """
        This function is magic. I don't know if it's the right one or if we should
        make a better one but whatever.
        """
        #TODO: experiment with other algorithms
        pct_value = min(self.diff_pct, _MAX_PCT_DIFF)
        pct_part = safe_log(self.diff_pct - _DIFF_PCT_MIN)
        abs_part = (self.diff_abs - _DIFF_ABS_MIN)*_DIFF_ABS_SCALE
        value = _SEV_SCALE * (safe_log(abs_part + pct_part) - _SEV_SUB)
        if value < -1:
            return -1
        if value > 10:
            return 10
        return int(floor(value))
        
    def emit(self):
        headers = {
            'content-type': 'application/json',
            'accept': 'application/json; indent=4',
            'Fjord-Authorization': 'Token ' + ALERT_TOKEN,
        }
        timediff = dt.timedelta(hours = _TIMEFRAME)
        start_time = self.end_time - timediff
        links = []
        for link_id in self.after.link_list:
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
            ", ".join(self.after.sorted_metadata),
            self.base_pct * 10,
            self.after_pct * 10,
            self.diff_abs * 10,
            self.diff_pct
        )).strip()
        payload = {
            'severity': self.severity,
            'summary': '%s is trending up by %.2f'%\
                (self.after.sorted_metadata[0], self.diff_pct),
            'description': description,
            'flavor': 'word-based',
            'emitter_name': 'input_word_alert',
            'emitter_version': 1,
            'links': links,
            'start_time': start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }  
        print "Headers", headers
        resp = requests.post(
            'https://input.mozilla.org/api/v1/alerts/alert/',
            data=json.dumps(payload),
            headers=headers
        )
        if resp.status_code == 201:
            print "All systems good. Submitted alert for %s" % \
                (self.after.sorted_metadata[0])
        else:
            print "Failed to submit alert for %s" % (self.after.sorted_metadata[0])
            print resp.json()['detail']
            
    def __repr__(self):
        repr = "Word counter object for %s with %d before and %d after counts"%\
            (self.key, self.base.count, self.after.count)
        return repr
        
    def __str__(self):
        str = dedent("""
            Severity %d counter for %s.
            Words: %s
            Before: %.2f/1000
            After %.2f/1000
            Absolute Difference: %.2f %%age points
            Percent Difference: %.2f %%
            Total links: %d
        """%(
            self.severity,
            self.after.sorted_metadata[0],
            ", ".join(self.after.sorted_metadata),
            self.base_pct * 10,
            self.after_pct * 10,
            self.diff_abs * 10,
            self.diff_pct,
            len(self.after.link_list)
        )).strip()
        return str

    
        
def safe_log (value):
    if value <= 0:
        return 0
    return log(value)
    
if __name__ == '__main__':

    main()

