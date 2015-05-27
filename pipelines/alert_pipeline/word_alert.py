#!/usr/local/bin/python

import csv
import datetime as dt
import httplib
import json
import operator
import re
import smtplib
import sys
from collections import defaultdict
from email.mime.text import MIMEText
from math import log, floor
from os import path, environ
from textwrap import dedent

import requests
from pytz import timezone as tz
from sqlalchemy import sql
from sqlalchemy.exc import OperationalError

from lib.database.input_db import Db as inputDb
from lib.general.counters import ItemCounterDelta
from lib.general.simplewarn import warn
from lib.language.leven import SpamDetector
from lib.language.word_types import tokenize

httplib.HTTPConnection.debuglevel = 1

_VERSION = 2 # Update this when you update stuff (ints only)
_TIMEFRAME = 12 # Hours
_PAST_TIMEFRAME = 3 # Weeks
# Constants for calculation of severity
_DIFF_PCT_MIN = 30 # Percentage increase for which we absolutely don't want to return sev.
_DIFF_ABS_MIN = 0.5 # Percentage point change for which we absolutely ignore
_DIFF_ABS_SCALE = 2 # Scaling factor between rel and abs diff
_SEV_SCALE = 8.5 # Factor by which to scale things up to fit the range.
_SEV_SUB = 2.2 # Reduce this to alert more, increase to alert less
_MAX_PCT_DIFF = 50 # Infinity throws everything off, so we're capping things. This is 
                    # per piece of feedback, which should make the 0 before, 3 after case
                    # not trigger so bad.

_MIN_COUNT_THRESHOLD = 3
_MIN_DENOM_THRESHOLD = 20

_EMAIL_SEV_MIN = 5 # Severity level above which we send email
_ALERT_SEV_MIN = 2 # Severity level above which we send alerts (-1 = send everything)
_MAX_ALERT_LINKS = 25 # Send at most this number of links
_MAX_EMAIL_LINKS = 15 # Email at most this number of links

ALERT_EMAIL_FROM = environ['ALERT_EMAIL_FROM']
ALERT_EMAIL = environ['ALERT_EMAIL']

ALERT_TOKEN = environ['ALERT_TOKEN']


def process_alerts(date = None, debug = False, debug_file = sys.stdout, email = True):
    input_db = inputDb('input_mozilla_org_new')
    
    delta = defaultdict(WordDeltaCounter)
    base_total = 0
    after_total = 0
    
    if (date is None) :
        date = dt.datetime.now()    
    if (isinstance(date, dt.datetime)):
        pass
    elif (isinstance(date, dt.date)):
        date = dt.datetime.combine(date, dt.time(0,0,0))
    
    date_string = date.strftime('%Y-%m-%d %H:%M:%S')
    date = tz('US/Pacific').localize(date)
    

    if debug:
        if not isinstance(debug_file, file):
            warn("Debug file should be type <file>, outputting to stdout instead")
            debug_file = sys.stdout

    if (not debug or debug_file != sys.stdout):
        print "Generating alerts for " + date_string

    old_data_sql = """
        SELECT description, MIN(id) as id
        FROM feedback_response fr
        WHERE
        created > DATE_SUB(:now, INTERVAL :old WEEK) AND
        created < DATE_SUB(:now, INTERVAL :new HOUR)
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
        results = input_db.execute_sql(old_data_sql, old=_PAST_TIMEFRAME, new=_TIMEFRAME, now = date_string)
    except (OperationalError):
        warn("Database timed out executing base sql.")
        #TODO: raise an alert instead of just printing.
        return
    
    for row in results:
        (word_dict, value) = tokenize(row.description, input_id = row.id)
        if value < 1:
            continue
        for (key, word_set) in word_dict.iteritems():
            if (key is None) or not re.match('\S', key):
                continue
            delta[key].base.insert(key = key, link = (row.id, value), meta = word_set)
        base_total += 1

    after_comments = dict()
    
    new_data_sql = """
        SELECT description, MIN(id) as id
        FROM feedback_response fr
        WHERE
        created > DATE_SUB(:now, INTERVAL :new HOUR) AND
        created < :now
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
        results = input_db.execute_sql(new_data_sql, new=_TIMEFRAME, now = date_string)
    except (OperationalError):
        warn("Database timed out executing after sql.")
        return

    for row in results:
        (word_dict, value) = tokenize(row.description, input_id = row.id)
        after_comments[row.id] = row.description
        if value < 1:
            continue
        for (key, word_set) in word_dict.iteritems():
            if (key is None) or not re.match('\S', key):
                continue
            delta[key].after.insert(key = key, link = (row.id, value), meta = word_set)
        after_total += 1   
    
    if (after_total < _MIN_DENOM_THRESHOLD or base_total < _MIN_DENOM_THRESHOLD):
        warn("NOT ENOUGH FEEDBACK %d before and %d after" % (base_total, after_total))
        return
    
    #Generate alerts
    
    alert_count = 0
    alerted_feedback = dict()
    
    for (k,v) in delta.iteritems():
        v.set_thresholds(diff_pct = _DIFF_PCT_MIN, diff_abs = _DIFF_ABS_MIN)
        v.set_potentials(base = base_total, after = after_total)
        v.end_time = tz('UTC').normalize(date)
        if (v.is_significant and v.severity >= _ALERT_SEV_MIN
                and v.after.count >= _MIN_COUNT_THRESHOLD):
            for link_item in v.after.link_list:
                alerted_feedback[link_item[0]] = link_item[1]
            v.alert = True
    
    test_spam = { x: after_comments[x] for x in alerted_feedback.keys() }
    spam = SpamDetector().check_entries_for_spam(test_spam)
    spam_count = len(spam.keys())
    print spam
    
    for (k,v) in delta.iteritems():
        if (v.alert):
            for s in spam.keys():
                if s in v.after.link_list:
                    v.after.remove(link = (s, alerted_feedback[s]))
                    v.alert = False
    
    after_total -= spam_count
    
    for (k,v) in delta.iteritems():
        v.set_potentials(base = base_total, after = after_total)
        if (v.is_significant and v.severity >= _ALERT_SEV_MIN
            and v.after.count >= _MIN_COUNT_THRESHOLD):
            if (not debug or debug_file != sys.stdout):
                print "Emitting alert for %s" % v.after.sorted_metadata[0]
            v.emit(debug = debug, debug_file = debug_file)
            alert_count += 1

    
    if alert_count <= 0:
        print "No alerts today"
        #This is super fishy but technically valid usecase. I guess leave it for now.
            
        # Now send an email, looking up each piece of feedback.
    if (email):
        email_list = set()
    
        for (k,v) in delta.iteritems():
            v.set_thresholds(diff_pct = _DIFF_PCT_MIN, diff_abs = _DIFF_ABS_MIN)
            if (v.is_significant and v.severity >= _EMAIL_SEV_MIN
                and v.after.count >= _MIN_COUNT_THRESHOLD):
                email_list.add(v)
        email_results(email_list, after_comments)

