# -*- coding: utf-8 -*-

'''Collects, calculates and returns telemetry stats'''

import collections
import decimal
from datetime import datetime,timedelta
from flask import json
from functools import wraps
from pprint import pprint
from re import search
from useradvocacy.database import db
from werkzeug.exceptions import Unauthorized, Forbidden, NotFound, BadRequest, Conflict
from werkzeug.datastructures import MultiDict


# ======= HELPERS ==============================================================

def _execute(query):
    results = db.session.execute(query)

    keys = results.keys()
    data = []
    for row in results:
        row_data = {}
        for key in keys:
            entry_type = type(row[key])
            if not row[key]:
                row_data[key] = row[key]
            elif entry_type in [int,long,float]:
                row_data[key] = row[key]
            elif entry_type == decimal.Decimal:
                row_data[key] = float(row[key])
            else:
                row_data[key] = str(row[key])
        data.append(row_data)

    return data

def _get_maxes():

    week_data = _execute(
            'SELECT week FROM telemetry.weekly_telemetry_stats GROUP BY 1 ORDER BY 1 DESC LIMIT 2;'
        )
    version_data = _execute(
            'SELECT version FROM telemetry.weekly_telemetry_stats GROUP BY 1 ORDER BY 1 DESC LIMIT 2;'
        )
    return {
            'week':   {
                    'latest': str(week_data[0]['week']),
                    'previous': str(week_data[1]['week'])
                },
            'version': {
                    'latest': str(version_data[0]['version']),
                    'previous': str(version_data[1]['version'])
                }
        }
#    return {                                       #TODO DELETE
#            'week':   {                            #TODO DELETE
#                    'latest': '34',                #TODO DELETE
#                    'previous': '33'               #TODO DELETE
#                },                                 #TODO DELETE
#            'version': {                           #TODO DELETE
#                    'latest': '2014-12-09',        #TODO DELETE
#                    'previous': '2014-12-02'       #TODO DELETE
#                }                                  #TODO DELETE
#        }                                          #TODO DELETE

def _resolve_oss(target_os_str, base_os_str = None, messages = None):
    if not target_os_str and not base_os_str:
        return 'all', 'all', messages
    return _resolve_params('os', target_os_str, base_os_str, messages)

def _resolve_channels(target_channel_str, base_channel_str = None, messages = None):
    return _resolve_params('channel', target_channel_str, base_channel_str, messages)

def _resolve_params(param, target_str, base_str = None, messages = None):

    if not messages:
        messages = {}

    target, messages = _resolve_param(param, target_str, messages, False)
    base,   messages = _resolve_param(param, base_str,   messages, True )

    if not target or (target != target_str):
        target = base
    elif not base   or (base   != base_str):
        base = target

    return target, base, messages


def _resolve_os(os, messages = None, is_base = False):
    return _resolve_param('os', os, messages, is_base)

def _resolve_channel(channel, messages = None, is_base = False):
    return _resolve_param('channel', channel, messages, is_base)

def _resolve_param(param, param_string, messages = None, is_base = False):
    _PARAMS_INFO = {
            'os':{
                    'default': None,
                    'values': [
                            'all',
                            'mac',
                            'linux',
                            'windows'
                        ]
                },
            'channel':{
                    'default': 'release',
                    'values': [
                            'release',
                            'beta',
                            'aurora',
                            'nightly'
                        ]
                }
        }

    if param not in _PARAMS_INFO.keys():
        raise Exception('Parameter %s not recognized.' % str(param))

    if not messages:
        messages = {}

    if not param_string:
        param_string = _PARAMS_INFO[param]['default']
    elif param_string not in _PARAMS_INFO[param]['values']:
        param_string = _PARAMS_INFO[param]['default']
        label = ('base_' + param) if is_base else param
        messages[label] = '%s %s is not recognized.' % (param,param_string)

    return param_string, messages


def _resolve_date(old_date, messages = None, is_base = False, maxes = None):
    return _resolve_time(
            'date',
            old_date,
            messages = messages,
            is_base = is_base,
            maxes = maxes
        )


def _resolve_version(old_version, messages = None, is_base = False, maxes = None):
    return _resolve_time(
            'version',
            old_version,
            messages = messages,
            is_base = is_base,
            maxes = maxes
        )


