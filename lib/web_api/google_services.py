#!/usr/local/bin/python

"""
Handles Google Service Authentication
"""

# TODO(rrayborn): Better documentation

__author__ = "Rob Rayborn"
__copyright__ = "Copyright 2014, The Mozilla Foundation"
__license__ = "MPLv2"
__maintainer__ = "Rob Rayborn"
__email__ = "rrayborn@mozilla.com"
__status__ = "Development"

from OpenSSL.crypto import load_pkcs12, dump_privatekey, FILETYPE_PEM

from datetime import date, datetime, timedelta
from os import environ
import json
import jwt
import requests
import time


_SECRETS_PATH  = environ['SECRETS_PATH']

# Header and Grant Type are always the same for Google's API so making a 
#   variable instead of a file
_HEADER_JSON = {'alg':'RS256','typ':'jwt'}
_GRANT_TYPE = 'urn:ietf:params:oauth:grant-type:jwt-bearer'
# Default filenames
_CLAIMS_FILE = _SECRETS_PATH + 'claims.json'
_P12_FILE    = _SECRETS_PATH + 'goog.p12'
_AUTH_FILE   = _SECRETS_PATH + '.auth.tmp'
# Other defaults
_GOOG_PASSPHRASE = 'notasecret' # notasecret is the universal google passphrase

class google_service_connection(object):
    def __init__(self, json_web_token=None, expiration=None, claims_file=_CLAIMS_FILE, 
                 p12_file=_P12_FILE, auth_file=_AUTH_FILE):
        self._json_web_token = None
        self._expiration     = None
        self._auth_token     = None

        self._claims_file    = claims_file
        self._p12_file       = p12_file
        self._auth_file      = auth_file

        self.get_auth_token(json_web_token,expiration)

    def get_expiration(self):
        return self._expiration

    def set_files(self, claims_file=None, p12_file=None, 
                  auth_file=None):
        self._claims_file    = claims_file or self._claims_file
        self._p12_file       = p12_file    or self._p12_file
        self._auth_file      = auth_file   or self._auth_file

    def _refresh_json_web_token(self, json_web_token=None, expiration=None, 
                                force=False):

        if not force and not _expired(self._expiration):
            return
        if json_web_token or expiration:
            if json_web_token and expiration:
                if not _expired(expiration):
                    self._json_web_token = json_web_token
                    self._expiration = expiration
                    return
                #else continue
            else:
                raise Exception('_refresh_json_web_token: Must pass json_web_token'\
                                ' and expiration together.')
        

        with open(self._p12_file, 'r')  as f:
            pk = load_pkcs12(f.read(), _GOOG_PASSPHRASE).get_privatekey()

        secret = dump_privatekey(FILETYPE_PEM, pk)

        # Load claims json
        with open(self._claims_file, 'r') as f:    
            claims_json = json.load(f)
        # Modify claims data
        current_time = int(time.time())
        claims_json['iat'] = current_time
        claims_json['exp'] = current_time + 3600 - 1

        # Remember expiration
        self._expiration = current_time + 3600

        self._json_web_token = jwt.encode(
                claims_json, secret, algorithm='RS256', headers=_HEADER_JSON
            )


    def _load_auth_token(self):
        try:
            with open(self._auth_file, 'r') as f:
                auth_json = json.load(f)
                if not _expired(auth_json['expiration']):
                    self._expiration = auth_json['expiration']
                    self._auth_token = auth_json['token']
                    return self._auth_token
                else:
                    return None
        except:
            return None
            
    def _save_auth_token(self):
        with open(self._auth_file, 'w') as f:
            data = {'token':self._auth_token, 'expiration':self._expiration}
            json.dump(data, f)

    def get_auth_token(self, json_web_token=None, expiration=None):
        if self._load_auth_token():
            return self._auth_token

        self._refresh_json_web_token(json_web_token=json_web_token, 
                                     expiration=expiration)
        parameters = {
                'grant_type':_GRANT_TYPE,
                'assertion':self._json_web_token
            }

        response = requests.post('https://accounts.google.com/o/oauth2/token', 
                                 data=parameters)
        if response.status_code == 200:
            self._auth_token = response.json()['access_token']
        else:
            raise Exception('Token Request results in a %s response code.' \
                            % response.status_code)
        self._save_auth_token()
        return self._auth_token


def _expired(exp):
    return time.time() >= exp


def main():
    gsc = google_service_connection()

    
if __name__ == '__main__':
    main()