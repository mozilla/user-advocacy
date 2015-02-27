#!/usr/local/bin/python

"""
This is a generic wrapper for sqlalchemy engines to add a database object that you can
specify. Database objects behave like engines but sets a default DB each time.
"""

import logging
import sqlalchemy
from sqlalchemy.sql import text, select

#logging.basicConfig()
#logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)


def init_engine (uri):
    return sqlalchemy.create_engine(uri + "?charset=utf8&use_unicode=0", 
        echo=False, encoding='utf-8')

class Database(object):
    """Database object. Represents an explicitly named DB accessed from a given engine."""
    def __init__(self, database_name, engine, is_persistent = False):
        meta = sqlalchemy.schema.MetaData(bind=engine, schema=database_name)
        meta.reflect()
        self.engine = engine
        if is_persistent:
            self.conn = self.engine.connect()
        self.Metadata = meta
        self.tables = meta.tables
        self.database_name = database_name

    def _get_connection(self):
        return self.conn if hasattr(self,'conn') else self.engine.connect()

    def execute_sql(self, sql_string, *multiparams, **params):
        """Explicitly executes a SQL command."""
        sql = text(sql_string)
        conn = self._get_connection()
        conn.execute('use '+ self.database_name)
        return conn.execute(sql, *multiparams, **params)

    def connect(self):
        """Returns a DB connection with a new default DB"""
        conn = self._get_connection()
        conn.execute('use '+ self.database_name)
        return conn

    def execute(self, object, *multiparams, **params):
        """Executes a sql object (can be made with sqlalchemy.sql)"""
        conn = self._get_connection()
        conn.execute('use '+ self.database_name)
        return conn.execute(object, *multiparams, **params)
    
    def get_table (self, table_name):
        """ Returns a sqlalchemy table (needed for building queries)"""
        if not '.' in table_name:
            return self.Metadata.tables[self.database_name + '.' + table_name]
        return sqlalchemy.schema.MetaData(bind=engine).tables[table_name]


    
