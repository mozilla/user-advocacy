#!/usr/local/bin/python

import csv
import httplib
import json
import operator
import re
import smtplib
import sys
from collections             import defaultdict
from datetime                import date,datetime,time,timedelta
from email.mime.text         import MIMEText
from math                    import log, floor
from os                      import path, environ
from textwrap                import dedent

import requests
from argparse                import ArgumentParser
from pytz                    import timezone as tz
from sqlalchemy              import sql
from sqlalchemy.exc          import OperationalError

from lib.database.input_db   import Db as inputDb
from lib.general.counters    import ItemCounterDelta
from lib.general.simplewarn  import warn
from lib.language.leven      import SpamDetector
from lib.language.word_types import tokenize

httplib.HTTPConnection.debuglevel = 1

# Constants for tuning
_VERSION             = 2   # Update this when you update stuff (ints only)
_DESKTOP_TIMEFRAME   = 12  # Hours
_ANDROID_TIMEFRAME   = 24  # Hours
_PAST_TIMEFRAME      = 3   # Weeks

# Constants for calculation of severity
_DIFF_PCT_MIN        = 30  # Percentage increase for which we absolutely don't 
                           #   want to return sev.
_DIFF_ABS_MIN        = 0.5 # Percentage point change for which we absolutely 
                           #   ignore
_DIFF_ABS_SCALE      = 2   # Scaling factor between rel and abs diff
_SEV_SCALE           = 8.5 # Factor for scaling things up to fit the range.
_SEV_SUB             = 2.2 # Reduce this to alert more, increase to alert less
_MAX_PCT_DIFF        = 50  # Infinity throws everything off, so we're capping 
                           #   things. This is per piece of feedback, which should 
                           #   make the 0 before, 3 after case not trigger so bad.
_MIN_COUNT_THRESHOLD = 3
_MIN_DENOM_THRESHOLD = 20
_EMAIL_SEV_MIN       = 5   # Severity level above which we send email
_ALERT_SEV_MIN       = 2   # Severity level above which we send alerts 
                           #   (-1 = send everything)
_MAX_ALERT_LINKS     = 25  # Send at most this number of links
_MAX_EMAIL_LINKS     = 15  # Email at most this number of links

# Environment vars
_ALERT_EMAIL_FROM    = environ['ALERT_EMAIL_FROM']
_DESKTOP_EMAIL       = environ['ALERT_EMAIL']
_ANDROID_EMAIL       = environ['ANDROID_ALERT_EMAIL']
_ALERT_TOKEN         = environ['ALERT_TOKEN']

# Database
_INPUT_DB            = None


