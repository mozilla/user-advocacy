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

import csv
import gzip
import json
from datetime import date,timedelta
from os import path
from subprocess import call

from lib.database.backend_db import Db

_PIPELINE_PATH   = path.dirname(path.realpath(__file__))+'/'
_OTHER_SQL_FILE  = _PIPELINE_PATH + 'other.sql'
_COUNTS_SQL_FILE = _PIPELINE_PATH + 'counts.sql'
_DUMP_SQL_FILE   = _PIPELINE_PATH + 'dump.sql'

#TODO(rrayborn): Make this a relative path
_OUTPUT_PATH         = '/var/server/server/useradvocacy/data/static_json/'
_OUTPUT_JSON_NAME    = 'hello.json'
_OUTPUT_CSV_NAME     = 'hello.csv.gz'

#TODO(rrayborn): make this more elegant
_INPUT_DB = Db('input')

def update(
            start_date    = date.today() - timedelta(days=6*7), 
            end_date      = date.today() - timedelta(days=1),
            last_run_date = date.today() - timedelta(days=1),
            output_path   = _OUTPUT_PATH
        ):
    '''
    Updates the Hello files.

    Args:
        start_date    (datetime): start date of data to pull, inclusive (default: 42 days ago)
        end_date      (datetime): end date of data to pull, inclusive   (default: 1 day ago)
        last_run_date (datetime): last date that the pipeline was run for (default: 1 day ago)
        output_path   (str): the location where our files should be output (default: _OUTPUT_PATH)
    '''

    json_path = output_path + '/' + _OUTPUT_JSON_NAME
    csv_path  = output_path + '/' + _OUTPUT_CSV_NAME

    # Create query var dict for SQL replacement
    query_vars = {
            'start_date':    start_date,
            'end_date':      end_date,
            'last_run_date': last_run_date
        }

    #============ JSON CREATION =============================
    # Generate the aggregate counts for each category/week

    # fetch data from SQL
    with open(_COUNTS_SQL_FILE, 'r') as counts_sql:
        counts_query = counts_sql.read()
    counts_data  = _INPUT_DB.execute_sql(counts_query, query_vars)

    # parse data into dict
    counts_dict = {}
    for row in counts_data:
        day      = str(row[0])
        category = str(row[1])
        count    = int(row[2])
        if day not in counts_dict.keys():
            counts_dict[day] = {}
            counts_dict[day]['date']  = day
            counts_dict[day]['total_count']  = 0
        counts_dict[day][category + '_count'] = count
        counts_dict[day]['total_count'] += count

    # Generate the Other verbatims week

    # fetch data from SQL
    with open(_OTHER_SQL_FILE, 'r') as other_sql:
        other_query = other_sql.read()
    other_data = _INPUT_DB.execute_sql(other_query, query_vars)

    # parse data into dict
    other_comment_label = 'other_comments'
    for row in other_data:
        day     = str(row[0])
        comment = str(row[1])
        count   = int(row[2])
        if other_comment_label not in counts_dict[day].keys():
            counts_dict[day][other_comment_label] = []
        counts_dict[day][other_comment_label].append({'comment':comment,'count':count})

    # output the json
    with open(json_path, 'w') as outfile:
        json.dump(
                {'data':counts_dict.values()},
                outfile, 
                indent=4,
                ensure_ascii=False,
                encoding="utf-8"
            )
    

    #============ CSV =============================

    # get old data within our timeframe so that we only have to do the minimum
    # amount of work
    header = [
            'created','id','happy','category','platform','browser',
            'browser_version','channel','version','user_agent','description',
            'url'
        ]
    output_data = [header]
    #TODO(rrayborn): check for existance
    with gzip.open(csv_path, 'rb') as output_csv:
        csv_reader = csv.reader(output_csv, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        csv_reader.next() # remove header
        for row in csv_reader:
            if      row[0] > start_date.strftime('%Y-%m-%d') and \
                    row[0] < last_run_date.strftime('%Y-%m-%d'):
                output_data.append(row)

    
 
    # append new data
    with open(_DUMP_SQL_FILE, 'r') as dump_sql:
        dump_query = dump_sql.read()
    dump_data = _INPUT_DB.execute_sql(dump_query, query_vars)

    new_data = []
    for row in dump_data:
        new_row = []
        for entry in row:
            if type(entry) == 'str':
                new_row.append(entry.decode("utf-8").encode('latin-1')) #TODO(rrayborn): why latin-1?
            else:
                new_row.append(entry)

        new_data.append(new_row)
        
    output_data += new_data

    # output result
    with gzip.open(csv_path, 'w+') as output_csv:
        csv_writer = csv.writer(output_csv, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in output_data:
            csv_writer.writerow(row)


if __name__ == "__main__":
    update()
