
#TODO: add gflags
#TODO: encoding issues

from lib.database.backend_db import Db

import csv
from datetime import date,datetime,timedelta
from dateutil.relativedelta import relativedelta
from os import path,environ
from subprocess import check_output
from collections import Counter

_OVERLAP    = 2 # INCREASE THIS IF GOOGLE STARTS BACK POPULATING DATA

_PIPELINE_PATH = path.dirname(path.realpath(__file__))+'/'
_DATA_PATH  = _PIPELINE_PATH + 'data/'

_TMP_CSV    = _DATA_PATH + '.google_play_tmp.csv'
_LATEST_CSV = _DATA_PATH + 'google_play_latest.csv'
_ALL_CSV    = _DATA_PATH + 'google_play_all.csv'
_REVIEW_FILE_PATTERN = environ['GS_PLAY_BUCKET'] + \
        '/reviews/reviews_org.mozilla.*%s.csv'

#This should be handled better...
_SENTIMENT_DB = Db('sentiment')


#FLAGS = gflags.FLAGS
#
#gflags.DEFINE_integer('my_version', 0, 'Version number.')
#gflags.DEFINE_string('filename', None, 'Input file name', short_name='f')
#
#gflags.RegisterValidator('my_version',
#                        lambda value: value % 2 == 0,
#                        message='--my_version must be divisible by 2')
#gflags.MarkFlagAsRequired('filename')
#
#



def main():
    update()

#TODO(rrayborn): Make a bootstrap method
#def bootstrap(start_month = date.today() - relativedelta(years = 1, months = 1),
#              end_month = date.today()):
#    if start_month > end_month:
#        raise Exception('start_month is greater than end_month.')
#
#    month = start_month - timedelta(start_month.day - 1) #TODO am I off by 1
#    destroy = True
#    while (month <= end_month):
#        _download_convert_merge(month, latest_csv, destroy=destroy)
#        destroy = False
#        month = month + relativedelta(months = 1)
#    _execute_sql()
#    _execute('mv -f %s %s' % (_LATEST_CSV, _ALL_CSV))


def update(pull_date  = date.today() - relativedelta(days = 1),
           latest_csv = _LATEST_CSV,
           all_csv    = _ALL_CSV,
           db         = _SENTIMENT_DB):

    day = pull_date.day

    _download_convert_merge(pull_date, latest_csv, destroy = True)
    
    if day == _OVERLAP:
        # Merge last month and all for posterity
        _download_convert_merge(pull_date - timedelta(days=day), all_csv)

    if day <= _OVERLAP:
        # Merge this month and last month
        _download_convert_merge(pull_date - timedelta(days=day), latest_csv)
    
    _header_exception_raiser(latest_csv, all_csv)

    # min_date = MONTH_FLOOR(pull_date - (_OVERLAP + 1))
    # The min date of our data is the max date of the previous data
    min_date = (pull_date - timedelta(days=_OVERLAP+1)).strftime('%Y-%m-01')
    version_dates = _get_versions_dates(pull_date,pull_date)

    # Database stuff
    create_table_if_not_exists()

    with open(latest_csv, 'rb') as f:
        reader = csv.reader(f)
        reader.next() # remove header
        #stats = {} # version -> Counter()
        for row in reader:
            package        = row[0]       #Package Name
                                          #App Version [Not the same as our versioning!]
            language       = row[2]       #Reviewer Language
            model          = row[3]       #Reviewer Hardware Model
                                          #Review Submit Date and Time
            created        = int(row[5])  #Review Submit Millis Since Epoch
                                          #Review Last Update Date and Time
            updated_millis = int(row[7])  #Review Last Update Millis Since Epoch
            rating         = int(row[8])  #Star Rating
            title          = row[9]       #Review Title
            description    = row[10]      #Review Text
                                          #Developer Reply Date and Time
                                          #Developer Reply Millis Since Epoch
                                          #Developer Reply Text
                                          #URL [undocumented]

            date_str = datetime.fromtimestamp(updated_millis/1000 + 7*3600)\
                    .strftime('%Y-%m-%d')
            if date_str == pull_date.strftime('%Y-%m-%d'):
                is_beta = package.find('beta') >=0
                start_date_key = 'beta_start_date' if is_beta else 'release_start_date'
                end_date_key   = 'beta_end_date'   if is_beta else 'release_end_date'
                version = None
                for row in version_dates:
                    if row[start_date_key] \
                            and date_str >= row[start_date_key] \
                            and date_str <= row[end_date_key]:
                        version = row['version']
                        break

                if version is None:
                    raise Exception('Version information not found in release_info \
                                    for date %s' % date_str)

                #if version not in stats.keys():
                #    stats[version] = Counter()
                #stats[version][date_str] += 1

                _update_row(
                        {
                            'created':     created,
                            'date_str':    date_str,
                            'version':     version,
                            'language':    language,
                            'model':       model,
                            'rating':      rating,
                            'title':       title,
                            'description': description
                        },
                        db
                    )
    #pprint(stats)

