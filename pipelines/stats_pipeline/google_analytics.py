
#TODO: add gflags
#TODO: add SQL lib
#
#TODO: test

#TODO(rrayborn): Fix this
import sys; sys.path.append('/home/shared/code/lib/web_api/')
import google_services
#TODO(rrayborn): Fix this
import sys; sys.path.append('/home/shared/code/lib/database/')
from simple_db import SimpleDB

from datetime import date, datetime, timedelta
import csv
import requests
import urllib

_DESKTOP_GA_ID = 'ga:65912487'
_MOBILE_GA_ID = 'ga:69769017'
_MAX_RESULTS = 100*365*4
_API_URL = 'https://www.googleapis.com/analytics/v3/data/ga?'

def main():
    generate_inproduct(device_type = 'desktop', start_date = '2014-10-10', end_date = '2014-10-11')


def generate_inproduct(
            auth_token  = google_services.google_service_connection().get_auth_token(), 
            versions    = None, 
            device_type = 'desktop', 
            filename    = None,
            start_date  = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'), 
            end_date    = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'), 
            ga_id       = None,
            config_file = None
        ):

    db = SimpleDB('sentiment', config_file=config_file)
    
    if not versions:
        max_version = db.execute('SELECT MAX(version) FROM release_info;')[0][0]
        versions = range(1,max_version)
    if not ga_id:
        ga_id = _DESKTOP_GA_ID if device_type == 'desktop' else _MOBILE_GA_ID
    if not filename:
        filename = device_type + '.tsv'

    # SET UP REQUEST
    device_category = 'ga:deviceCategory==desktop' if device_type =='desktop' \
            else 'ga:deviceCategory==mobile,ga:deviceCategory==tablet'

    version_filters = []
    for version in versions:
        version_filters.append('ga:browserVersion=@%s.0' % version)

    filters = [
            'ga:browser==Firefox',
            ','.join(version_filters),
            device_category,
            'ga:source=@inproduct'
        ]

    parameters = {
            'access_token': auth_token,
            'filters':      ';'.join(filters),
            'ids':          ga_id,
            'max-results':  _MAX_RESULTS,
            'dimensions':   'ga:date,ga:browserVersion',
            'metrics':      'ga:sessions',
            'samplingLevel':'HIGHER_PRECISION'
        }

    # MAKE REQUESTS
    day_datetime = datetime.strptime(start_date, '%Y-%m-%d')
    end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
    data = {}
    while day_datetime <= end_datetime:
        day = day_datetime.strftime('%Y-%m-%d')
        parameters['start-date'] = day
        parameters['end-date']   = day
        _make_request(parameters, data)
        day_datetime += timedelta(days=1)
    
    with open(filename, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter='\t',
                                quotechar='\"', quoting=csv.QUOTE_MINIMAL)

        header = ['day','version','visits']
        spamwriter.writerow(header)
        for day in sorted(data.keys()):
            for version in data[day].keys():
                spamwriter.writerow([day, version, data[day][version]])


def _make_request(parameters, data = {}):
    # TODO(rrayborn): Is there a prettier way to do this (like POST)?
    request = _API_URL + urllib.urlencode(parameters, True)
    response = requests.get(request)

    # PARSE RESPONSE
    if response.status_code == 200:
        response_json = response.json()
        for row in response_json['rows']:
            day = datetime.strptime(row[0], '%Y%m%d').strftime('%Y-%m-%d')

            if day not in data:
                data[day] = {}

            version = int(row[1].split('.')[0])
            if int(row[2]) > 0:
                if version not in data[day]:
                    data[day][version] = 0
                data[day][version] += int(row[2])
    else:
        raise Exception('Token Request results in a %s response code.' \
                        % response.status_code)

    return data

if __name__ == '__main__':
    main()

