#!/usr/local/bin/python

import sys
from datetime import datetime,timedelta,time

from lib.general.simplewarn import warn
from pipelines.alert_pipeline.word_alert import process_alerts

import argparse


def main():
    args = parseArgs()
    print args
    if args.debug:
        file = args.outfile
        print >> file, 'product,end_time,word,base_pct,after_pct,base_count,after_count,severity\n'

    date      = datetime.strptime(args.date, '%Y-%m-%d')
    now       = datetime.now()
    increment = timedelta(days = 1)
    if args.product.lower() == 'desktop':
        times = [time(0), time(6), time(12), time(18)]
    else:
        times = [time(6)]

    while(date < now):
        for t in times:
            dt_to_run = datetime.combine(date.date(), t)
            if (dt_to_run < now):
                # print dt_to_run.isoformat()
                process_alerts(args.product, now = dt_to_run,
                               debug = args.debug, debug_file = args.outfile, 
                               email = False)
        date += increment
    
    if args.debug:
        file.close()


def parseArgs():
    parser = argparse.ArgumentParser(description='Backfill Input Alerts.')
    parser.add_argument('--debug', '-d',
                        action = 'store_true', 
                        help = 'Whether we should emit alerts or write to a file instead')
    parser.add_argument('--date','-s',
                        action = 'store',
                        default = '2015-01-01', 
                        help = 'Start date for Alerts generation omit for running once')
    parser.add_argument('--outfile','-o',
                        type = argparse.FileType('w'),
                        default=sys.stdout,
                        help = 'File to write to')
    parser.add_argument('--product',
                        action = 'store',
                        default = 'desktop', 
                        help = 'Product to backfill for. e.g. "desktop"/"android"')
    return parser.parse_args()


if __name__ == '__main__':
    main()