def _resolve_time(time_type, old_time,
                  messages = None, is_base = False, maxes = None):
    keywords = ['latest','previous']

    if not messages:
        messages = {}
    if not maxes:
        maxes = _get_maxes()

    if time_type == 'date':
        time_fn = _round_to_tuesday
    else:
        time_fn = int

    new_time = None
    if old_time:
        if old_time in keywords:
            new_time = time_fn(maxes['week'][old_time])
        else:
            try:
                new_time = time_fn(old_time)
            except ValueError:
                label = ('base_' if is_base else '') + time_type
                messages[label] = '%s not recognized: %s' % (label, old_time)

    return new_time, messages


def _round_to_tuesday(str_time):
    dt = datetime.strptime(str_time, '%Y-%m-%d')
    new_dt = dt - timedelta((dt.weekday() - 1)%7)
    return new_dt.strftime('%Y-%m-%d')


# ==============================================================================
# ======= PUBLIC API FUNCTIONS =================================================
# ==============================================================================

# ======= PARAMS ===============================================================

def telemetry_params():
    week_data = _execute(
            'SELECT week FROM telemetry.weekly_telemetry_stats GROUP BY 1 ORDER BY 1;'
        )
    version_data = _execute(
            'SELECT version FROM telemetry.weekly_telemetry_stats GROUP BY 1 ORDER BY 1;'
        )

    weeks    = [row['week']    for row in week_data   ]
    versions = [row['version'] for row in version_data]

    return json.jsonify({
            'latest_week': weeks[-1],
            'prev_week': weeks[-2],
            'weeks': weeks,

            'latest_version': versions[-1],
            'prev_version': versions[-2],
            'versions': versions
        })

# ======= SINGLE STAT ==========================================================
#grouping OR element OR measure REQUIRED
#end_date   OR end_version   (today)
#start_date OR start_version (18 weeks)

#timestep = version|week     ()
#os
#channel

