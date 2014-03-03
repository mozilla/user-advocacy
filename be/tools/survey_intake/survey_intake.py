#!/usr/local/bin/python

"""
Converts survey result CSV files to MySQL tables.
"""

__author__ = "Rob Rayborn"
__copyright__ = "Copyright 2014, The Mozilla Foundation"
__license__ = "MPLv2"
__maintainer__ = "Rob Rayborn"
__email__ = "rrayborn@mozilla.com"
__status__ = "Development"


import argparse
import json
from pprint import pprint
import re
import sys
import urllib2

# TODO(rrayborn): Clean up the path stuff here
sys.path.append('/home/rrayborn/Documents/moz-dev/user-advocacy/be/lib')
from simple_db import SimpleDB


def survey_get_request(survey_id, command, user, password):
    """ Executes a get requests for Survey Gizmo's API.

    Keyword arguments:
    survey_id -- The survey ID that we want to pull data for
    command -- The command to execute 
            (e.g. '', 'surveyquestion', 'surveyresponse')
    user -- The username of the Survey Gizmo user 
    password -- The password of the Survey Gizmo user 
    """
    base_url = 'https://restapi.surveygizmo.com/head/survey'
    authstring = 'user:pass=%s:%s' % (user, password)
    url_data = urllib2.urlopen('%s/%s/%s?%s' % \
            (base_url, survey_id, command, authstring))
    return json.load(url_data)['data']

def to_sql(val, sql_type = 'TEXT'):
    """ Converts the value to the inline representation that SQL would use.
    i.e. 'cats' => '"cats"'
         '0' == FLOAT => 0.0

    Keyword arguments:
    val -- the value to convert
    sql_type -- the SQL type to convert to (default 'TEXT')
    """
    if sql_type == 'BOOL':
        if val and (str(val).lower() != 'false') and (str(val).lower() != 'f') \
                and (str(val).lower() != '0'):
            return '1'
        else:
            return '0'
    elif not val:
        return 'NULL'
    elif sql_type == 'TEXT' or re.search(r'VARCHAR\(.*\)', sql_type):
        return '"'+str(val)+'"'
    elif sql_type == 'INT':
        return str(int(val))
    elif sql_type == 'FLOAT':
        return str(float(val))
    elif sql_type == 'DATETIME':
        # TODO(rrayborn): date validation 
        #       (it's also done in MySQL, so it's not a huge deal to ignore)
        return '"'+str(val)+'"'
    else:
        raise Error('Type %s not recognized.' % sql_type)




