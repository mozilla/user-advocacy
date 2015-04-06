
#TODO: add gflags
#TODO: test


from lib.database.backend_db import Db
from lib.web_api import google_services


from datetime import date, datetime, timedelta
import csv
import requests
import urllib

_DESKTOP_GA_ID = 'ga:65912487'
_MOBILE_GA_ID = 'ga:69769017'
_MAX_RESULTS = 100*365*4
_API_URL = 'https://www.googleapis.com/analytics/v3/data/ga?'


def main():
    generate_inproduct(device_type = 'both')


def generate_inproduct(
            db          = None,
            auth_token  = google_services.google_service_connection().get_auth_token(), 
            versions    = None, 
            device_type = 'both', 
            filename    = None,
            start_date  = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'), 
            end_date    = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'), 
            ga_ids       = None,
            max_results = _MAX_RESULTS
        ):
    if not versions:
        if not db:
            db = Db('sentiment')
        max_version = db.execute_sql('SELECT MAX(version) FROM release_info;').first()[0]
        versions = range(1,max_version)
    version_filters = []
    for version in versions:
        version_filters.append('ga:browserVersion=@%s.0' % version)

    if not filename:
        filename = device_type + '.tsv'

    device_types = []
    if device_type == 'both' or device_type == 'desktop':
        device_types.append(True)
    if device_type == 'both' or device_type == 'mobile':
        device_types.append(False)

    data = {}
    # SET UP REQUEST
    for is_desktop in device_types:
        if not ga_ids:
            if is_desktop:
                ga_ids = _DESKTOP_GA_ID
            else:
                ga_ids = _MOBILE_GA_ID

        device_categories = []
        if is_desktop:
            device_categories = ['ga:deviceCategory==desktop']
        else:
            device_categories = ['ga:deviceCategory==mobile',
                                 'ga:deviceCategory==tablet']

        dimensions = ['ga:date', 'ga:browserVersion']

        filters = [
                ','.join(version_filters),
                ','.join(device_categories),
                'ga:browser==Firefox',
                'ga:source=@inproduct'
            ]

        parameters = {
                'ids':          ga_ids,
                'access_token': auth_token,
                'max-results':  max_results,
                'filters':      ';'.join(filters),
                'dimensions':   ','.join(dimensions),
                'metrics':      'ga:sessions',
                'samplingLevel':'HIGHER_PRECISION'
            }

        # MAKE REQUESTS
        # This is done in a for loop since it's easy to hit Google's data limit
        # in a single multi-day request.
        day_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')
        while day_datetime <= end_datetime:
            day = day_datetime.strftime('%Y-%m-%d')
            parameters['start-date'] = day
            parameters['end-date']   = day
            _make_request(parameters, is_desktop, data)
            day_datetime += timedelta(days=1)
    
    with open(filename, 'wb') as csvfile:
        spamwriter = csv.writer(csvfile, delimiter='\t',
                                quotechar='\"', quoting=csv.QUOTE_MINIMAL)

        header = ['day','version','is_desktop','visits']
        spamwriter.writerow(header)
        for day in sorted(data.keys()):
            for version in sorted(data[day].keys()):
                for is_desktop in sorted(data[day][version].keys()):
                    spamwriter.writerow([day, version, is_desktop, 
                                        data[day][version][is_desktop]])


def _make_request(parameters, is_desktop, data = {}):
    # TODO(rrayborn): Is there a prettier way to do this (like POST)?
    request = _API_URL + urllib.urlencode(parameters, True)
    response = requests.get(request)

    # PARSE RESPONSE
    if response.status_code == 200:
        response_json = response.json()
        for row in response_json['rows']:
            day = datetime.strptime(row[0], '%Y%m%d').strftime('%Y-%m-%d')
            try:
                version = int(row[1].split('.')[0])
            except Exception:
                version = None

            if day not in data.keys():
                data[day] = {}

            if int(row[2]) > 0:
                if version not in data[day].keys():
                    data[day][version] = {}
                if is_desktop not in data[day][version].keys():
                    data[day][version][is_desktop] = 0
                data[day][version][is_desktop] += int(row[2])
    else:
        raise Exception('Token Request results in a %s response code.' \
                        % response.status_code)

    return data


if __name__ == '__main__':
    main()

