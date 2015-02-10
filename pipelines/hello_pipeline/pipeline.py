
#TODO: add gflags
#TODO: add SQL lib
#
#TODO: test

#TODO(rrayborn): Fix this
import sys;
sys.path.append('/home/shared/code/lib/database/')
from simple_db import SimpleDB

import csv
import gzip
import json
from datetime import date,timedelta
from os import path
from subprocess import call

_PIPELINE_PATH   = path.dirname(path.realpath(__file__))+'/'
_OTHER_SQL_FILE  = _PIPELINE_PATH + 'other.sql'
_COUNTS_SQL_FILE = _PIPELINE_PATH + 'counts.sql'
_DUMP_SQL_FILE   = _PIPELINE_PATH + 'dump.sql'

_OUTPUT_PATH         = '/var/server/server/useradvocacy/data/static_json/'
_OUTPUT_JSON         = _OUTPUT_PATH + 'hello.json'
_OUTPUT_CSV_PATTERN  = _OUTPUT_PATH + 'hello.csv.gz'

def main():
    update()

def update(
            start_date = date.today() - timedelta(days=6*7), 
            end_date   = date.today() - timedelta(days=1)
        ):
    
    query_preface = 'set @start_date = "%s";\nset @end_date = "%s";\n' % (
            start_date,
            end_date
        )
    
    db = SimpleDB('sentiment')
    db.set_utf8()

#    #============ JSON =============================
#    with open(_COUNTS_SQL_FILE, 'r') as counts_sql:
#        if counts_sql:
#            counts_query = query_preface + counts_sql.read()
#            counts_data = db.execute(counts_query)
#
#    # category counts
#    counts_dict = {}
#    for row in counts_data:
#        day      = str(row[0])
#        category = row[1]
#        count    = int(row[2])
#        if day not in counts_dict.keys():
#            counts_dict[day] = {}
#            counts_dict[day]['date']  = day
#            counts_dict[day]['total_count']  = 0
#        counts_dict[day][category + '_count'] = count
#        counts_dict[day]['total_count'] += count
#
#    # "Other" verbatims
#    with open(_OTHER_SQL_FILE, 'r') as other_sql:
#        if other_sql:
#            other_query = query_preface + other_sql.read()
#            other_data = db.execute(other_query)
#
#    other_dict = {}
#    for row in other_data:
#        day      = str(row[0])
#        comment  = row[1]
#        count    = int(row[2])
#        if day not in other_dict.keys():
#            other_dict[day] = []
#        other_dict[day].append({'comment':comment,'count':count})
#
#    # merge data
#    count_list = []
#    for day in counts_dict.keys():
#        counts_dict[day]['other_comments'] = other_dict[day]
#        count_list.append(counts_dict[day])
#
#    # output
#    with open(_OUTPUT_JSON, 'w') as outfile:
#        json.dump(
#                {'data':count_list},
#                outfile, 
#                indent=4,
#                ensure_ascii=False,
#                encoding="utf-8"
#            )
#    

    #============ CSV =============================
    output_csv_file = end_date.strftime(_OUTPUT_CSV_PATTERN)

    # Remove old data
    output_data = [[
            'created','id','happy','category','platform','browser',
            'browser_version','channel','version','user_agent','description',
            'url'
        ]]
    try:
        with gzip.open(output_csv_file, 'rb') as output_csv:
            csv_reader = csv.reader(output_csv, delimiter=',',
                                    quotechar='"', quoting=csv.QUOTE_MINIMAL)
            csv_reader.next()
            for row in csv_reader:
                if row[0] > start_date.strftime('%Y-%m-%d') and row[0] < end_date.strftime('%Y-%m-%d'):
                    output_data.append(row)
    except Exception, err:
        print Exception, err
    
 
    # append new DB data
    with open(_DUMP_SQL_FILE, 'r') as dump_sql:
        if dump_sql:
            dump_query = query_preface + dump_sql.read()
            dump_data = db.execute(dump_query)
        new_data = []
        for row in dump_data:
            new_row = []
            for entry in row:
                if type(entry) == 'str':
                    new_row.append(entry.decode("utf-8").encode('latin-1'))
                else:
                    new_row.append(entry)

            new_data.append(new_row)
            
        output_data += new_data


    # output result

    with gzip.open(output_csv_file, 'w+') as output_csv:
        csv_writer = csv.writer(output_csv, delimiter=',',
                                quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in output_data:
            csv_writer.writerow(row)


if __name__ == "__main__":
    main()
