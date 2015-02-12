#!/usr/local/bin/python

import sys
from os import path
sys.path.append(path.normpath(path.join(path.dirname(__file__), '..', '..')))
from lib.database.backend_db import Db
import csv
import json
import requests
import datetime

_TIMEFRAME = 12 # Hours
_PAST_TIMEFRAME = 3 # Weeks



def main():
    input_db = Db('input')
    
    old_data_sql = """
        SELECT description
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
        AND (platform LIKE 'Windows%' OR platform LIKE 'OS X' OR platform LIKE 'OS X')
    """
    
    results = telemetry_db.execute_sql(old_data_sql, { 
        'old' : _PAST_TIMEFRAME, 'new' : _TIMEFRAME 
        })

    for row in results:
        # Process stuff here
        print row
        
        
    new_data_sql = """
        SELECT description
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
        AND (platform LIKE 'Windows%' OR platform LIKE 'OS X' OR platform LIKE 'OS X')
    """
    
    results = telemetry_db.execute_sql(new_data_sql, { 'new' : _TIMEFRAME })

    for row in results:
        # Process stuff here
        print row
        

if __name__ == '__main__':
    main()

