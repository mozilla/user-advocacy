#!/usr/local/bin/python

import datetime
import httplib
import json
import sys
import urllib
from email.utils import mktime_tz, parsedate_tz
from os import path, environ, remove

import requests

httplib.HTTPConnection.debuglevel = 1

_TIMEFRAME = 14 # Days
ALERT_FILENAME = 'input_alerts.json'
ANDROID_ALERT_FILENAME = 'android_input_alerts.json'

ALERT_TOKEN = environ['ALERT_TOKEN']
_INPUT_URL = 'https://input.mozilla.org/api/v1/alerts/alert/?'

_OUTPUT_PATH = path.join(environ['SERVER_PATH'],'data/static_json/')

end_time = datetime.datetime.now() - datetime.timedelta(days=_TIMEFRAME)

def get_alerts(flavor, filename):
    headers = {
        'content-type': 'application/json',
        'accept': 'application/json; indent=4',
        'Fjord-Authorization': 'Token ' + ALERT_TOKEN,
    }
    qs_params = {
        'flavors': flavor,
        'max': 3000,
        'end_time_start': end_time.isoformat()
    }
    resp = requests.get(
        _INPUT_URL + urllib.urlencode(qs_params),
        headers=headers
    )
    if resp.status_code == 200:
        file_path = path.join(
            _OUTPUT_PATH,
            filename
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
    
def main():
    get_alerts('word-based', ALERT_FILENAME)
    get_alerts('android-word-based', ANDROID_ALERT_FILENAME)

if __name__ == '__main__':

    main()

