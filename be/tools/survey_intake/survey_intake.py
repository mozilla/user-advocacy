#!/usr/local/bin/python

import csv
import re
import sys

# MySQLdb isn't in the default path
sys.path.append('/usr/lib/python2.7/dist-packages/')
import MySQLdb

 
# == DATA TYPE STUFF ===========================================================
# TODO(rrayborn): Make this more robust / class based 
_TYPES = ['TEXT', 'DATE', 'DATETIME', 'TIME', 'BOOL', 'INT',
          'FLOAT']

def _convert_to_type(val, data_type):
  if data_type == 'BOOL':
    return '1' if val not in ['false','no','n','0',''] else '0'
  elif data_type in ('TEXT', 'DATE', 'DATETIME', 'TIME', 'INT', 'FLOAT'):
    return val
  else:
    raise Exception('Data type %s is not handled.' % data_type)

# == DATABASE STUFF ============================================================
# TODO(rrayborn): Make this more robust / class based
_DB_NAME = 'surveys'

_DATABASE = MySQLdb.connect(host="localhost", db=_DB_NAME)
_CURSOR = _DATABASE.cursor()

def execute(sql):
  code = 0
  try:
    _CURSOR.execute(sql)
    _DATABASE.commit()
  except:
    _DATABASE.rollback()
  return _CURSOR.fetchall()



def main():

  # Get CSV name from terminal argument
  csv_name = sys.argv[1] # TODO(rrayborn): make this robust
  
  # Load data
  header = ''
  with open(csv_name, 'rb') as f:
    header = re.escape(f.readline())

  data = []
  with open(csv_name, 'rb') as f:
    data_reader = csv.reader(f)
    for row in data_reader:
      data.append(row)
  parsed_header = data.pop(0)

  # run
  setup()
  Table(header, parsed_header, data)


def setup():
  if not execute('SHOW TABLES WHERE tables_in_%s = "survey_table_metadata";' % (_DB_NAME)):
    execute(
        '''CREATE TABLE survey_table_metadata(
          id INT NOT NULL AUTO_INCREMENT,
          name VARCHAR(50) NOT NULL,
          header TEXT NOT NULL,
          PRIMARY KEY ( id )
        );'''
      )
  if not execute('SHOW TABLES WHERE tables_in_%s = "survey_column_metadata";' % (_DB_NAME)):
    execute(
        '''CREATE TABLE survey_column_metadata(
          id INT NOT NULL AUTO_INCREMENT,
          name TEXT NOT NULL,
          field VARCHAR(50) NOT NULL,
          type VARCHAR(50) NOT NULL,
          survey_table_metadata_id INT NOT NULL,
          PRIMARY KEY ( id ),
          FOREIGN KEY (survey_table_metadata_id) 
              REFERENCES survey_table_metadata(id)
              ON DELETE CASCADE
        );
        '''
      )