#TODO(rrayborn): Add category as input
def telemetry_stat(args):
    _timesteps = ['version','week']
    messages   = {}
    parameters = {}
    ret = {
            'status':     200,
            'parameters': parameters,
            'results':    {},
            'messages':   messages,
            'count':      0
        }

    maxes = _get_maxes()

    #OS
    os_str = args.pop('os', None)
    os,messages = _resolve_os(os_str, messages)
    if os_str:
        ret['parameters']['os'] = os_str
    #Channel
    channel_str = args.pop('channel', None)
    channel,messages = _resolve_channel(channel_str, messages)
    if channel_str:
        ret['parameters']['channel'] = channel_str

    #Measure/Element/Grouping
    measures  = args.getlist('measures')
    elements  = args.getlist('elements')
    groupings = args.getlist('groupings')
    if measures:
        ret['parameters']['measures'] = measures
        if elements:
            messages['elements'] = 'Elements param ignored because measures was passed.'
        if groupings:
            messages['groupings'] = 'Groupings param ignored because measures was passed.'
    elif elements:
        ret['parameters']['elements'] = elements
        if groupings:
            messages['groupings'] = 'Groupings param ignored because elements was passed.'
    elif groupings:
        ret['parameters']['groupings'] = groupings
    elif not groupings:
        ret['status'] = 400
        messages['groupings'] = 'No measures, elements, or groupings param'
        return json.jsonify(ret) #TODO(rrayborn): throw code: , 400

    #Timestep
    timestep_str = args.pop('timestep', None)
    ret['parameters']['timestep'] = timestep_str
    if not timestep_str:
        timestep = 'week'
    if (timestep_str not in _timesteps):
        timestep = 'week'
        messages['timestep'] = 'Timestep %s is not recognized.' % str(os)
    else:
        timestep = timestep_str

    # Times/Versions
    # dates
    end_date_str = args.pop('end_date', None)
    end_date, messages = _resolve_date(
            end_date_str,
            messages = messages,
            maxes = maxes
        )

    start_date_str = args.pop('start_date', None)
    start_date, messages = _resolve_date(
            start_date_str,
            messages = messages,
            maxes = maxes
        )
    # version
    end_version_str = args.pop('end_version', maxes['version']['latest'])
    end_version, messages = _resolve_version(
            end_version_str,
            messages = messages,
            maxes = maxes
        )

    start_version_str = args.pop('start_version', None)
    start_version, messages = _resolve_version(
            start_version_str,
            messages = messages,
            maxes = maxes
        )

    # date/version
    is_diff = False

    if start_version or end_version:
        if not end_version:
            end_version = min(start_version + 1, maxes['version']['latest'])
            ret['parameters']['start_version'] = start_version_str
        elif not start_version:
            start_version = end_version - 1
            ret['parameters']['end_version']    = end_version_str
        else:
            ret['parameters']['start_version'] = start_version_str
            ret['parameters']['end_version']    = end_version_str

        if start_version >= end_version:
            ret['status'] = 400
            messages['version'] = 'start_version %s >= end_version %s' % (
                    start_version, end_version
                )
            return json.jsonify(ret) #TODO(rrayborn): throw code: , 400

        if start_date_str:
            messages['start_date'] = 'start_date ignored since version provided'
        if end_date_str:
            messages['end_date'] = 'end_date ignored since version provided'

        start_date = None
        end_date   = None

    elif start_date or end_date:
        if not end_date:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = min(
                    (start_dt + timedelta(days=7*6)).strftime('%Y-%m-%d'),
                    maxes['week']['latest']
                )
            ret['parameters']['start_date'] = start_date_str
        elif not start_date:
            end_dt = datetime.strptime(start_date, '%Y-%m-%d')
            start_date = (end_dt - timedelta(days=7*6)).strftime('%Y-%m-%d')
            ret['parameters']['end_date']    = end_date_str
        else:
            ret['parameters']['start_date'] = start_date_str
            ret['parameters']['end_date']   = end_date_str

        if start_date >= end_date:
            ret['status'] = 400
            messages['date'] = 'start_date %s >= end_date %s' % (
                    start_date, end_date
                )
            return json.jsonify(ret) #TODO(rrayborn): throw code: , 400

    else:
        ret['status'] = 400
        messages['date/version'] = 'No version or date given.'
        return json.jsonify(ret) #TODO(rrayborn): throw code: , 400


    # Return unknown parameters
    #TODO(rrayborn): we could use a whitelist here?  I'd hate for misspellings
    #                like 'versoin' to be returned unchecked
    for k,v in args.iteritems():
        ret['parameters'][str(k)] = v

    ret['results'] = _stat_query(
            measures, elements, groupings, os, channel, timestep,
            start_date, end_date,
            start_version, end_version
        )

    ret['count'] = len(ret['results'])

    return json.jsonify(ret) #TODO(rrayborn): throw code: , 200


