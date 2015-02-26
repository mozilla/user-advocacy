#!/usr/local/bin/python

import sys
from os import path, environ
import json
import requests
import datetime
import httplib
httplib.HTTPConnection.debuglevel = 1
import urllib
from email.utils import mktime_tz, parsedate_tz

_TIMEFRAME = 14 # Days
ALERT_FILENAME = 'input_alerts.json'

ALERT_TOKEN = environ['ALERT_TOKEN']

def main():
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json; indent=4',
        'Fjord-Authorization': 'Token ' + ALERT_TOKEN,
    }
    qs_params = {
        'flavors': 'word-based'
    }
    resp = requests.get(
        'https://input.mozilla.org/api/v1/alerts/alert/?' + urllib.urlencode(qs_params),
        headers=headers
    )
    if resp.status_code == 200:
        file_path = path.join(
            environ['CODE_PATH'], 
            'flask/useradvocacy/data/static_json',
            ALERT_FILENAME
        )
        file = open(file_path, 'w')
        alert_json = resp.json()
        timestamp = mktime_tz(parsedate_tz(resp.headers['date']))
        alert_json['lastUpdateTimestamp'] = timestamp
        alert_json['lastUpdated'] = str(datetime.datetime.fromtimestamp(timestamp))
        json.dump(alert_json, file)
        print "Successfully saved %s"%(file_path)
    else:
        print "Error: " + json.dumps(resp)
    
if __name__ == '__main__':

    main()

