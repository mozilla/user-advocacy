#!/usr/local/bin/python

import sys
from os import path
from lib.database.backend_db import Db
import csv
import json
import requests
import datetime
from warnings import warn

import operator

from collections import defaultdict
from lib.general.counters import ItemCounterDelta
from lib.language.word_types import tokenize

_TIMEFRAME = 12 # Hours
_PAST_TIMEFRAME = 3 # Weeks
_DIFF_PERCENT = 100
_DIFF_ABS = 5

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
    
    results = input_db.execute_sql(old_data_sql, old=_PAST_TIMEFRAME, new=_TIMEFRAME)
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
    
    results = input_db.execute_sql(new_data_sql, new=_TIMEFRAME)

    for row in results:
        (word_dict, value) = tokenize(row.description)
        if value == 0:
            continue
        for (key, word_set) in word_dict.iteritems():
            delta[key].after.insert(key = key, link = row.id, meta = word_set)
        after_total += 1

    for (k,v) in delta.iteritems():
        v.set_thresholds(diff_pct = _DIFF_PERCENT, diff_abs = _DIFF_ABS)
        v.set_potentials(base = base_total, after = after_total)
        if v.is_significant:
            print "ALERT FOR $s: Before: %2f /1000; After %2f /1000; "\
                  "Diff: %2f; %%diff: %2f" % (
                v.after.sorted_metadata[0:3],
                v.base_pct * 10,
                v.after_pct * 10,
                v.diff_abs * 10,
                v.diff_pct
            )

if __name__ == '__main__':

    main()