def _stat_query(measures, elements, groupings, os, channel, timestep,
                 start_date, end_date,
                 start_version, end_version):
    # Query
    where_statements = []
    if measures:
        where_statements.append('stats.measure_name IN("%s")' % '","'.join(measures))
    if elements:
        where_statements.append('elements.name IN("%s")' % '","'.join(elements))
    if groupings:
        where_statements.append('measures.`table` IN("%s")' % '","'.join(groupings))

    if timestep == 'week':
        time_select = 'stats.week AS time'
        time_group_by = 'stats.week'
    else:
        time_select = 'stats.version AS time'
        time_group_by = 'stats.version'

    if start_date or end_date:
        where_statements.append('week >= "%s"' % start_date)
        where_statements.append('week <= "%s"' % end_date)
    if start_version or end_version:
        where_statements.append('version >= "%s"' % start_version)
        where_statements.append('version <= "%s"' % end_version)
    if os:
        where_statements.append('os = "%s"' % os)
    if channel:
        where_statements.append('channel = "%s"' % channel)

    if where_statements:
        where_clause = 'WHERE ' + ' AND '.join(where_statements)
    else:
        where_clause = ''

    query = '''
            SELECT
                %s,
                stats.measure_name         AS measure,
                measures.type              AS type,
                measures.table             AS `table`,
                measures.sort              AS sort,
                elements.category          AS category,
                elements.name              AS alias,
                elements.name              AS element,
                elements.description       AS description,
                elements.x                 AS screenshot_x,
                elements.y                 AS screenshot_y,
                elements.width             AS screenshot_w,
                elements.height            AS screenshot_h,
                screens.file               AS screenshot_file,

                SUM(stats.measure_average*stats.potential_users)/
                    SUM(stats.potential_users) AS `average`,
                SUM(stats.measure_average*stats.potential_users)/
                    SUM(stats.active_users)    AS `nonzero_average`,
                stats.measure_value        AS value,
                SUM(stats.active_users)    AS active_users,
                SUM(stats.potential_users) AS potential_users,
                SUM(stats.users)           AS `count`
            FROM
                telemetry.weekly_telemetry_stats       stats
                LEFT JOIN telemetry.telemetry_measures measures
                        ON(stats.measure_name = measures.name)
                LEFT JOIN telemetry.telemetry_elements elements
                        ON(measures.element_id = elements.id)
                LEFT JOIN telemetry.telemetry_screens  screens
                        ON(elements.screen_id = screens.id)
            %s
            GROUP BY %s,measures.id,elements.id,stats.measure_name,stats.measure_value
            ;
            ''' % (time_select, where_clause, time_group_by)

    data  = _execute(query)

    results = {}
    for row in data:
        measure = row['measure']
        if measure not in results.keys():
            results[measure] = {
                    'table':                row['table'],
                    'category':             row['category'],
                    'measure':              row['measure'],
                    'type':                 row['type'],
                    'alias':                row['alias'],
                    'element':              row['element'],
                    'description':          row['description'],
                    'sort':                 row['sort'],
                    'times':                {}
                }
            if row['screenshot_file']:
                results[measure]['screenshot_x']     = row['screenshot_x']
                results[measure]['screenshot_y']     = row['screenshot_y']
                results[measure]['screenshot_w']     = row['screenshot_w']
                results[measure]['screenshot_h']     = row['screenshot_h']
                results[measure]['screenshot_file']  = row['screenshot_file']

        time_value = row['time']
        time_dict = results[measure]['times']

        if time_value not in time_dict.keys():
            time_dict[time_value] = {}
            time_dict[time_value]['time']            = row['time']
            time_dict[time_value]['potential_users'] = row['potential_users']
            time_dict[time_value]['active_users']    = row['active_users']
            time_dict[time_value]['average']         = row['average']
            time_dict[time_value]['nonzero_average'] = row['nonzero_average']
            time_dict[time_value]['users'] = {}

        user_dict = time_dict[time_value]['users']

        value = row['value']
        range_regex = '^[0-9]+\-[0-9]+$'
        if search(range_regex, value) and int(value.partition('-')[0]) >= 16:
            value = '16+'

        if value not in user_dict.keys():
            user_dict[value] = {'value': value, 'count': 0}

        user_dict[value]['count'] += row['count']

    for measure_result in results.itervalues():
        new_times = []
        old_times = measure_result['times']
        for key in sorted(old_times.iterkeys()):
            new_times.append(old_times[key])
        measure_result['times'] = new_times

    return results

