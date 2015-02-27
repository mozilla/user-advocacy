#!/usr/local/bin/python

'''
Exports Hello AKA Loop data to our server's static data dir.
'''

#TODO(rrayborn): 

__author__     = 'Rob Rayborn'
__copyright__  = 'Copyright 2015, The Mozilla Foundation'
__license__    = 'MPLv2'
__maintainer__ = 'Rob Rayborn'
__email__      = 'rrayborn@mozilla.com'
__status__     = 'Production'

#TODO: add gflags
#TODO: add SQL lib
#
#TODO: test

from lib.database.backend_db  import Db
from pipelines.stats_pipeline import google_analytics

import csv
from datetime import date,timedelta
from dateutil.relativedelta import relativedelta
from os import path
from subprocess import check_output

_PIPELINE_PATH      = path.dirname(path.realpath(__file__))+'/'
_DATA_PATH          = _PIPELINE_PATH + 'data/'
_ADIS_SQL_FILE      = _PIPELINE_PATH + 'adis.sql'
_QUERY_FILE_PATTERN = _PIPELINE_PATH + 'daily_%s_stats.sql'

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
_SENTIMENT_DB = Db('sentiment', is_persistent = True)

def main():
    update(product='desktop',start_date='2015-02-24', end_date='2015-02-24')
    #update()

#TODO(rrayborn): bootstrap function

def update(
            product    = None,
            start_date = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d'),
            end_date   = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d'),
            db         = _SENTIMENT_DB
        ):
    if product:
        _update_product(product, start_date, end_date, db)
    else:
        _update_product('desktop', start_date, end_date, db)
        _update_product('mobile',  start_date, end_date, db)

def _update_product(
            product,
            start_date,
            end_date,
            db
        ):

    adis_file   = _DATA_PATH + '.' + product +'_adis.tsv'
    visits_file = _DATA_PATH + '.' + product +'_visits.tsv'
    query_file  = _QUERY_FILE_PATTERN % product
    alt_product = 'Firefox' if product == 'desktop' else 'Fennec'

    # =========== Parse ADI data ===============================================
    tmp_adis_table = 'tmp_%s_adis' % product
    cmd = 'echo "%s" | isql -v metrics_dsn  -b -x0x09 >%s'
    with open(_ADIS_SQL_FILE, 'r') as adis_sql:
        if adis_sql:
            query = adis_sql.read().replace('\n','  ') % (
                    alt_product, start_date, end_date)
    check_output(cmd % (query, adis_file), shell=True)
    query ='''CREATE TEMPORARY TABLE {table} (
                `date`                DATE NOT NULL, 
                version               INT  NOT NULL, 
                num_adis              INT  NOT NULL, 
                CONSTRAINT unique_stat UNIQUE (`date`, version)
            );'''.format(table = tmp_adis_table)
    execute_wrapper(db, query)

    load_csv_into_table(adis_file, 
                        tmp_adis_table,
                        db,
                        header = ['`date`', 'version', 'num_adis'])
            
    # =========== Parse Analytics data =========================================
    tmp_sumo_table = 'tmp_%s_sumo_visits' % product
    # Get Google analytics data
    google_analytics.generate_inproduct( 
            db          = db,
            device_type = product, 
            filename    = visits_file,
            start_date  = start_date,
            end_date    = end_date
        )

    query ='''CREATE TEMPORARY TABLE {table} (
                `date`                DATE NOT NULL, 
                version               INT  NOT NULL, 
                visits                INT  NOT NULL, 
                CONSTRAINT unique_stat UNIQUE (`date`, version)
            );'''.format(table = tmp_sumo_table)
    execute_wrapper(db, query)

    load_csv_into_table(visits_file, 
                        tmp_sumo_table,
                        db,
                        header = ['`date`', 'version', 'visits'])

    # =========== Run Stats query ==============================================
    with open(query_file, 'r') as query_sql:
        if query_sql:
            query = query_sql.read()
    
    execute_wrapper(db, query, {'start_date': start_date, 'end_date': end_date})


def load_csv_into_table(filename, tablename, db, header = None):
    with open(filename, 'rb') as f:
        reader = csv.reader(f, delimiter='\t')
        # remove header
        h = reader.next()
        if not header:
            header = h
        insert_str = ('INSERT INTO %s (%s) ' % (tablename, ','.join(header))) \
                     + ' VALUES (%s);'
        for row in reader:
            if isinstance(row[0],str):
                row[0] = '"' + row[0] + '"'
            db.execute_sql(insert_str % ','.join(row))
    
def execute_wrapper(db, sql, query_vars = None, verbose = False):
    queries = sql.split(';')
    for query in queries:
        print query
        if query != '':
            if query_vars:
                db.execute_sql(query, query_vars)
            else:
                db.execute_sql(query)

if __name__ == "__main__":
    main()
