
#TODO: add gflags
#TODO: add SQL lib
#
#TODO: test

#TODO(rrayborn): Fix this
import sys; sys.path.append('/home/shared/code/lib/database/')
from simple_db import SimpleDB

from datetime import date,timedelta
from dateutil.relativedelta import relativedelta
from subprocess import check_output


_OVERLAP    = 2 # INCREASE THIS IF GOOGLE STARTS BACK POPULATING DATA
_PIPELINE_PATH = '/home/shared/code/pipelines/google_play/'
_DATA_PATH  = _PIPELINE_PATH + 'data/'
_TMP_CSV    = _DATA_PATH + '.google_play_tmp.csv'
_LATEST_CSV = _DATA_PATH + 'google_play_latest.csv'
_ALL_CSV    = _DATA_PATH + 'google_play_all.csv'
_SQL_FILE   = _PIPELINE_PATH + 'google_play_update.sql'
_SQL_CONFIG = _PIPELINE_PATH + 'sql.cnf'
_REVIEW_FILE_PATTERN = 'gs://pubsite_prod_rev_04753778179066947806' + \
        '/reviews/reviews_org.mozilla.*%s.csv'


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
    update()

def bootstrap(start_month = date.today() - relativedelta(years = 1, months = 1),
              end_month = date.today()):
    if start_month > end_month:
        raise Exception('start_month is greater than end_month.')

    month = start_month - timedelta(start_month.day - 1) #TODO am I off by 1
    destroy = True
    while (month <= end_month):
        _download_convert_merge(month, destroy=destroy)
        destroy = False
        month = month + relativedelta(months = 1)
    _execute_sql()
    _execute('mv -f %s %s' % (_LATEST_CSV, _ALL_CSV))


def update(pull_date = date.today()):

    day = pull_date.day

    _download_convert_merge(pull_date, True)
    
    if day == _OVERLAP:
        # Merge last month and all for posterity
        _download_convert_merge(pull_date - timedelta(days=day), new_file=_ALL_CSV)

    if day <= _OVERLAP:
        # Merge this month and last month
        _download_convert_merge(pull_date - timedelta(days=day))
    
    _header_exception_raiser(_LATEST_CSV,_ALL_CSV)

    # min_date = MONTH_FLOOR(pull_date - (_OVERLAP + 1))
    # The min date of our data is the max date of the previous data
    min_date = (pull_date - timedelta(days=_OVERLAP+1)).strftime('%Y-%m-01')

    # Database stuff
    _execute_sql(max_date = min_date)


def _execute_sql(csv_file = _LATEST_CSV, max_date = '2000-01-01'):
    with open(_SQL_FILE, 'r') as sql:
        if sql:
            query = 'SET @max_date="%s";\n' % max_date
            query += 'SET @csv_file="%s";\n' % csv_file
            query += sql.read()

            db = SimpleDB('sentiment', config_file=_SQL_CONFIG)
            db.execute(query)
            db.commit()


def _download_convert_merge(file_date, destroy=False, new_file=_LATEST_CSV):
    year_month = file_date.strftime('%Y%m')

    # Download new files
    _execute('gsutil cp %s %s' % (_REVIEW_FILE_PATTERN % year_month, _DATA_PATH))
    
    ls_out = _execute('ls %s*%s.csv' % (_DATA_PATH, year_month))
    filenames = ls_out.split('\n')[:-1]

    for old_file in filenames:
        if destroy:
            _execute('iconv  -f  UTF-16LE -t UTF-8 %s >%s' % (old_file, new_file) )
            destroy = False
        else:
            _execute('iconv  -f  UTF-16LE -t UTF-8 %s >%s' % (old_file, _TMP_CSV) )
            _execute('tail -n +2 <%s >>%s' % (_TMP_CSV, new_file) )
            _header_exception_raiser(_TMP_CSV, new_file)
    
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