# ======= SUMMARY STATS ========================================================
def telemetry_stats(args):
    messages = {}
    ret = {
            'status':     200,
            'parameters': {},
            'resolved_parameters': {},
            'messages':   messages,
            'count':      0
        }

    maxes = _get_maxes()

    # Times/Versions
    # dates
    target_date_str = args.pop('date', None)
    target_date, messages = _resolve_date(
            target_date_str,
            messages = messages,
            is_base = False,
            maxes = maxes
        )

    base_date_str = args.pop('base_date', None)
    base_date, messages = _resolve_date(
            base_date_str,
            messages = messages,
            is_base = True,
            maxes = maxes
        )
    # version
    target_version_str = args.pop('version', None)
    target_version, messages = _resolve_version(
            target_version_str,
            messages = messages,
            is_base = False,
            maxes = maxes
        )

    base_version_str = args.pop('base_version', None)
    base_version, messages = _resolve_version(
            base_version_str,
            messages = messages,
            is_base = True,
            maxes = maxes
        )
    # date/version
    is_diff = False
    if target_version:
        if target_date_str:
            messages['date'] = 'date ignored since version provided'
        if base_date_str:
            messages['base_date'] = 'base_date ignored since version provided'
        target_date = None
        base_date   = None

        ret['resolved_parameters']['version'] = target_version
        ret['parameters']['version'] = target_version_str

        if base_version:
            if base_version > target_version:
                messages['versions'] = 'version is less than base_version.'

            ret['resolved_parameters']['base_version'] = base_version
            ret['parameters']['base_version'] = base_version_str
            is_diff = True

    elif target_date:
        if target_version_str:
            messages['version'] = 'version ignored since version provided'
        if base_version_str:
            messages['base_version'] = \
                    'base_version ignored since version provided'
        target_version = None
        base_version   = None

        ret['resolved_parameters']['date'] = target_date
        ret['parameters']['date'] = target_date_str

        if base_date:
            if base_date > target_date:
                messages['dates'] = 'date is less than base_date.'

            ret['resolved_parameters']['base_date'] = base_date
            ret['parameters']['base_date'] = base_date_str
            is_diff = True
    else:
        ret['status'] = 400
        messages['date/version'] = 'No version or date given.'
        return json.jsonify(ret) #TODO(rrayborn): throw code: , 400

    #ret['parameters']['is_diff'] = is_diff
    ret['resolved_parameters']['is_diff'] = is_diff

    #OS
    target_os_str = args.pop('os', None)
    base_os_str   = args.pop('base_os', None)

    target_os, base_os, messages = \
            _resolve_oss(target_os_str, base_os_str, messages)

    if target_os:
        ret['resolved_parameters']['os'] = target_os
    if base_os and is_diff:
        ret['resolved_parameters']['base_os'] = base_os
    if target_os_str:
        ret['parameters']['os'] = target_os_str
    if base_os_str and is_diff:
        ret['parameters']['base_os'] = base_os_str
    else:
        base_os = None


    # Channel
    target_channel_str = args.pop('channel', None)
    base_channel_str = args.pop('base_channel', None)

    target_channel, base_channel, messages = \
            _resolve_channels(target_channel_str, base_channel_str, messages)

    if target_channel:
        ret['resolved_parameters']['channel'] = target_channel
    if base_channel and is_diff:
        ret['resolved_parameters']['base_channel'] = base_channel
    if target_channel_str:
        ret['parameters']['channel'] = target_channel_str
    if base_channel_str and is_diff:
        ret['parameters']['base_channel'] = base_channel_str
    else:
        base_channel = None


    # Return unknown parameters
    #TODO(rrayborn): we could use a whitelist here?  I'd hate for misspellings
    #                like 'versoin' to be returned unchecked
    for k,v in args.iteritems():
        ret['parameters'][str(k)] = v

#    return ret #TODO DELETE

    # Do the queries
    data = _stats_query(
            target_date, target_version, target_os, target_channel
        )

    if is_diff:
        data = _stats_query(
                base_date, base_version, base_os, base_channel, data
            )

    ret['count']   = len(data)
    ret['results'] = data

    return json.jsonify(ret) #TODO(rrayborn): throw code: , 200