class SurveyDefinition():
    def __init__(self, survey_metadata_json = None, \
            question_metadata_json = None, responses_json = None):
        self.metadata_sql_types = {
                'survey_id':             'INT',
                'id':                    'INT',
                'is_test_data':          'BOOL',
                'contact_id':            'INT',
                'date_submitted':        'DATETIME',
                'response_id':           'INT',
                's_response_comment':    'TEXT',
                'status':                'VARCHAR(100)',
                'portal_relationship':   'VARCHAR(100)',
                'standard_comments':     'TEXT',
                'standard_geocity':      'VARCHAR(100)',
                'standard_geocountry':   'VARCHAR(100)',
                'standard_geodma':       'INT',
                'standard_geopostal':    'VARCHAR(100)',
                'standard_georegion':    'VARCHAR(100)',
                'standard_ip':           'VARCHAR(100)',
                'standard_lat':          'FLOAT',
                'standard_long':         'FLOAT',
                'standard_referer':      'TEXT',
                'standard_responsetime': 'INT',
                'standard_useragent':    'VARCHAR(100)'
            }
        self.metadata_aliases = {
                'id': 'id', 
                'created_on': 'created_on', 
                'title': 'name', 
                'internal_title': 'internal_name'
            }

        self.question_definitions = {}
        self.metadata = {}
        self.responses = []

        if survey_metadata_json:
            self.set_survey_metadata_from_json(survey_metadata_json)
            if question_metadata_json:
                self.add_questions_from_json(question_metadata_json)
                if responses_json:
                    self.add_responses(responses_json)

    # ==== Metadata ============================================================
    def set_survey_metadata(self, key, value):
        if key not in self.metadata_aliases:
            raise Exception('%s not a valid metadata key (%s)' % \
                    (key, self.metadata_aliases))
        self.metadata[key] = to_sql(value)

    def set_survey_metadata_from_json(self, survey_metadata_json):
        self.metadata = dict((self.metadata_aliases[k],v) \
                for k, v in survey_metadata_json.iteritems() \
                if k in self.metadata_aliases)

    # ==== Questions ===========================================================
    def get_question(self, question_id, option_id):
        question_id = str(question_id)
        option_id = str(option_id)
        if question_id not in self.question_definitions:
            raise Exception('Question ID: $s not found' % question_id)
        elif option_id not in self.question_definitions[question_id]:
            if len(self.question_definitions[question_id]) == 1:
                return self.question_definitions[question_id].values()[0]
            else:
                raise Exception(
                        'Repeated Option ID:%s for same Question ID: %s' 
                        % (question_id, option_id)
                    )
        else:
            return self.question_definitions[question_id][option_id]

    def _add_question(self, question_dict):
        question_id = str(question_dict['question_id'])
        option_id = str(question_dict['option_id'])
        if question_id not in self.question_definitions:
            self.question_definitions[question_id] = {}
        self.question_definitions[question_id][option_id] = question_dict

    def add_question(self, question_id, question_internal_name, question_name, 
                     survey_type, option_id, option_name, option_internal_name, 
                     field_name, sql_type):
        self._add_question({
                'question_id':            str(question_id),
                'question_internal_name': str(question_internal_name),
                'question_name':          str(question_name),
                'survey_type':            str(survey_type),
                'option_id':              str(option_id),
                'option_name':            str(option_name),
                'option_internal_name':   str(option_internal_name),
                'field_name':             str(field_name),
                'sql_type':               str(sql_type)
            })

    def add_questions_from_json(self, question_metadata_json):
        for question in question_metadata_json:
            question_id = question['id']
            question_internal_name = \
                    str(question['shortname']).replace('"','\'')
            question_name = str(question['title']['English']).replace('"','\'')
            survey_type = question['_subtype']


            if survey_type == 'checkbox':
                for option in question['options']:
                    option_id = option['id']
                    option_name = option['title']['English']
                    option_internal_name = option['value']
                    field_name = question_internal_name + '_' + \
                            option_internal_name
                    sql_type = 'BOOL'

                    self.add_question(question_id, question_internal_name, 
                        question_name, survey_type, option_id, option_name, 
                        option_internal_name, field_name, sql_type)

                    if 'other' in option['properties']:
                        field_name = '_'.join([question_internal_name, 
                                               option_internal_name ,'comment'])
                        sql_type = 'TEXT'
                        option_id = str(option_id) + '-other'

                        self.add_question(question_id, question_internal_name, 
                                          question_name, survey_type, option_id,
                                          option_name, option_internal_name,
                                          field_name, sql_type)
            else:
                option_id = ''
                option_name = ''
                option_internal_name = ''
                field_name = question_internal_name
                sql_type = ''

                if survey_type in ['textbox', 'essay', 'radio', 'menu']:
                    sql_type =  'TEXT'
                elif survey_type == 'slider':
                    sql_type =  'INT'
                elif survey_type in ['instructions']:
                    continue
                else:
                    raise Exception('Question type: %s not currently supported.'
                                    % survey_type)

                self.add_question(question_id, question_internal_name,
                                  question_name, survey_type, option_id, 
                                  option_name, option_internal_name, field_name,
                                  sql_type)

    # ==== Responses ===========================================================
    def add_responses(self, responses_json):
        for response_json in responses_json:

            response = SurveyResponse()
            response.set_metadata_from_json(response_json)
            response.set_id(response_json['id'])

            data = {}

            for question_key_json, question_value_json in \
                    response_json.iteritems():
                question_id_re = re.search(r'\[question\(([0-9]+)\).*',
                                           question_key_json)
                if not question_id_re:
                    continue
                question_id = question_id_re.group(1)

                option_id = ''
                option_id_re = r'.*option\("{0,1}([0-9A-Za-z\-]+)"{0,1}\).*'
                option_id_result = re.search(option_id_re, question_key_json)
                if option_id_result
                    option_id = option_id_result.group(1)

                question = self.get_question(question_id, option_id)
                response.set_data(question['field_name'], 
                                  to_sql(question_value_json, 
                                         question['sql_type']))

            self.responses.append(response)

        return self.responses

    # ==== Object ==============================================================
    def save(self, db):

        # Create Response Metadata Table
        response_metadata_table = \
                '%s_response_metadata' % self.metadata['internal_name']

        db.drop_table(response_metadata_table)
        sql = 'CREATE TABLE %s (\n' % response_metadata_table
        for k,v in self.metadata_sql_types.iteritems():
            sql += '  %s %s,\n' % (k, v)
        sql += 'PRIMARY KEY (id));'
        db.execute(sql)



        # Create Response Data Table
        response_data_table = \
                '%s_response_data' % self.metadata['internal_name']
        db.drop_table(response_data_table)
        # Create Table
        sql = 'CREATE TABLE %s (\n' % response_data_table
        sql += '  id INT,\n'
        for question_id in self.question_definitions:
            for option_id in self.question_definitions[question_id]:
                question = self.question_definitions[question_id][option_id]
                sql += '  %s %s,\n' % \
                        (question['field_name'], question['sql_type'])
        sql += 'PRIMARY KEY (id));'
        db.execute(sql)

        # Save Responses
        for response in self.responses:
            response.save(db, self.metadata['internal_name'])

        # Create Meta tables
        # TODO(rrayborn): Create metadata tables to audit our mappings later.  
        # Not required for MVP
