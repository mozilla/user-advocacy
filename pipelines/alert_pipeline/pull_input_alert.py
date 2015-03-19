#!/usr/local/bin/python

import sys
from os import path, environ, remove
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
_INPUT_URL = 'https://input.mozilla.org/api/v1/alerts/alert/?'

# TODO: make this env based.
_OUTPUT_PATH = '/var/server/server/useradvocacy/data/static_json/'

def main():
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json; indent=4',
        'Fjord-Authorization': 'Token ' + ALERT_TOKEN,
    }
    qs_params = {
        'flavors': 'word-based',
        'max': 10000
    }
    resp = requests.get(
        _INPUT_URL + urllib.urlencode(qs_params),
        headers=headers
    )
    if resp.status_code == 200:
        file_path = path.join(
            _OUTPUT_PATH,
            ALERT_FILENAME
        )
        remove(file_path)
        file = open(file_path, 'w')
        alert_json = resp.json()
        timestamp = mktime_tz(parsedate_tz(resp.headers['date']))
        alert_json['lastUpdateTimestamp'] = timestamp
        alert_json['lastUpdated'] = str(datetime.datetime.fromtimestamp(timestamp))
        json.dump(alert_json, file, indent=4, ensure_ascii=False, encoding="utf-8")
        print "Successfully saved %s"%(file_path)
    else:
        print "Error: " + json.dumps(resp)
    
if __name__ == '__main__':

    main()

