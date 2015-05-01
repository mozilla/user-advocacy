#!/usr/local/bin/python

import sys
import datetime as dt

from lib.general.simplewarn import warn
from pipelines.alert_pipeline.android_word_alert import process_alerts

import argparse



def main():
    args = parseArgs()
    print args
    date = dt.datetime.strptime(args.date, '%Y-%m-%d')
    now = dt.datetime.now()
    increment = dt.timedelta(days = 1)
    times = [dt.time(6)]
    if args.debug:
        file = args.outfile
        print >> file, "end_time,word,base_pct,after_pct,base_count,after_count,severity\n"
    while(date < now):
        for time in times:
            dt_to_run = dt.datetime.combine(date.date(), time)
            if (dt_to_run < now):
                # print dt_to_run.isoformat()
                process_alerts(dt_to_run, debug = args.debug, debug_file = args.outfile, 
                                email = False)
        date += increment
    if args.debug:
        file.close()

def parseArgs():
    parser = argparse.ArgumentParser(description='Backfill Android Input Alerts.')
    parser.add_argument('--debug', '-d', action = 'store_true', 
        help = 'Whether we should emit alerts or write to a file instead')
    parser.add_argument('--date','--startdate','-s', action = 'store',
        default = '2015-01-01', 
        help = 'Start date for Alerts generation omit for running once')
    parser.add_argument('--outfile','-o', type = argparse.FileType('w'),
        default=sys.stdout,
        help = 'File to write to')
    return parser.parse_args()

if __name__ == '__main__':
    main()
