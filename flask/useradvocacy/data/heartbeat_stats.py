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


def heartbeat_stats_return(args):
    ret = {}

    # create WHERE clause

    where_statements = []
    
    date_start    = args.get('date_start')
    date_end      = args.get('date_end')
    if date_start:
        where_statements.append('`date` >= "%s"' % date_start)
    if date_end:
        where_statements.append('`date` <= "%s"' % date_end)
    
    version_start = args.get('version_start')
    version_end   = args.get('version_end')
    if version_start:
        where_statements.append('version >= "%s"' % version_start)
    if version_end:
        where_statements.append('version <  "%s"' % version_end)
    
    channels = args.get('channels') #TODO(rrayborn): make list handler
    if channels:
        where_statements.append('lower(channel) LIKE "%%%s%%"' % channels.lower())
    
    question_id = args.get('question_id')
    if question_id:
        where_statements.append('lower(question_id) = "%s"' % question_id.lower())

    is_response = args.get('is_response') is not None
    if is_response:
        where_statements.append('is_response')

    platform = args.get('platform')
    if platform:
        where_statements.append('lower(platform) LIKE "%%%s%%"' % platform.lower())

    where_clause = 'WHERE %s ' % ' AND '.join(where_statements)

    query = '''
            SELECT
                survey_id,
                question_id,
                question_text,
                date,
                channel,
                version,
                platform,
                max_score,
                is_response,
                score,
                SUM(volume)
            FROM sentiment.daily_heartbeat_stats
            WHERE %s
            GROUP BY 1,2,3,4,5,6,7,8,9,10
        ;''' % (' AND\n '.join(where_statements))

    print query
    data = _execute(query)

    ret['count'] = len(data)
    ret['results'] = data

    return json.jsonify(ret) #TODO(rrayborn): throw code: , 200


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