"""
if not db.execute('SHOW TABLES WHERE tables_in_surveys = "survey_metadata";'):
    db.execute(
            '''CREATE TABLE survey_metadata(
            id INT NOT NULL,
            created_on DATETIME NOT NULL,
            name TEXT,
            internal_name VARCHAR(50) NOT NULL,
            PRIMARY KEY (id)
            );'''
      )
if not db.execute('SHOW TABLES WHERE tables_in_surveys = "question_metadata";'):
    db.execute(
            '''CREATE TABLE question_metadata(
            survey_id INT NOT NULL,
            question_id INT NOT NULL,
            internal_name VARCHAR(50) NOT NULL,
            name TEXT,
            python_type VARCHAR(50),
            survey_type VARCHAR(50),
            FOREIGN KEY (survey_id) 
                REFERENCES survey_metadata(id)
                ON DELETE CASCADE
            );'''
        )

    db.execute(
            '''CREATE TABLE %s (
            survey_id INT,
            question_id INT,
            internal_name VARCHAR(100),
            name TEXT,
            python_type VARCHAR(100),
            survey_type VARCHAR(100),
            ''' % response_data_table
        )
"""



class SurveyResponse():
    def __init__(self):
        self.aliases = {
                'survey_id':        'survey_id',                       
                'id':               'id',                              
                'is_test_data':     'is_test_data',                    
                'contact_id':       'contact_id',                      
                'datesubmitted':    'date_submitted',                   
                'responseID':       'response_id',                      
                'sResponseComment': 's_response_comment',                
                'status':           'status',                          
                '[variable("PORTAL_RELATIONSHIP")]':   'portal_relationship',  
                '[variable("STANDARD_COMMENTS")]':     'standard_comments',    
                '[variable("STANDARD_GEOCITY")]':      'standard_geocity',     
                '[variable("STANDARD_GEOCOUNTRY")]':   'standard_geocountry',  
                '[variable("STANDARD_GEODMA")]':       'standard_geodma',      
                '[variable("STANDARD_GEOPOSTAL")]':    'standard_geopostal',   
                '[variable("STANDARD_GEOREGION")]':    'standard_georegion',   
                '[variable("STANDARD_IP")]':           'standard_ip',          
                '[variable("STANDARD_LAT")]':          'standard_lat',         
                '[variable("STANDARD_LONG")]':         'standard_long',        
                '[variable("STANDARD_REFERER")]':      'standard_referer',     
                '[variable("STANDARD_RESPONSETIME")]': 'standard_responsetime',
                '[variable("STANDARD_USERAGENT")]':    'standard_useragent',  
            }
        self.metadata = {}
        self.data = {}

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str([self.metadata, self.data])

    def _set_metadata(self, k, v):
        self.metadata[k] = to_sql(v)

    def set_metadata(self, k, v):
        if k in self.aliases.values():
            self._set_metadata(k, v)

    def set_metadata_from_json(self, new_metadata):
        for k,v in new_metadata.iteritems():
            if k in self.aliases:
                self._set_metadata(self.aliases[k], v)

    def set_id(self, value):
        self.data['id'] = value

    def set_data(self, field_name, value):
        self.data[field_name] = value

    def set_data_from_json(self, new_data):
        self.data = new_data

    def save(self, db, internal_name):
        response_metadata_table = \
                '%s_response_metadata' % internal_name
        response_data_table = \
                '%s_response_data' % internal_name

        db.insert_row(response_metadata_table, self.metadata, True)
        db.insert_row(response_data_table, self.data, True)

    



def main():
    # Command line args
    parser = argparse.ArgumentParser(
    description='Loads CSV data to MySQL based on user defined rules')
    parser.add_argument('--user', metavar='u', type=str, 
                        help='Survey Gizmo username')
    parser.add_argument('--password', metavar='p', type=str, 
                        help='Survey Gizmo password')
    parser.add_argument('--survey', metavar='s', type=int, 
                        help='Survey ID')

    args = vars(parser.parse_args())
    user = args['user']
    password = args['password']
    survey_id = args['survey']

    # Create DB
    db = SimpleDB('surveys')

    # JSON requests
    survey_metadata_json = survey_get_request(survey_id, '', 
                                              user, password)
    question_metadata_json = survey_get_request(survey_id, 'surveyquestion', 
                                                user, password)
    response_data_json = survey_get_request(survey_id, 'surveyresponse', 
                                            user, password)

    # Survey defining
    survey_definition = SurveyDefinition(survey_metadata_json, 
                                         question_metadata_json, 
                                         response_data_json)

    # Survey saving
    survey_definition.save(db)

    # Commit DB
    db.commit()

 
if __name__ == "__main__":
    main()