def _stats_query(week, version, os, channel, target = None):
    where_statements = []
    if week:
        where_statements.append('week = "%s"' % week)
    elif version:
        where_statements.append('version = %s' % version)
    if os and os!='all':
        where_statements.append('os = "%s"' % os)
    if channel:
        where_statements.append('channel = "%s"' % channel)

    if where_statements:
        where_clause = 'WHERE ' + ' AND '.join(where_statements)
    else:
        where_clause = ''
    query = '''
            SELECT
                stats.measure_name         AS measure,
                measures.type              AS type,
                measures.table             AS `table`,
                measures.sort              AS sort,
                elements.category          AS category,
                elements.name              AS alias,
                elements.name              AS element,
                elements.description       AS description,
                elements.x                 AS screenshot_x,
                elements.y                 AS screenshot_y,
                elements.width             AS screenshot_w,
                elements.height            AS screenshot_h,
                screens.file               AS screenshot_file,

                SUM(stats.measure_average*stats.potential_users)/
                    SUM(stats.potential_users) AS `average`,
                SUM(stats.measure_average*stats.potential_users)/
                    SUM(stats.active_users)    AS `nonzero_average`,
                stats.measure_value        AS value,
                SUM(stats.active_users)    AS active_users,
                SUM(stats.potential_users) AS potential_users,
                COALESCE(SUM(stats.users),0) AS `count`
            FROM
                telemetry.weekly_telemetry_stats       stats
                LEFT JOIN telemetry.telemetry_measures measures
                        ON(stats.measure_name = measures.name)
                LEFT JOIN telemetry.telemetry_elements elements
                        ON(measures.element_id = elements.id)
                LEFT JOIN telemetry.telemetry_screens  screens
                        ON(elements.screen_id = screens.id)
            %s
            GROUP BY measures.id,elements.id,stats.measure_name,stats.measure_value
            ;
            ''' % where_clause
    data = _execute(query)

    if target: # target exists already, so this is base
        ret           = target
        status_label  = 'old'
        prefix        = 'base_'
    else:
        ret           = {}
        status_label  = 'new'
        prefix        = ''

    potential_users_label = prefix + 'potential_users'
    active_users_label    = prefix + 'active_users'
    average_label         = prefix + 'average'
    count_label           = prefix + 'count'
    nonzero_average_label = prefix + 'nonzero_' + 'average'

    for row in data:
        measure = row['measure']
        if measure not in ret.keys():
            ret[measure] = {
                    'table':                row['table'],
                    'category':             row['category'],
                    'measure':              row['measure'],
                    'type':                 row['type'],
                    'alias':                row['alias'],
                    'element':              row['element'],
                    'description':          row['description'],
                    'sort':                 row['sort'],
                    'users':                {}
                }
            if row['screenshot_file']:
                ret[measure]['screenshot_x']     = row['screenshot_x']
                ret[measure]['screenshot_y']     = row['screenshot_y']
                ret[measure]['screenshot_w']     = row['screenshot_w']
                ret[measure]['screenshot_h']     = row['screenshot_h']
                ret[measure]['screenshot_file']  = row['screenshot_file']

        if potential_users_label not in ret[measure].keys():
            ret[measure][potential_users_label] = row['potential_users']
            ret[measure][active_users_label]    = row['active_users']
            ret[measure][average_label]         = row['average']
            ret[measure][nonzero_average_label] = row['nonzero_average']
            if 'measure_status' not in ret[measure].keys():
                ret[measure]['measure_status'] = status_label
            elif ret[measure]['measure_status'] != status_label:
                ret[measure]['measure_status'] = 'both'


        value = row['value']
        range_regex = '^[0-9]+\-[0-9]+$'
        if search(range_regex, value) and int(value.partition('-')[0]) >= 16:
            value = '16+'

        if value not in ret[measure]['users'].keys():
            ret[measure]['users'][value] = {'value': value}
        if count_label not in ret[measure]['users'][value].keys():
            ret[measure]['users'][value][count_label] = 0
        ret[measure]['users'][value][count_label] += row['count']

    return ret


#====== HELPERS ================================================================


def main():
    import json as built_in_json
    print(built_in_json.dumps(telemetry_stats(
            MultiDict([
                    ('version', '31'),
                    ('base_version', '30'),
                    ('base_date', '2014-01-29'),
                    ('os', 'linux')
                ])
        ),
        sort_keys=True,
        indent=4,
        separators=(',', ': ')))
    print(built_in_json.dumps(telemetry_stats(
            MultiDict([
                    ('date', '2014-12-11'),
                    ('base_date', '2014-12-02'),
                    ('os', 'windows')
                ])
        ),
        sort_keys=True,
        indent=4,
        separators=(',', ': ')))
    print(built_in_json.dumps(telemetry_stat(
            MultiDict([
                    ('measure', 'home-button'),
                    ('timestep', 'week'),
                    ('end_version', '31'),
                    ('start_version', '30'),
                    ('end_date', '2014-01-29'),
                    ('os', 'linux')
                ])
        ),
        sort_keys=True,
        indent=4,
        separators=(',', ': ')))
    print(built_in_json.dumps(telemetry_stat(
            MultiDict([
                    ('measure', 'home-button'),
                    ('timestep', 'week'),
                    ('end_date', '2014-12-09'),
                    ('start_date', '2014-12-02'),
                    ('channel', 'aurora')
                ])
        ),
        sort_keys=True,
        indent=4,
        separators=(',', ': ')))

if __name__ == "__main__":
   main()
