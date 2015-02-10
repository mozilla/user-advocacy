#!/usr/local/bin/python

"""
Wraps MySQLdb to make things simpler/class based.
"""

__author__ = "Rob Rayborn"
__copyright__ = "Copyright 2014, The Mozilla Foundation"
__license__ = "MPLv2"
__maintainer__ = "Rob Rayborn"
__email__ = "rrayborn@mozilla.com"
__status__ = "Development"

#TODOs
# TODO(rrayborn): Make this work with both auto-commit and manual commit DBs

import getpass
import MySQLdb
from os import environ
import re
import sys

class SimpleDB():

    def __init__(self, 
                 db,
                 host = None,
                 user = None,
                 password = None,
                 config_file = None,
                 encoding = None):

        if encoding:
            self.set_character_set(encoding)
        
        # TODO(rrayborn): make this less naive
        if config_file:
            with open(config_file, 'r') as config:
                if config:
                    for line in config:
                        if '=' in line:
                            command = (re.sub(r'= *','=\'',line[:-1]) + '\'')
                            exec(command)
        if not host:
            if environ.get('SQL_HOST'):
                host = environ['SQL_HOST']
            else:
                host = "localhost"
        if not user:
            if environ.get('UTILITES_USER'):
                user = environ['UTILITES_USER']
                if environ.get('UTILITES_PASSWORD'):
                    password = environ['UTILITES_PASSWORD']
            else:
                user = getpass.getuser()
                if environ.get('SQL_PASSWORD'):
                    password = environ['SQL_PASSWORD']

        if password:
            self.database = MySQLdb.connect(host=host, passwd=password, db=db, user=user, local_infile = 1)
        else:
            self.database = MySQLdb.connect(host=host, db=db, user=user, local_infile = 1)
        self.cursor = self.database.cursor()
        self.database.autocommit(False)
        self.is_committed = True    # TODO(rrayborn): is there a flag in the 
                                    # MySQLdb module to accomplish this?
        self.database_name = db     # TODO(rrayborn): this shoulbe be 
                                    # retrievable from self.database

        self.cursor.execute('select @@global.autocommit')
        self.autocommit = self.cursor.fetchall()[0][0] == '1'
  
    #def __del__(self):
        #if not self.is_committed:
            ##TODO(rrayborn): Figure out why this is having issues and re-enable
            ##self.database.rollback() 
            #raise Warning('Changes to database haven\'t been committed before '
            #              'destructor was initialized.')
        
    # ==== OTHER ===========================================================
    
    def set_character_set(self, encoding):
        self.database.set_character_set(encoding)
        self.cursor.execute('SET NAMES %s;' % encoding)
        self.cursor.execute('SET CHARACTER SET %s;' % encoding)
        self.cursor.execute('SET character_set_connection=%s;' % encoding)

    def set_utf8(self):
        self.set_character_set('utf8')

    # ==== EXECUTION ===========================================================
    def commit(self):
        self.is_committed = True
        self.database.commit()
  
    def execute(self, sql, include_header=False, verbose=False):
        try:
            #TODO: make this work for multiple commands in a non-hacky way
            for command in sql.split(';\n'):
                if verbose:
                    print command
                    print '='*80
                self.cursor.execute(command)
            #self.cursor.execute(sql)
        except MySQLdb.Error, e:
            self.database.rollback()
            raise Exception('Bad SQL command: %s\n SQL ERROR: %s' % (sql, e))
        
        desc = self.cursor.description
        
        result = [list(row) for row in self.cursor.fetchall()]
    
        self.is_committed = self.autocommit
    
        if not result:
            return None
        
        if include_header:
            fields = map(lambda d: d[0] ,desc)
            result.insert(0, fields)
    
        return result
  
    def execute_to_dict(self, sql):
        result = []
        result_list = self.execute(sql)
    
        fields = result_list.pop(0)
        for row in result_list:
            new_row = {}
            for i in range(len(fields)):
                new_row[fields[i]] = row[i]
            result.append(new_row)
        return result

    # ==== OUTPUT ==============================================================
  
    def is_valid_table_name(self, table_name):
        return re.match(r'[A-Za-z0-9_\$]{%i}' % (len(table_name)), table_name)
  
    def is_existing_table(self, table_name):
        return bool(self.execute(
                '''SHOW TABLES 
                WHERE Tables_in_%s = "%s";''' % (self.database_name, table_name)
            ))
  
    def desc_table(self, table_name):
        if not self.is_valid_table_name(table_name):
            raise Exception('Table name "%s" is not valid.' % table_name)
        if not self.is_existing_table(table_name):
            raise Exception('Table name "%s" does not exist.' % table_name)

        return self.execute('DESC %s;' % table_name)
  
    def drop_table(self, table_name):
        if not self.is_valid_table_name(table_name):
            raise Exception('Table name "%s" is not valid.' % table_name)
        return self.execute('DROP TABLE IF EXISTS %s;' % table_name)
  
    def show_tables(self):
        return self.execute('SHOW TABLES;')

    # ==== INPUT ===============================================================

    def save_table(self, table_name, data, is_overwrite = False):
        if type(data[0]) is list:
            header = data.pop(0)
        else:
            header = None

        for row in data:
            self.insert_row(table_name, row, is_overwrite, header)

    def insert_row(self, table_name, data, is_overwrite = False, header = None):

        command = 'REPLACE' if is_overwrite else 'INSERT'
        if type(data) is list and header:
            new_data = {}
            for row in zip(header, data):
                new_data[row[0]] = row[1]
            data = new_data
        
        cols = ', '.join(['%s = %s' % (k,v) for k, v in data.iteritems()])
        sql = '%s INTO %s SET %s;' % (command, table_name, cols)
        self.execute(sql)


def janky_test():
    db = SimpleDB('test')
    print db.execute('CREATE TABLE test AS SELECT 3;')
    print db.show_tables()
    print db.desc_table('test')
    print db.execute('select * from test;')
    print db.execute_to_dict('select * from test;')
    print db.drop_table('test')
    #db.save_table('t1', [{'a':1,'b':2,'c':3}, {'a':4,'b':5,'c':6}])
    print db.commit()

