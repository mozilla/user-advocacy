#!/usr/local/bin/python

'''
Exports data to our server's stats table from various sources including:
 * Input
 * Sumo
 * Google Play
 * Google Analytics
'''


__author__     = 'Rob Rayborn'
__copyright__  = 'Copyright 2015, The Mozilla Foundation'
__license__    = 'MPLv2'
__maintainer__ = 'Rob Rayborn'
__email__      = 'rrayborn@mozilla.com'
__status__     = 'Production'


#TODO: merge desktop/mobile table into one table with Product field
#TODO: add gflags
#TODO: better tests

from lib.database.backend_db  import Db as UA_DB
from lib.database.input_db    import Db as Input_DB
from lib.database.sumo_db     import Db as Sumo_DB
from pipelines.stats_pipeline import google_analytics

from datetime import date,timedelta,datetime
from dateutil.relativedelta import relativedelta
from os import path
from subprocess import check_output

_PIPELINE_PATH        = path.dirname(path.realpath(__file__))+'/'
_DATA_PATH            = _PIPELINE_PATH + 'data/'
_CREATE_SQL_FILE      = _PIPELINE_PATH + 'create.sql'
_INPUT_SQL_FILE       = _PIPELINE_PATH + 'input.sql'
_BASE_SQL_FILE        = _PIPELINE_PATH + 'base.sql'
_SUMO_SQL_FILE        = _PIPELINE_PATH + 'sumo.sql'
_ADIS_SQL_FILE        = _PIPELINE_PATH + 'adis.sql'
_QUERY_FILE_PATTERN   = _PIPELINE_PATH + 'daily_%s_stats.sql'
_DESKTOP_FILE_PATTERN = 'daily_desktop_stats.sql'
_MOBILE_FILE_PATTERN  = 'daily_mobile_stats.sql'
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

#This should be handled better...

def main():
    update()

def update(
            product    = 'both',
            start_date = (date.today() - timedelta(days=5)).strftime('%Y-%m-%d'),
            end_date   = (date.today() - timedelta(days=1)).strftime('%Y-%m-%d'),
            ua_db      = None,
            input_db   = None,
            sumo_db    = None
        ):

    if not ua_db:
        ua_db    = UA_DB('sentiment', is_persistent = True)
    if not input_db:
        input_db = Input_DB(is_persistent = True)
    if not sumo_db:
        sumo_db  = Sumo_DB(is_persistent = True)

    adis_file   = _DATA_PATH + '.' + product +'_adis.tsv'
    input_file  = _DATA_PATH + '.' + product +'_adis.tsv'
    visits_file = _DATA_PATH + '.' + product +'_visits.tsv'

    params = {'start_date': start_date, 'end_date': end_date}

    # =========== Create tables ============================================
    _execute_query(ua_db, _CREATE_SQL_FILE, params=params, multi=True)

    # =========== Parse input data =============================================
    
    # Fetch Input data
    data = _execute_query(input_db, _INPUT_SQL_FILE, params=params)

    # Create tmp_input table
    query ='''CREATE TEMPORARY TABLE tmp_input (
                `date`                     DATE,
                `version`                  INT,
                `is_desktop`               BOOL,
                `input_average`            FLOAT,
                `input_volume`             INT,
                `heartbeat_average`        FLOAT,
                `heartbeat_surveyed_users` INT,
                `heartbeat_volume`         INT
            );'''
    ua_db.execute_sql(query)

    # Insert Input data
    header = data.keys()
    ua_db.insert_data_into_table(data, 'tmp_input', header, has_header = False)
    
    # =========== Create base table ============================================
    _execute_query(ua_db, _BASE_SQL_FILE, params=params)
    
    # =========== Parse sumo data =============================================
    
    # Fetch Sumo data
    data = _execute_query(sumo_db, _SUMO_SQL_FILE, params=params)

    # Create tmp_sumo table
    query ='''CREATE TEMPORARY TABLE tmp_sumo (
                `date`                     DATE,
                `version`                  INT,
                `is_desktop`               BOOL,
                `num_unanswered_72`        INT,
                `num_posts`                INT
            );'''
    ua_db.execute_sql(query)

    # Insert Sumo data
    header = data.keys()
    ua_db.insert_data_into_table(data, 'tmp_sumo', header, has_header = False)

    # =========== Parse ADI data ===============================================
    
    # Generate query
    # TODO(rrayborn): Need to investigate why part of the end date is missing.
    #                 Doesn't seem to affect the start_date...
    today_minus_three = (date.today() - timedelta(days=3)).strftime('%Y-%m-%d')
    adi_end_date = min(today_minus_three, end_date)
    with open(_ADIS_SQL_FILE, 'r') as adis_sql:
        query = adis_sql.read().replace('\n','  ') % (start_date, adi_end_date)

    # Generate/execute command line
    cmd = 'echo "%s" | isql -v metrics_dsn  -b -x0x09  >%s' # | tail -n+10'
    check_output(cmd % (query, adis_file), shell=True)

    # Create tmp table
    query ='''CREATE TEMPORARY TABLE tmp_adis (
                `date`                DATE,
                version               INT,
                is_desktop            BOOL,
                num_adis              INT
            );'''
    ua_db.execute_sql(query)

    header = ['date', 'version', 'is_desktop', 'num_adis']

    ua_db.insert_csv_into_table(adis_file, 'tmp_adis', header, delimiter = '\t')
    
    # =========== Parse Analytics data =========================================

    # Get Google analytics data
    google_analytics.generate_inproduct( 
            db          = ua_db,
            device_type = product, 
            filename    = visits_file,
            start_date  = start_date,
            end_date    = end_date
        )

    # Create tmp table
    query ='''CREATE TEMPORARY TABLE tmp_sumo_visits (
                `date`      DATE, 
                version     INT,
                is_desktop  BOOL,
                visits      INT
            );'''
    ua_db.execute_sql(query)

    header = ['date', 'version', 'is_desktop', 'visits']
    ua_db.insert_csv_into_table(visits_file, 'tmp_sumo_visits', header, delimiter = '\t')

    
    # =========== Parse Play data ==============================================

    query = '''CREATE TEMPORARY TABLE tmp_play AS 
        SELECT
            `date`, 
            version,
            AVG(rating) AS play_average,
            COUNT(*)    AS play_volume
        FROM google_play_reviews
        WHERE
                `date` >= :start_date
            AND `date` <= :end_date
        GROUP BY 1,2;
    '''
    ua_db.execute_sql(query, params)
    
    # =========== Run Stats query ==============================================
    query_files = []
    if product == 'both' or product == 'desktop':
        query_files.append(_DESKTOP_FILE_PATTERN)
    if product == 'both' or product == 'mobile':
        query_files.append(_MOBILE_FILE_PATTERN)

    for query_file in query_files:
        _execute_query(ua_db,query_file, params=params)

def _execute_query(db, query_file, params = None, multi=False):
    with open(query_file, 'r') as query_sql:
        query = query_sql.read()
    if multi:
        db.janky_execute_sql_wrapper(query, query_vars = params)
    else:
        return db.execute_sql(query, params)

if __name__ == "__main__":
    main()
