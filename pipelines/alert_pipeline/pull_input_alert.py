#!/usr/local/bin/python

import sys
from os import path, environ
import json
import requests
import datetime
import httplib
httplib.HTTPConnection.debuglevel = 1

_TIMEFRAME = 14 # Days

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
        print resp.json
    else:
        print resp
    
if __name__ == '__main__':

    main()