class Table(object):

  def __init__(self, header, parsed_header, data):
    # get list of existing table that match our data header
    sql = 'SELECT id, name FROM survey_table_metadata WHERE header = "%s";' \
        % (header)
    potential_tables = execute(sql)
    potential_table_names = map(lambda row: row[1], potential_tables)

    if potential_table_names:
      print "The following tables have identical headers to your input CSV:"
      print "\t%s" % (',\n\t'.join(potential_table_names))
    else:
      print("No existing tables match the headers of your input CSV.")
    # prompt the user for a new/existing table name
    table_name = raw_input("What table would you like to use? ") # TODO check that this is a valid table name

    # get a list of existing tables with our selected name
    actual_tables = execute('SHOW TABLES WHERE tables_in_%s = "%s";'
                      % (_DB_NAME, table_name))
    actual_table_names = map(lambda row: row[0], actual_tables)

    # Define table overwrite behaviour
    if table_name in actual_table_names:
      if table_name not in potential_table_names:
        raise Exception(
            'Table %s exists in the database %s ' % (table_name, _DB_NAME) +
                    'independently of this program. Please manage this ' +
                    'conflict in MySQL.'
          )
      else:
        delete_table_input = raw_input(
              "\nYou have selected an existing table name. " +
              "Would you like to DELETE the existing table and " +
              "overwrite it's information? (Y/n, default:n) "
            ).lower() or ['n']
        if 'y' == delete_table_input[0]:
          execute("TRUNCATE TABLE %s" % (table_name) )

    # Create table
    if table_name in potential_table_names:
      table_id = next(x[0] for x in potential_tables if x[1] == table_name)

      result = execute(
        'SELECT id FROM survey_table_metadata WHERE id = %s;' % (table_id))
      if len(result) == 0: #TODO validate this logic
        raise Exception(
            'Table ID %s can\'t be found in survey_table_metadata.' % (table_id))

      self.name = table_name
      self.header = header
      self.id = table_id
      self.columns = {}

      self._load_metadata()
      self._insert_data(parsed_header, data)
    else: # table_name not in potential_table_names
      result = execute(
          'SELECT id FROM survey_table_metadata WHERE name = "%s"' % (table_name))
      if len(result)>0:
        raise Exception("Table %s already exists." % table_name)

      execute('INSERT INTO survey_table_metadata (name, header) ' + 
              'VALUES ("%s","%s");' % (table_name, header))
      result = execute(
          'SELECT id FROM survey_table_metadata WHERE name = "%s";' % (table_name))
      table_id = result[0][0]

      self.name = table_name
      self.header = header
      self.id = table_id
      self.columns = {}

      self._create_metadata(parsed_header, data)
      self._insert_data(parsed_header, data)

  def _load_metadata(self):
    # load_metadata
    result = execute('SELECT name, field, type FROM survey_column_metadata ' +
                     'WHERE survey_table_metadata_id = %s;' % self.id)
    for row in result:
      self.columns[row[0]] = Column(row[0], row[1], row[2])

  def _create_metadata(self, parsed_header, data):
    if self.columns:
      raise Exception("Table %s already has populated metadata." % self.name)

    # generate new column info 
    num_rows = len(data)
    num_columns = len(parsed_header)

    for col_num in range(num_columns):
      column_name = parsed_header[col_num]

      num_examples = 0
      column_text = column_name + '\n'
      for row_num in range(num_rows):
        entry = data[row_num][col_num]
        if entry != '':
          column_text += '\t' + entry + '\n'
          num_examples += 1
          if num_examples == 10:
            break


      print '\n'+ 80 * '='
      print 'EXAMPLE COLUMN: \n\t%s' % (column_text)

      field = raw_input(
          'What field name do we want to use for the following column (blank to ignore column):\n\t' +
          '"%s" \n' % (column_name)
        ) # TODO check that this is a valid name
      if field == '':
        continue

      data_type = ''
      while data_type not in _TYPES:
        data_type = raw_input('What type is the field "%s"?  ' % (field) +
                              '(Valid input types: %s): ' % (', '.join(_TYPES))
                             ).upper()

      self.columns[column_name] = Column(column_name, field, data_type)
      sql = '''INSERT INTO survey_column_metadata (name, field, type, survey_table_metadata_id) 
               VALUES ("%s", "%s", "%s", "%s")''' % (column_name, field, data_type, self.id)
      execute(sql)

    # create new table
    fields = ',\n'.join(map(lambda col: col.field_def(), self.columns.values()))
    sql = 'CREATE TABLE %s (\n%s\n);' % (self.name,  fields)
    execute(sql)


  def _create_table(self):
    # create new table
    fields = ',\n'.join(map(lambda col: col.field_def(), self.columns.values()))
    sql = 'CREATE TABLE %s (\n%s\n);' % (self.name,  fields)
    execute(sql)

  def _insert_data(self, parsed_header, data):
    if not execute('SHOW TABLES WHERE tables_in_%s = "%s";' % (_DB_NAME, self.name)):
      self._create_table()

    for row in data:
      #row = data[row_num]
      fields = []
      values = []
      for col_num in range(len(parsed_header)):
        column_name = parsed_header[col_num]

        if column_name not in self.columns:
          continue
        else:
          column_metadata = self.columns[column_name]
          entry = _convert_to_type(row[col_num], column_metadata.data_type)
          fields.append(column_metadata.field)
          values.append(entry)

      sql ='INSERT INTO %s (%s) VALUES ("%s");' % (self.name,
                                                      ', '.join(fields),
                                                      '\", \"'.join(values)
                                                     )
      execute(sql)

  def  __str__(self):
    return str(self.id) + ', ' + self.name

class Column(object):
  def __init__(self, name, field, data_type):
    self.name = name
    self.field = field
    self.data_type = data_type

  def  __str__(self):
    return self.field + ', ' + self.data_type + ', ' + self.name

  def field_def(self):
    return self.field + ' ' + self.data_type



if __name__ == '__main__':
  main()