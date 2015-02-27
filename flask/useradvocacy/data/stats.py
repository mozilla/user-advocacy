# -*- coding: utf-8 -*-

'''Collects, calculates and returns stats'''

import collections
import decimal
from datetime import datetime,timedelta
from flask import json
from functools import wraps
from useradvocacy.database import db
from werkzeug.exceptions import Unauthorized, Forbidden, NotFound, BadRequest, Conflict
from werkzeug.datastructures import MultiDict


_MIN_DATE = '2013-09-01'

_NONDAILY_MEASURES = [
        'input_average',
        'input_volume',
        'play_average',
        'play_volume',
        'sumo_forum_posts',
        'sumo_inproduct_visits',
        'sumo_forum_unanswered_pct',
        'heartbeat_average',
        'heartbeat_response_rate',
        'heartbeat_volume',
        'adis'
    ]

_DAILY_MEASURES = list(_NONDAILY_MEASURES)
_DAILY_MEASURES.extend(['input_average_7_days'])

_ALL_PRODUCTS = [
        'Firefox',
        'Firefox for Android'
    ]

_ALL_CHANNELS = [
        'release',
        'beta',
        'aurora',
        'nightly',
        'other'
    ]

_ALL_PERIODS = [
        'day',
        'week',
        'month',
        'version'
    ]

# def main():
#     import json as built_in_json
#     '''
#     print(built_in_json.dumps(stats_return(
#             MultiDict([
#                     ('measures', 'input_volume'),
#                     ('measures', 'input_average'),
#                     ('measures', 'gplay_volume'),
#                     ('channels', 'beta'),
#                     ('products', 'Firefox'),
#                     ('period', 'week'),
#                     ('version_start', '27'),
#                     ('version_end', '30')
#                 ])
#         ),
#         sort_keys=True,
#         indent=4,
#         separators=(',', ': ')))'''
#     print(built_in_json.dumps(stats_return(
#             MultiDict([
#                     ('measures', 'sumo_forum_posts'),
#                     ('measures', 'input_average_7_days'),
#                     ('channels', 'release'),
#                     ('products', 'Firefox'),
#                     ('period', 'month'),
#                     ('period_delta', 9),
#                     ('date_start', '2014-01-15')
#                 ])
#         ),
#         sort_keys=True,
#         indent=4,
#         separators=(',', ': ')))
#     print(built_in_json.dumps(stats_return(
#             MultiDict([
#                     ('measures', 'sumo_forum_unanswered_pct'),
#                     ('measures', 'input_average_7_days'),
#                     ('products', 'Firefox for Android'),
#                     ('period', 'day'),
#                     ('date_end', '2014-10-09')
#                 ])
#         ),
#         sort_keys=True,
#         indent=4,
#         separators=(',', ': ')))