def process_alerts(product, 
                   now = datetime.now(), old = _PAST_TIMEFRAME, new = None, 
                   debug = False, debug_file = sys.stdout,
                   email = True, address = None):
    delta = defaultdict(WordDeltaCounter)
    
    # Resolve date
    if not isinstance(now, datetime) and isinstance(now, date):
        now = datetime.combine(now, time(0,0,0))
    #if not isinstance(now, datetime): 
        # I don't feel like checking this. It's not a likely exception.
        #raise Exception('"now" must me of type datetime or date.')
    
    now_string = now.strftime('%Y-%m-%d %H:%M:%S')
    now = tz('US/Pacific').localize(now)

    # Product related vars
    product = product.lower()
    if product == 'desktop':
        new           = new if new else _DESKTOP_TIMEFRAME
        where_product = ('product = "firefox"' + 
                         '\nAND LEFT(platform,7) IN("Windows","OS X","Linux")')
        flavor        = 'word-based'
        subject       = 'Desktop Input Alert'
        address       = address if address else _DESKTOP_EMAIL
    elif product == 'android':
        new           = new if new else _ANDROID_TIMEFRAME
        where_product = 'product LIKE "Firefox for Android"'
        flavor        = 'android-word-based'
        subject       = 'Android Input Alert'
        address       = address if address else _ANDROID_EMAIL
    else:
        raise Exception('product must be "desktop" or "android".')

    # Resolve debug info
    if debug and not isinstance(debug_file, file):
            warn('Debug file should be type <file>, outputting to stdout.')
            debug_file = sys.stdout
    if not debug or debug_file != sys.stdout:
        print 'Generating %s for %s' % (subject, now_string)

    # Retrieve old timeframe
    where = (where_product + 
             '\nAND created > DATE_SUB(:now, INTERVAL :old WEEK)' + 
             '\nAND created < DATE_SUB(:now, INTERVAL :new HOUR)')
    base_total = _aggregate(where, delta, True, now_string, old, new)
    
    # Retrieve new timeframe
    after_comments = {}
    where = (where_product + 
             '\nAND created > DATE_SUB(:now, INTERVAL :new HOUR)' + 
             '\nAND created < :now')
    after_total = _aggregate(where, delta, False, now_string, old, new,
                             comments = after_comments)
    
    if (after_total < _MIN_DENOM_THRESHOLD or
                base_total < _MIN_DENOM_THRESHOLD):
        warn('NOT ENOUGH FEEDBACK %d before and %d after' % (base_total, 
                                                             after_total))
        return


    #Generate alerts
    
    alerted_feedback = {}
    
    # Determine if we should alert for each word and add the alert feedback to a 
    # dict for spam detection
    for (k,v) in delta.iteritems():
        v.set_thresholds(diff_pct = _DIFF_PCT_MIN, diff_abs = _DIFF_ABS_MIN)
        v.set_potentials(base = base_total, after = after_total)
        v.end_time = tz('UTC').normalize(now)
        if (v.is_significant and v.severity >= _ALERT_SEV_MIN
                and v.after.count >= _MIN_COUNT_THRESHOLD):
            for link_item in v.after.link_list:
                alerted_feedback[link_item[0]] = link_item[1]
            v.alert = True

    # Find spam
    test_spam = { x: after_comments[x] for x in alerted_feedback.keys() }
    spam = SpamDetector().check_entries_for_spam(test_spam)
    # Remove spam
    after_total -= len(spam.keys())
    for (k,v) in delta.iteritems():
        if (v.alert):
            for s in spam.keys():
                if s in v.after.link_list:
                    v.after.remove(link = (s, alerted_feedback[s]))
                    v.alert = False
    
    # Reprocess alerts while removing spam
    has_alerts = False
    for (k,v) in delta.iteritems():
        v.set_potentials(base = base_total, after = after_total)
        if (v.is_significant and v.severity >= _ALERT_SEV_MIN
            and v.after.count >= _MIN_COUNT_THRESHOLD):
            if (not debug or debug_file != sys.stdout):
                print 'Emitting alert for %s' % v.after.sorted_metadata[0]
            v.emit(debug = debug, flavor = flavor, debug_file = debug_file)
            has_alerts = True

    if not has_alerts:
        # This is super fishy but technically valid usecase.
        # Might alert on this in the future
        print 'No alerts today'
        return

    # Now send an email, looking up each piece of feedback.
    if email:
        email_list = set()
    
        for (k,v) in delta.iteritems():
            v.set_thresholds(diff_pct = _DIFF_PCT_MIN, diff_abs = _DIFF_ABS_MIN)
            if (v.is_significant and v.severity >= _EMAIL_SEV_MIN
                and v.after.count >= _MIN_COUNT_THRESHOLD):
                email_list.add(v)
        _email_results(email_list, subject, address, after_comments)


def _aggregate(where, delta, is_base, now,
               old, new, comments = None):
    global _INPUT_DB
    _INPUT_DB = _INPUT_DB if _INPUT_DB else inputDb('input_mozilla_org_new') 

    sql = '''
        SELECT
            description,
            id
        FROM feedback_response fr
        WHERE
            %s
            AND locale = "en-US"
            AND happy = 0
            AND (campaign IS NULL OR campaign = "")
            AND (source   IS NULL OR source   = "")
            AND (version NOT RLIKE "[^a.0-9]")
        ;
    ''' % where
    try:
        results = _INPUT_DB.execute_sql(sql, old = old, new = new, 
                                       now = now)
    except (OperationalError):
        #TODO(rrayborn): raise an alert instead of just warning.
        warn('Database timed out executing base sql.')
        return

    total = 0
    for row in results:
        # Tokenize the row into delta and store comments for retreival in comments
        (word_dict, value) = tokenize(row.description, input_id = row.id)
        if comments is not None:
            comments[row.id] = row.description
        if value > 0:
            for (key, word_set) in word_dict.iteritems():
                if (key is None) or not re.match('\S', key):
                    continue
                data_set = delta[key].base if is_base else delta[key].after
                data_set.insert(key = key, link = (row.id, value),
                                meta = word_set)
            total += 1   
    return total