def email_results(email_list, after_comments):
    email_body = ''
    shortwords = []
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
        link_list = list(v.after.link_list)
        link_list.sort(key = lambda x:(x[1], x[0]), reverse=True)
        link_list = link_list[:_MAX_EMAIL_LINKS]
        for link in link_list :
            email_body += "\n<https://input.mozilla.org/dashboard/response/%s>:\n" % \
                (str(link[0]))
            if len(after_comments[link[0]]) < 500:
                email_body += after_comments[link[0]]
            else:
                email_body += after_comments[link[0]][:450] + "..."
                
        email_body += "\n\n"
        shortwords.append(v.after.sorted_metadata[0])
    
    if len(email_list) > 0:

        msg = MIMEText(email_body)
        msg['Subject'] = "[Input Alert] " + ", ".join(shortwords)
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
        self.alert = False

    @property
    def severity (self):
        """
        This function is magic. I don't know if it's the right one or if we should
        make a better one but whatever.
        """
        #TODO: experiment with other algorithms
        max_possible_count = self.after.count if (self.base.count <= 0) else 15
        pct_value = min(self.diff_pct, _MAX_PCT_DIFF * max_possible_count)
        pct_part = safe_log(pct_value - _DIFF_PCT_MIN)
        abs_part = (self.diff_abs - _DIFF_ABS_MIN)*_DIFF_ABS_SCALE
        value = _SEV_SCALE * (safe_log(abs_part + pct_part) - _SEV_SUB)
        if value < -1:
            return -1
        if value > 10:
            return 10
        return int(floor(value))
        
    def emit(self, debug = False, debug_file = sys.stdout):
        if debug:
            if isinstance(debug_file, file):
                self.log_to_csv(debug_file)
            else:
                warn("Debug file should be type <file>, outputting to stdout instead")
                self.log_to_csv(sys.stdout)
            return
        headers = {
            'content-type': 'application/json',
            'accept': 'application/json; indent=4',
            'Fjord-Authorization': 'Token ' + ALERT_TOKEN,
        }
        timediff = dt.timedelta(hours = _TIMEFRAME)
        start_time = self.end_time - timediff
        link_list = list(self.after.link_list)
        link_list.sort(key = lambda x:(x[1], x[0]), reverse=True)
        link_list = link_list[:_MAX_ALERT_LINKS]
        links = []
        for link in link_list:
            links.append({
                'name'  : 'Input Link',
                'url'   : 'http://input.mozilla.org/dashboard/response/'+str(link[0])
            })
        description = dedent("""
    
            Trending words: %s
    
            Before: %.2f/1000
            After %.2f/1000
            Absolute Difference: %.2f %%age points
            Percent Difference: %.2f %%
            Total feedback in the past %d hours: %d

        """%(
            ", ".join(self.after.sorted_metadata),
            self.base_pct * 10,
            self.after_pct * 10,
            self.diff_abs * 10,
            self.diff_pct,
            _TIMEFRAME,
            len(self.after.link_list)
            
        )).strip()
        payload = {
            'severity': self.severity,
            'summary': '%s is trending up by %.2f'%\
                (self.after.sorted_metadata[0], self.diff_pct),
            'description': description,
            'flavor': 'word-based',
            'emitter_name': 'input_word_alert',
            'emitter_version': _VERSION,
            'links': links,
            'start_time': start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }
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
            
    def log_to_csv(self, file):
        
        output = '"%s","%s",%.10f,%.10f,%d,%d,%d'%(
            self.end_time.strftime('%Y-%m-%d %H:%M:%S'),
            self.after.sorted_metadata[0],
            self.base_pct,
            self.after_pct,
            self.base.count,
            self.after.count,
            self.severity
        )
        print >> file, output
    
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
            Total feedback in the past %d hours: %d
        """%(
            self.severity,
            self.after.sorted_metadata[0],
            ", ".join(self.after.sorted_metadata),
            self.base_pct * 10,
            self.after_pct * 10,
            self.diff_abs * 10,
            self.diff_pct,
            _TIMEFRAME,
            len(self.after.link_list)
        )).strip()
        return str

def safe_log (value):
    if value <= 0:
        return 0
    return log(value)
    
def main():
    process_alerts()
    
if __name__ == '__main__':

    main()