def create_table_if_not_exists(db = _SENTIMENT_DB):
    # create the table if not exists
    query = '''CREATE TABLE IF NOT EXISTS google_play_reviews (
        created               BIGINT NOT NULL, 
        `date`                DATE, 
        version               INT, 
        language              TEXT, 
        model                 TEXT, 
        rating                INT, 
        title                 TEXT, 
        description           TEXT, 
        PRIMARY KEY (created)
    );'''
    db.execute_sql(query)

def _update_row(values, db = _SENTIMENT_DB):
    query = '''REPLACE INTO google_play_reviews
                SET
                    created     = :created,
                    `date`      = :date_str,
                    version     = :version,
                    language    = :language,
                    model       = :model,
                    rating      = :rating,
                    title       = :title,
                    description = :description
            ;'''
    db.execute_sql(query, values)


def _get_versions_dates(start_date_str, end_date_str, db = _SENTIMENT_DB):
    query = '''SELECT
            version,
            IF(release_start_date <= :end_date_str
                        AND release_end_date >= :start_date_str,
                    release_start_date,
                    Null
                ) AS release_start_date,
            IF(release_start_date <= :end_date_str
                        AND release_end_date >= :start_date_str,
                    release_end_date,
                    Null
                ) AS release_end_date,
            IF(beta_start_date <= :end_date_str
                        AND beta_end_date >= :start_date_str,
                    beta_start_date,
                    Null
                ) AS beta_start_date,
            IF(beta_start_date <= :end_date_str
                        AND beta_end_date >= :start_date_str,
                    beta_end_date,
                    Null
                ) AS beta_end_date
        FROM
            release_info
        WHERE  
                beta_start_date <= :end_date_str
                AND release_end_date >= :start_date_str
        ;
        '''
    results = db.execute_sql(
            query, 
            {'start_date_str':start_date_str, 'end_date_str':end_date_str}
        )
    ret = []

    for row in results:
        new_row = {}
        for k in row.keys():
            if isinstance(row[k],date):
                v = row[k].strftime('%Y-%m-%d')
            else:
                v = row[k]
            new_row[k] = v
        ret.append(new_row)
    return ret


def _download_convert_merge(file_date, filename, destroy=False):
    year_month = file_date.strftime('%Y%m')

    # Download new files
    _execute('gsutil cp %s %s' % (_REVIEW_FILE_PATTERN % year_month, _DATA_PATH))
    
    ls_out = _execute('ls %s*%s.csv' % (_DATA_PATH, year_month))
    filenames = ls_out.split('\n')[:-1]

    for old_file in filenames:
        if destroy:
            _execute('iconv  -f  UTF-16LE -t UTF-8 %s >%s' % (old_file, filename) )
            destroy = False
        else:
            _execute('iconv  -f  UTF-16LE -t UTF-8 %s >%s' % (old_file, _TMP_CSV) )
            _execute('tail -n +2 <%s >>%s' % (_TMP_CSV, filename) )
            _header_exception_raiser(_TMP_CSV, filename)
    
    _execute('rm %s/reviews_org.mozilla*' % _DATA_PATH)

def _header_exception_raiser(file1, file2):
    ret1 = _execute('head -n 1 %s' % file1)
    ret2 = _execute('head -n 1 %s' % file2)
    if (ret1 != ret2):
        raise Exception('%s\'s headers don\'t match %s\'s headers' 
                        % (file1, file2))

def _execute(cmd):
    return check_output(cmd, shell=True)


if __name__ == "__main__":
    main()