def stats_return(args):

    ret = {
            'status':200,
            'messages':{},
            'parameters':{},
            'count':0
        }


    # Products ###ERRR
    corrected_products,unknown_products = _validate_parameters(
            args.getlist('products'),
            _ALL_PRODUCTS
        )
    
    if unknown_products:
        ret['messages']['products'] = 'Unknown products ignored: %s' % \
                unknown_products

    if not corrected_products:
        corrected_products = ['Firefox']

    ret['parameters']['products'] = corrected_products

    # Channels
    corrected_channels,unknown_channels = _validate_parameters(
            args.getlist('channels'),
            _ALL_CHANNELS
        )
    
    if unknown_channels:
        if 'all' in unknown_channels:
            corrected_channels = list(_ALL_CHANNELS)
        else:
            ret['messages']['channels'] = 'Unknown channels ignored: %s' % \
                    unknown_channels

    if not corrected_channels:
        corrected_channels = list(_ALL_CHANNELS)

    ret['parameters']['channels'] = corrected_channels

    # Dates

    #start
    version_start = args.get('version_start')
    date_start = args.get('date_start')

    if version_start:
        version_start = int(version_start)
        if date_start:
            ret['messages']['dates'] = 'date_start ignored since version_start exists'
        
        min_channel = _get_min_channel(corrected_channels)
        query = 'SELECT %s_start_date AS start_date FROM sentiment.release_info where version = %s;' % \
            (min_channel, version_start)
        start_date = _execute(query)[0]['start_date']
    elif date_start:
        start_date = date_start
    else:
        start_date = None

    #end
    version_end = args.get('version_end')
    date_end = args.get('date_end')

    if version_end:
        version_end = int(version_end)
        if date_end:
            ret['messages']['dates'] = 'date_end ignored since version_end exists'
        max_channel = _get_max_channel(corrected_channels)
        query = 'SELECT %s_end_date AS end_date FROM sentiment.release_info where version = %s;' % \
            (max_channel, version_end)
        end_date = _execute(query)[0]['end_date']
    elif date_end:
        end_date = date_end
    else:
        end_date = None
    

    #period
    period = args.get('period')
    if period:
        if period not in _ALL_PERIODS:
            ret['messages']['period'] = 'period ignored since period %s is unknown.' \
                    % period
            corrected_period = 'day'
        else:
            corrected_period = period
    elif version_start or version_end:
        corrected_period = 'version'
    else:
        corrected_period = 'day'

    ret['parameters']['period'] = corrected_period

    #delta
    period_delta = args.get('period_delta')
    if start_date and end_date and period_delta:
        ret['messages']['period_delta'] = 'period_delta ignored since other ' + \
                'information present to derive start and end dates.'
    else:
        if period_delta:
            period_delta = int(period_delta)
        if corrected_period == 'day':
            if not period_delta:
                period_delta = 90
            corrected_period_delta = period_delta - 1
        elif corrected_period == 'week':
            if not period_delta:
                period_delta = 18
            corrected_period_delta = 7*period_delta - 1
        elif corrected_period == 'month':
            if not period_delta:
                period_delta = 3
            #TODO(rrayborn): make this actual month diffs
            corrected_period_delta = 31*period_delta - 1
        else: #corrected_period == 'version':
            if not period_delta:
                period_delta = 3
            #TODO(rrayborn): make this actual version diffs
            corrected_period_delta = 6*7*period_delta - 1
    ret['parameters']['period_delta'] = corrected_period_delta
    
    #resolve start/end dates if they don't exist
    two_days_ago_datetime = datetime.today() - timedelta(days=2)
    min_datetime = datetime.strptime(_MIN_DATE, "%Y-%m-%d")
    if start_date and end_date:
        pass
    elif start_date and not end_date:
        start_datetime = datetime.strptime(start_date, "%Y-%m-%d")
        end_datetime = start_datetime + timedelta(days=corrected_period_delta)
        if end_datetime > two_days_ago_datetime:
            end_date = two_days_ago_datetime.strftime('%Y-%m-%d')
            ret['messages']['period_delta'] = 'Calculated end date is greater ' + \
                    'than %s, using %s' % (end_date, end_date)
        else:
            end_date = end_datetime.strftime('%Y-%m-%d')
    else: # not start_date:
        if not end_date:
            end_date = two_days_ago_datetime.strftime('%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, "%Y-%m-%d")
        start_datetime = end_datetime - timedelta(days=corrected_period_delta)
        if start_datetime < min_datetime:
            start_date = two_days_ago_datetime.strftime('%Y-%m-%d')
            ret['messages']['period_delta'] = 'Calculated start date is greater ' + \
                    'than %s, using %s' % (start_date, start_date)
        else:
            start_date = start_datetime.strftime('%Y-%m-%d')
    
    ret['parameters']['version_start'] = version_start if version_start else ''
    ret['parameters']['date_start']    = start_date
    ret['parameters']['version_end']   = version_end if version_end else ''
    ret['parameters']['date_end']      = end_date

    # Measures
    if corrected_period == 'day':
        master_list = _DAILY_MEASURES
    else:
        master_list = _NONDAILY_MEASURES

    corrected_measures,unknown_measures = _validate_parameters(
            args.getlist('measures'),
            master_list
        )
    
    if corrected_measures:
        if unknown_measures:
            ret['messages']['measures'] = 'Unknown measures ignored: %s' % \
                        ','.join(unknown_measures)
    
    else: # Error
        ret['status'] = 400

        if unknown_measures:
            ret['messages']['measures'] = 'No correct measures found.  ' + \
                    'Unknown measures ignored: %s.' % str(unknown_measures)
        else:
            ret['messages']['measures'] = 'No correct measures found'
            return json.jsonify(ret) #TODO(rrayborn): throw code: , 400
    ret['parameters']['measures'] = corrected_measures

    # do date math
    select_statements = []
    where_statements = []
    if corrected_period == 'day':
        select_statements.append('`date`')
        where_statements.append(
                '`date` >= "%s" AND `date` <= "%s"' % \
                (start_date, end_date)
            )
    elif corrected_period == 'week':
        select_statements.append(
                'DATE_SUB(`date`, INTERVAL DAYOFWEEK(`date`)-1 DAY) AS `date`')
        where_statements.append(
                ('`date` >= DATE_SUB("%s", INTERVAL DAYOFWEEK("%s")-1 DAY) ' + \
                'AND `date` < DATE_SUB("%s", INTERVAL DAYOFWEEK("%s")-8 DAY)') % \
                (start_date, start_date, end_date, end_date)
            )
    elif corrected_period == 'month':
        select_statements.append('DATE_FORMAT(`date`, "%%Y-%%m-01") AS `date`')
        where_statements.append(
                ('`date` >= DATE_FORMAT("%s", "%%%%Y-%%%%m-01") ' + \
                'AND `date` < DATE_FORMAT("%s", "%%%%Y-%%%%m-32")') % \
                (start_date, end_date)
            )
    else: #corrected_period == 'version':
        select_statements.append('version')
        where_statements.append(
                '`date` >= "%s" AND `date` <= "%s"' % (start_date, end_date)
            )

    # create WHERE clause
    channel_statements = []
    
    print "||".join(channel_statements)
    
    if 'other' in corrected_channels:
        channel_statements.append('channel IS NULL') 
        corrected_channels.remove('other')
    if corrected_channels:
        channel_statements.append('channel IN("%s")' % '","'.join(corrected_channels))
    where_statements.append('(%s)' % ' OR '.join(channel_statements))

    where_clause = 'WHERE %s ' % ' AND '.join(where_statements)

    # create FROM clause
    if 'Firefox' in corrected_products:
        if 'Firefox for Android' in corrected_products:
            #TODO(rrayborn), add multi-product logic
            ret['status'] = 400
            ret['messages']['products'] = 'Multi-product not yet implemented! ' + \
                        'Contact rrayborn for an ETA.'
            return json.jsonify(ret) #TODO(rrayborn): throw code: , 400
        else:
            from_clause = ' FROM sentiment.daily_desktop_stats desktop '
    else: # 'Firefox for Android' in corrected_products:
        from_clause = ' FROM sentiment.daily_mobile_stats mobile '
    
    # create SELECT clause
    if 'input_average'             in corrected_measures:
        select_statements.append(
                'SUM(input_average*input_volume)/SUM(input_volume) AS input_average'
            )
    if 'input_average_7_days'        in corrected_measures:
        select_statements.append(
                'AVG(input_average_7_days) AS input_average_7_days'
            )
    if 'input_volume'              in corrected_measures:
        select_statements.append(
                'SUM(input_volume) AS input_volume'
            )
    if 'heartbeat_average'         in corrected_measures:
        select_statements.append(
                'SUM(heartbeat_average*heartbeat_volume)/SUM(heartbeat_volume) AS heartbeat_average'
            )
    if 'heartbeat_response_rate'  in corrected_measures:
        select_statements.append(
                'SUM(heartbeat_response_rate*heartbeat_volume)/SUM(heartbeat_volume) AS heartbeat_response_rate'
            )
    if 'heartbeat_volume'          in corrected_measures:
        select_statements.append(
                'SUM(heartbeat_volume) AS heartbeat_volume'
            )
    if 'play_average'              in corrected_measures:
        select_statements.append(
                'SUM(play_average*play_volume)/SUM(play_volume) AS play_average'
            )
    if 'play_volume'               in corrected_measures:
        select_statements.append(
                'SUM(play_volume) AS play_average'
            )
    if 'sumo_forum_posts'          in corrected_measures:
        select_statements.append(
                'SUM(sumo_posts) AS sumo_forum_posts'
            )
    if 'sumo_inproduct_visits'     in corrected_measures:
        select_statements.append(
                'SUM(sumo_in_product_views) AS sumo_inproduct_visits'
            )
    if 'sumo_forum_unanswered_pct' in corrected_measures:
        select_statements.append(
                '100*COALESCE(AVG(sumo_unanswered_3_days/sumo_posts),0) AS sumo_forum_unanswered_pct'
            )
    if 'adis'                      in corrected_measures:
        select_statements.append(
                'AVG(adis) AS adis'
            )

    select_clause = 'SELECT %s ' % ', '.join(select_statements) 
    group_by_clause = 'GROUP BY 1'

    query = ' '.join(
            [select_clause, from_clause, where_clause, group_by_clause]
        ) + ';'
    print query
    data = _execute(query)

    ret['count'] = len(data)
    ret['results'] = data

    return json.jsonify(ret) #TODO(rrayborn): throw code: , 200



def _validate_parameters(given, master):
    passed_counter = collections.Counter(given)
    master_counter = collections.Counter(master)
    corrected = list((master_counter & passed_counter).elements())
    unknown = list((passed_counter - master_counter).elements())
    return corrected, unknown



def _execute(query):
    results = db.session.execute(query)

    keys = results.keys()
    data = []
    for row in results:
        row_data = {}
        for key in keys:
            entry_type = type(row[key])
            if entry_type in [int,long,float]:
                row_data[key] = row[key]
            elif entry_type == decimal.Decimal:
                row_data[key] = float(row[key])
            else:
                row_data[key] = str(row[key])
        data.append(row_data)

    return data


def _get_min_channel(channels):
    if 'nightly' in channels:
        return 'nightly'
    if 'aurora' in channels:
        return 'aurora'
    if 'beta' in channels:
        return 'beta'
    else:
        return 'release'

def _get_max_channel(channels):
    if 'release' in channels:
        return 'release'
    if 'beta' in channels:
        return 'beta'
    if 'aurora' in channels:
        return 'aurora'
    if 'nightly' in channels:
        return 'nightly'
    else:
        return 'release'


if __name__ == "__main__":
   main()
