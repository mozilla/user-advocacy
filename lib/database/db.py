#!/usr/local/bin/python

"""
This is a generic wrapper for sqlalchemy engines to add a database object that you can
specify. Database objects behave like engines but sets a default DB each time.
"""

import sqlalchemy
from sqlalchemy.sql import text, select

def init_engine (uri):
    return sqlalchemy.create_engine(uri, echo=False, encoding='utf-8')

class Database(object):
    """Database object. Represents an explicitly named DB accessed from a given engine."""
    def __init__(self, database_name, engine):
        meta = sqlalchemy.schema.MetaData(bind=engine, schema=database_name)
        meta.reflect()
        self.engine = engine
        self.Metadata = meta
        self.tables = meta.tables
        self.database_name = database_name
    

    def execute_sql(self, sql_string, **params):
        """Explicitly executes a SQL command."""
        sql = text(sql_string)
        conn = self.engine.connect()
        conn.execute('use '+ self.database_name)
        return conn.execute(sql, params)

    def connect(self):
        """Returns a DB connection with a new default DB"""
        conn = self.engine.connect()
        conn.execute('use '+ self.database_name)
        return conn

    def execute(self, object, *multiparams, **params):
        """Executes a sql object (can be made with sqlalchemy.sql)"""
        conn = self.engine.connect()
        conn.execute('use '+ self.database_name)
        return conn.execute(object, multiparams, params)
        


    
