
#TODO: add gflags
#TODO: add SQL lib
#
#TODO: test

#TODO(rrayborn): Fix this
import sys;
sys.path.append('/home/shared/code/lib/database/')
from simple_db import SimpleDB
sys.path.append('/home/shared/code/stats_pipeline/')
import google_analytics

import csv
from datetime import date,timedelta
from dateutil.relativedelta import relativedelta
from os import path
from subprocess import check_output

_PIPELINE_PATH = path.dirname(path.realpath(__file__))+'/'
_DATA_PATH  = _PIPELINE_PATH + 'data/'
_ADIS_SQL_FILE = _PIPELINE_PATH + 'adis.sql'
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
#def main():
#    bootstrap()
#    if bootstrap:
#        if csv:
#            bootstrap(csv)
#        else:
#            bootstrap()
#    elif date:
#        update(date)
#    else:
#        update()
def main():
    #update(start_date='2014-11-02', end_date='2014-11-04')
    update()

def update(
            start_date = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d'),
            end_date   = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d'),
            product    = None
        ):
    if product:
        update_product(product = product, start_date=start_date, end_date=end_date)
    else:
        update_product(product = 'desktop', start_date=start_date, end_date=end_date)
        update_product(product = 'mobile',  start_date=start_date, end_date=end_date)

def update_product(
            product    = None,
            start_date = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d'),
            end_date   = (date.today() - timedelta(days=2)).strftime('%Y-%m-%d')
        ):

    adis_file   = _DATA_PATH + '.' + product +'_adis.tsv'
    visits_file  = _DATA_PATH + '.' + product +'_visits.tsv'
    query_file  = _QUERY_FILE_PATTERN % product
    alt_product = 'Firefox' if product == 'desktop' else 'Fennec'

    generate_adis(alt_product, adis_file, start_date, end_date)

    google_analytics.generate_inproduct( 
            device_type = product, 
            filename    = visits_file,
            start_date  = start_date,
            end_date    = end_date
        )

    run_stats_query(
            start_date,
            end_date,
            adis_file,
            visits_file,
            query_file
        )

def run_stats_query(
            start_date,
            end_date,
            adis_file,
            visits_file,
            query_file
        ):
    
    #set @adis_file = "%s";\nset @visits_file = "%s";\n' % (
    #adis_file,
    #visits_file
    query_preface = 'set @start_date = "%s";\nset @end_date = "%s";\n' % (
            start_date,
            end_date
        )

    with open(query_file, 'r') as query_sql:
        if query_sql:
            query = query_sql.read()
            query = query.replace("@visits_file",visits_file)
            query = query.replace("@adis_file",adis_file)
            query = query.replace("@start_date",'"'+str(start_date)+'"')
            query = query.replace("@end_date",'"'+str(end_date)+'"')
    
    db = SimpleDB('sentiment')
    db.execute(query,verbose=True)
    db.commit()

def generate_adis(product, filename, start_date, end_date):
    cmd = 'echo "%s" | isql -v metrics_dsn  -b -x0x09 >%s'
    with open(_ADIS_SQL_FILE, 'r') as adis_sql:
        if adis_sql:
            query = adis_sql.read().replace('\n','  ') % (
                    product, start_date, end_date)
    _execute(cmd % (query, filename))


# Utilites

def _execute(cmd):
    return check_output(cmd, shell=True)


if __name__ == "__main__":
    main()
