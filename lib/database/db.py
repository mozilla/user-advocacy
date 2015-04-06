#!/usr/local/bin/python

"""
This is a generic wrapper for sqlalchemy engines to add a database object that you can
specify. Database objects behave like engines but sets a default DB each time.
"""
import csv
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

    #======== More Specific Helper Functions ===================================

    def janky_execute_sql_wrapper(self, sql, query_vars = None):
        '''
        SQL statements with more than one query were erroring out,
        This is a hacky fix.
        '''
        queries = sql.split(';')
        for query in queries:
            if query != '':
                if query_vars:
                    self.execute_sql(query, query_vars)
                else:
                    self.execute_sql(query)
    
    def insert_csv_into_table(self,
                              filename,
                              tablename,
                              col_fields,
                              has_header = True,
                              delimiter = ','):
        '''
        Loads a CSV into a Table

        Args:
            filename    (str): The path/filename of the CSV
            tablename   (str): The name of the table to update
            col_fields (dict): A dict that maps <column name|column index> -> field
                       (list): A list of the fields that correlate to the CSV columns
                               ex. {1:'week', 3:'total'} 
                               ex. {'date':'week', 'total':'total'}
            has_header (bool): Whether the FILE contains a header (default: True)
            delimiter   (str): The delimeter used in the CSV (default: ',')
        '''
        with open(filename, 'rb') as f:
            csv_iter = csv.reader(f, delimiter = delimiter)
            self.insert_data_into_table(csv_iter, tablename, col_fields, has_header)


    def insert_data_into_table(self,
                               data_iterator,
                               tablename,
                               col_fields,
                               has_header = True):
        '''
        Loads a CSV into a Table

        Args:
            data_iterator (iter): A data iterator
            tablename      (str): The name of the table to update
            col_fields    (dict): A dict that maps <column name|column index> -> field
                          (list): A list of the fields that correlate to the CSV columns
                                  ex. {1:'week', 3:'total'} 
                                  ex. {'date':'week', 'total':'total'}
            has_header    (bool): Whether the FILE contains a header (default: True)
        '''
        #TODO: It would be nice to be able to pass in functions to alter specific columns

        # Convert list to dict if list
        new_cf = {}
        if isinstance(col_fields, list):
            i = 0
            for v in col_fields:
                new_cf[i] = v
                i += 1
            col_fields = new_cf

        first_key = col_fields.keys()[0]
        col_type = type(first_key)
        if isinstance(first_key, (int, long)):
            needs_mapped = False
            new_mapping = col_fields
        else:
            needs_mapped = True
            new_mapping = {} # index -> field
            if not has_header:
                raise Exception('If you provide string keys for col_fields \
                                your file must have a header to map against.')
        # Sanity Check the keys of col_values for consistent types
        for k in col_fields.keys():
            if not isinstance(k,col_type):
                raise Exception('type(key) in col_fields must be consistent.')

        # remove header
        if has_header:
            first_line = data_iterator.next()
            if needs_mapped:
                header = {}
                i = 0
                for v in first_line:
                    header[v] = i
                    i += 1
                for k,v in col_fields.iteritems():
                    new_mapping[header[v]] = v

        insert_pattern = 'INSERT INTO %s (%s) VALUES (%s);'
        for row in data_iterator:
            fields = []
            values = []
            for index, field in new_mapping.iteritems():
                if row[index] is None or row[index] =='Null':
                    value = 'Null'
                elif isinstance(row[index],str):
                    value = '"' + row[index].decode('utf-8') + '"'
                else:
                    value = str(row[index])

                if value.lower() == '"true"' or value.lower() == '"false"':
                    value = '"1"' if value.lower() == '"true"' else '"0"'

                fields.append('`' + field + '`')
                values.append(value)
            query = insert_pattern % (
                    tablename,
                    ','.join(fields),
                    ','.join(values)
                )
            self.execute_sql(query)
    