def _email_results(email_list, subject, address, after_comments):
    if len(email_list) == 0:
        return

    # Create email body

    email_body = ''
    shortwords = []
    for v in email_list:
        email_body += '===== Lvl %d ALERT FOR %s: =====\n' % (
            v.severity,
            v.after.sorted_metadata[0]
            )
        email_body += 'Words: %s\n\n' % (', '.join(v.after.sorted_metadata)) + \
                'Before: %.2f/1000;'  % (v.base_pct * 10) + \
                'After %.2f/1000; '   % (v.after_pct * 10) + \
                'Diff: %.2f; '        % (v.diff_abs * 10) + \
                '%%diff: %.2f'        % (v.diff_pct) + \
                '\n\nInput Links:'

        link_list = list(v.after.link_list)
        link_list.sort(key = lambda x:(x[1], x[0]), reverse=True)
        link_list = link_list[:_MAX_EMAIL_LINKS]
        for link in link_list :
            email_body += '\n<https://input.mozilla.org/dashboard/response/%s>:\n' % \
                (str(link[0]))
            if len(after_comments[link[0]]) < 500:
                email_body += after_comments[link[0]]
            else:
                email_body += after_comments[link[0]][:450] + '...'
                
        email_body += '\n\n'
        shortwords.append(v.after.sorted_metadata[0])
    
    # Create email
    msg = MIMEText(email_body)
    msg['Subject'] = '[' + subject + '] ' + ', '.join(shortwords)
    msg['From']    = _ALERT_EMAIL_FROM
    msg['To']      = address
    
    server = smtplib.SMTP('localhost')
    server.sendmail(_ALERT_EMAIL_FROM, address.split(','), msg.as_string())
    server.quit()

    
class WordDeltaCounter (ItemCounterDelta):

    def __init__ (self, *args, **kwargs):
        super(WordDeltaCounter, self).__init__(*args, **kwargs)
        now = datetime.utcnow()
        now = tz('UTC').localize(now)
        self.end_time = now - (timedelta(microseconds=now.microsecond))
        self.alert = False

    @property
    def severity (self):
        '''
        This function is magic. I don't know if it's the right one or if we should
        make a better one but whatever.
        '''
        #TODO(rrayborn): experiment with other algorithms
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
        
    def emit(self, flavor = 'unknown', debug = False, debug_file = sys.stdout):
        if debug:
            if isinstance(debug_file, file):
                self.log_to_csv(debug_file)
            else:
                warn('Debug file should be type <file>, outputting to stdout instead')
                self.log_to_csv(sys.stdout)
            return
        headers = {
            'content-type': 'application/json',
            'accept': 'application/json; indent=4',
            'Fjord-Authorization': 'Token ' + _ALERT_TOKEN,
        }
        timediff = timedelta(hours = _TIMEFRAME)
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
        description = dedent('''
    
            Trending words: %s
    
            Before: %.2f/1000
            After %.2f/1000
            Absolute Difference: %.2f %%age points
            Percent Difference: %.2f %%
            Total feedback in the past %d hours: %d

        '''%(
            ', '.join(self.after.sorted_metadata),
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
            'flavor': flavor,
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
            print 'All systems good. Submitted alert for %s' % \
                (self.after.sorted_metadata[0])
        else:
            print 'Failed to submit alert for %s' % (self.after.sorted_metadata[0])
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
        repr = 'Word counter object for %s with %d before and %d after counts'%\
            (self.key, self.base.count, self.after.count)
        return repr
        
    def __str__(self):
        str = dedent('''
            Severity %d counter for %s.
            Words: %s
            Before: %.2f/1000
            After %.2f/1000
            Absolute Difference: %.2f %%age points
            Percent Difference: %.2f %%
            Total feedback in the past %d hours: %d
        '''%(
            self.severity,
            self.after.sorted_metadata[0],
            ', '.join(self.after.sorted_metadata),
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
    parser = ArgumentParser(description='Input Alerts.')
    parser.add_argument('--product',
                        action = 'store',
                        default = 'desktop', 
                        help = 'Product to backfill for. e.g. "desktop"/"android"')
    args = parser.parse_args()
    process_alerts(args.product)
    

if __name__ == '__main__':

    main()

