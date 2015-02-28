
import csv
import json
import re
import sys

from collections import defaultdict
from math        import log,pow,floor
#from pprint      import pprint
from os          import path

from lib.database.backend_db  import Db

_PIPELINE_PATH = path.dirname(path.realpath(__file__))+'/'
_DATA_PATH  = _PIPELINE_PATH + '/data/'
_UPDATE_SQL_FILE = _PIPELINE_PATH + 'update.sql'
_INTERMEDIATE_CSV = _DATA_PATH + '.tmp.csv'
_CHANNELS = ['release', 'beta', 'aurora', 'nightly']

#This should be handled better...
_SENTIMENT_DB = Db('sentiment', is_persistent = True)

def bootstrap():
    #TODO(rrayborn)
    raise Exception("Not implemented:Must run create.sql then populate the " \
            + "telemetry_measures and telemetry_screens tables.")

def run(date_str, channel, file_in):
    """
    Pulls in CSV for a given date/channel and generates a measure list for it.
    
    date_str = 'YYYY-MM-DD'
    file_in = '<PATH>/<FILE>'
    """
    channel = channel.lower()
    if channel not in _CHANNELS:
        raise Exception('Channel %s not in channels: %s.' % \
                (channel, ','.join(_CHANNELS)))

    # Transform
    measures = MeasureList()
    measures.load_csv(file_in)
    #measures.save_csv() #TODO(rrayborn): refactor this to avoid saving an intermediate CSV

    # Load to MySQL
    _telem_parsed_to_sql(date_str, channel, measures.get_iter())


# ===== SQLING =================================================================

def _telem_parsed_to_sql(date_str,
                         channel,
                         measure_iter,
                         version    = None, 
                         query_file = _UPDATE_SQL_FILE):
    """ Loads _INTERMEDIATE_CSV into the sentiment database """

    db = Db('telemetry', is_persistent = True)

    #version query
    if not version:
        query = """
                SELECT
                    version
                FROM 
                    sentiment.release_info ri
                WHERE
                    '{date}' >= ri.{channel}_start_date
                    AND '{date}' <= ri.{channel}_end_date
            ;""".format(date=date_str, channel=channel)
        version = str(db.execute_sql(query).first()[0])

    
    query ='''CREATE TEMPORARY TABLE tmp_weekly_stats (
            os                       ENUM('Windows','Mac','Linux'),
            measure                  VARCHAR(200),
            measure_value            VARCHAR(200),
            users                    INT,
            measure_average          FLOAT,
            measure_nonzero_average  FLOAT,
            active_users             FLOAT,
            potential_users          INT         
        );'''
    db.execute_sql(query)
    mappings = {
                0:'measure',
                1:'os',
                2:'measure_average',
                3:'measure_nonzero_average',
                4:'active_users',
                5:'potential_users',
                6:'measure_value'
            }
    db.insert_data_into_table(measure_iter, 'tmp_weekly_stats', mappings)


    with open(query_file, 'r') as query_sql:
        if query_sql:
            query = query_sql.read()
    
    db.execute_sql(query, {'week':date_str, 'channel':channel, 'version':version})

# ===== MUNGING ================================================================


class MeasureList:
    """
    Contains a dict of Measures with values and a dict that stores how many sessions have 
    been seen for each OS. Use the load_csv method to parse a CSV (talk to Ilana about
    formatting of said CSV.) 
    """
    
    _typo_dict = {'bookmark3Bar': 'bookmarksBar'} #TODO(rrayborn): Make this non-static??
    _os_map = {'winnt': 'windows', 'darwin': 'mac', 'linux': 'linux'}

    def __init__(self):
        self.measure_lists = {}
        self.os_totals = {}


    def _append_row(self, row):
        # Set search Regex
        reFeatures       = re.compile('^(extra_)?features_')
        reToolbars       = re.compile('barEnabled-(True|False)', flags=re.I)
        reSearch         = re.compile('^search-', flags=re.I)
        reScreen         = re.compile('^sizemode-.+') #TODO(rrayborn): the ".+" is for the "sizemode-"
        reLeftClick      = re.compile('^click-.*left$')
        reClicks         = re.compile('^click-')
        reCustomize      = re.compile('^customization_time')
        reAddons         = re.compile('^addonToolbars')
        reCustomAction   = re.compile('^customize-')
        reTour           = re.compile('^seenPage-')
        
        # Set defaults
        os = row[0]
        if os.lower() in self._os_map:
            os = self._os_map[os.lower()]
        else:
            raise Warning('OS "%s" not recognized.' % os)

        raw_value      = row[1]
        values         = json.loads(row[2])
        os_total       = int(row[3])
        #measure_name   = None
        #value         = None

        if len(values)==1:
            total = values.values()[0]
        else:
            total = None

        # Giant parsetree of doom
        if reFeatures.search(raw_value):
            # raw_value     = 'features_kept-new-window-button'
            # featurelist  = ['features_kept','new','window','button']
            # value        = 'kept'
            # measure_name = 'window-button'
#            print "features"
            featurelist  = raw_value.partition('-')
            value        = featurelist[0].rpartition('_')[2]
            measure_name = featurelist[2]

            self.insert(measure_name, 'string', 
                        os, os_total,  
                        value = value, total = total)
        elif reToolbars.search(raw_value):
            # raw_value    = titleBarEnabled-True
            # featurelist  = ['title','True']
            # value        = 'Enabled'
            # measure_name = 'titleBar'
            featurelist = raw_value.partition('Enabled-')
            if featurelist[2].lower()   == 'true':
                value = 'enabled'
            elif featurelist[2].lower() == 'false':
                value = 'disabled'
            else:
                raise Warning('Toolbar value %s unknown' % featurelist[2])
                value = None
#            print "toolbar"
            measure_name = featurelist[0]
            
            self.insert(measure_name, 'string', 
                        os, os_total,  
                        value = value, total = total)
        elif reScreen.search(raw_value):
            measure_name = 'sizemode'
            value        = raw_value.rpartition('-')[-1]
#            print "screen"
            
            self.insert(measure_name, 'string', 
                        os, os_total,  
                        value = value, total = total)
        elif reLeftClick.search(raw_value) \
                or reCustomize.search(raw_value) \
                or reAddons.search(raw_value) \
                or reSearch.search(raw_value):
            # featurelist  = ['click','menu','button','button','left']
            # value        = 'count'
            # measure_name = <yield>
#            print "buckets"
            measure_name = raw_value
            self.insert(measure_name, 'bucket', 
                        os, os_total,  
                        values = values)
        elif reClicks.search(raw_value) \
                or reCustomAction.search(raw_value) \
                or reAddons.search(raw_value) \
                or reTour.search(raw_value):
            return
        else:
            print 'Item "%s" not parsed' % raw_value

    def insert(
                self, measure_name, measure_type,
                os, os_total, 
                values = None,
                value = None, total = None
            ):
        if measure_name =='windows':
            raise Exception('Nooooo')

        if measure_name in self._typo_dict:
            measure_name = self._typo_dict[measure_name]
    
        if value and total:
            values = {value:total}

        if os not in self.os_totals:
            self.os_totals[os] = os_total
        elif os_total != self.os_totals[os]:
            raise Exception('OS totals inconsistent for %s. (%d != %d)' % \
                    (measure_name, os_total, self.os_totals[os]))

        if measure_name not in self.measure_lists:
            self.measure_lists[measure_name] = Measure(measure_name, measure_type)

        measure = self.measure_lists[measure_name]
        measure.insert(os, os_total, values = values)

    def get_iter(self):
        return iter(self.get_table())

    def get_table(self):
        ret = [Measure.get_header()]
        for measure_name, measure_list in self.measure_lists.iteritems():
            ret += measure_list.get_list(measure_name, self.os_totals)
        return ret

    def load_csv(self, file_in):
        with open(file_in, 'rb') as csvfile:
            csvreader = csv.reader(csvfile, delimiter=',', quotechar='"')
            #skip header
            next(csvreader, None)

            for row in csvreader:
#                print row
                self._append_row(row)


    def save_csv(self, file_out = _INTERMEDIATE_CSV):
        if file_out:
            with open(file_out, 'wb') as csvfile:
                my_writer = csv.writer(csvfile, delimiter=',',
                                        quotechar='"', quoting=csv.QUOTE_MINIMAL)
                for row in self.get_table():
                    my_writer.writerow(row)
        else:
            raise Warning('File out not provided')



class Measure:
    """ 
    Contains different kinds of measures, the type of measure and values therefor.
    Each measure consists of a dict of OSMeasure objects which contain values for a single
    OS.
    """
    
    _other_dict = {
            'bucket':  '0-0',
            'string': 'other',
            'int':     '0'
        }
    _numeric_types = ['int','bucket']

    def __init__(self, measure_name, measure_type):
        if measure_type not in self._other_dict:
            raise Exception('Type %s unknown.' % measure_type)
        self.measure_name = measure_name
        self.measure_type = measure_type
        self.other_value  = self._other_dict[measure_type]
        self.is_numeric   = measure_type in self._numeric_types
        self.os_measures  = {} # os -> measure
        self.total        = 0


    def insert(self, os, os_total, 
                values = None,
                value = None, total = None):
        if value and total:
            values = {value:total}
        elif not values:
            raise Exception('values or value & total must be populated.')

        for value,total in values.iteritems():
            if self.measure_type in self._numeric_types:
                numeric_value = int(value)
                if self.measure_type == 'bucket':
                    value = self._bucketize(value)
            else:
                numeric_value = None

            if os not in self.os_measures:
                self.os_measures[os] = OSMeasure(
                        self.measure_name, os, self.other_value, self.is_numeric
                    )
            
            self.os_measures[os].insert(
                    value, total, numeric_value = numeric_value
                )


    def _bucketize(self, input):
        if int(input)==0:
            return '0-0'
        lower_bound = int(pow(2,floor(log(int(input), 2))))
        return '-'.join([str(lower_bound), str(lower_bound*2-1)])
     
    @staticmethod
    def get_header():
        return [
                'name',
                'os',
                'average',
                'nonzero_average',
                'active_users',
                'os_users',
                'measure_value',
                'users'
            ]

    def get_list(self, name, os_totals):
        ret = []
        for os, os_total in os_totals.iteritems():
            if os not in self.os_measures:
                self.os_measures[os] = OSMeasure(
                        self.measure_name, os, self.other_value, self.is_numeric
                    )
            ret += self.os_measures[os].get_list(name, os_total)
        return ret

    def __str__(self):
        return 'Measure <%s, %s>' % (self.measure_name)


class OSMeasure:
    """ Measure <-> value pairing."""
    _inactive_types = ['removed']

    def __init__(self, measure_name, os, other_value, is_numeric):
        self.measure_name    = measure_name
        self.os              = os
        self.other_value     = other_value
        self.is_numeric      = is_numeric

        self.active_total    = 0
        self.running_total   = 0

        #numeric data
        if is_numeric:
            self.weighted_total  = 0
            self.nonzero_average = 0
            self.average         = 0
        else:
            self.weighted_total  = None
            self.nonzero_average = None
            self.average         = None

        self.values          = {}

    def insert(self, value, total, numeric_value = None):
        
        self.running_total += total

        if value not in self._inactive_types: 
            self.active_total += total
            # increment weighted total
            if numeric_value:
                self.weighted_total += total*numeric_value

        # store value
        if value in self.values:
            self.values[value] += total
        else:
            self.values[value]  = total

    def _finalize(self, os_total):

        # Set averages
        if self.is_numeric:
            if self.active_total:
                self.nonzero_average = float(self.weighted_total)/float(self.active_total)
            if os_total:
                self.average         = float(self.weighted_total)/float(os_total)

        # Check sums
        if self.running_total > os_total:
            warning_str = 'Running total %s is greater than the total passed in %s for: %s' \
                                % (self.running_total, os_total, self)
            if self.running_total/os_total > 1.01: # 1% off
                raise Exception(warning_str)
            if self.running_total/os_total > 1.001: # .1% off
                raise Warning(warning_str)
            else: # >0% off
                print warning_str
        # Populate 'Other'
        elif self.running_total < os_total:
            self.values[self.other_value] = os_total - self.running_total


    def get_list(self, name, os_total):
        self._finalize(os_total)

        ret = []
        for value, total in self.values.iteritems():
            ret.append([
                    name,
                    self.os,
                    self.average,
                    self.nonzero_average,
                    self.active_total,
                    os_total,
                    value,
                    total
                ])
        return ret

    def __str__(self):
        return 'OS Measure <%s, %s>' % (self.measure_name, self.os)


if __name__ == "__main__":
    queue = [
        ["2015-01-27", "nightly",  _DATA_PATH + "week_of_20150127_nightly.csv"]#,
        #["2014-07-01", "aurora",  _DATA_PATH + "week_of_20140701_aurora.csv"],
        #["2014-07-08", "aurora",  _DATA_PATH + "week_of_20140708_aurora.csv"],
        #["2014-07-15", "aurora",  _DATA_PATH + "week_of_20140715_aurora.csv"],
        #["2014-07-22", "aurora",  _DATA_PATH + "week_of_20140722_aurora.csv"],
        #["2014-07-22", "release", _DATA_PATH + "week_of_20140722_release.csv"],
        #["2014-07-29", "aurora",  _DATA_PATH + "week_of_20140729_aurora.csv"],
        #["2014-07-29", "release", _DATA_PATH + "week_of_20140729_release.csv"],
        #["2014-08-05", "aurora",  _DATA_PATH + "week_of_20140805_aurora.csv"],
        #["2014-08-12", "aurora",  _DATA_PATH + "week_of_20140812_aurora.csv"],
        #["2014-08-26", "aurora",  _DATA_PATH + "week_of_20140826_aurora.csv"],
        #["2014-09-02", "aurora",  _DATA_PATH + "week_of_20140902_aurora.csv"],
        #["2014-09-09", "aurora",  _DATA_PATH + "week_of_20140909_aurora.csv"],
        #["2014-09-16", "aurora",  _DATA_PATH + "week_of_20140916_aurora.csv"],
        #["2014-09-23", "aurora",  _DATA_PATH + "week_of_20140923_aurora.csv"],
        #["2014-09-30", "aurora",  _DATA_PATH + "week_of_20140930_aurora.csv"],
        #["2014-10-07", "aurora",  _DATA_PATH + "week_of_20141007_aurora.csv"],
        #["2014-10-14", "aurora",  _DATA_PATH + "week_of_20141014_aurora.csv"],
        #["2014-10-14", "release", _DATA_PATH + "week_of_20141014_release.csv"],
        #["2014-10-21", "aurora",  _DATA_PATH + "week_of_20141021_aurora.csv"],
        #["2014-10-21", "release", _DATA_PATH + "week_of_20141021_release.csv"],
        #["2014-10-28", "aurora",  _DATA_PATH + "week_of_20141028_aurora.csv"],
        #["2014-10-28", "release", _DATA_PATH + "week_of_20141028_release.csv"],
        #["2014-11-04", "aurora",  _DATA_PATH + "week_of_20141104_aurora.csv"],
        #["2014-11-04", "release", _DATA_PATH + "week_of_20141104_release.csv"],
        #["2014-11-11", "aurora",  _DATA_PATH + "week_of_20141111_aurora.csv"],
        #["2014-11-11", "release", _DATA_PATH + "week_of_20141111_release.csv"],
        #["2014-11-18", "aurora",  _DATA_PATH + "week_of_20141118_aurora.csv"],
        #["2014-11-18", "release", _DATA_PATH + "week_of_20141118_release.csv"],
        #["2014-11-25", "release", _DATA_PATH + "week_of_20141125_release.csv"],
        #["2014-12-02", "release", _DATA_PATH + "week_of_20141202_release.csv"],
        #["2014-12-09", "release", _DATA_PATH + "week_of_20141209_release.csv"],
        #["2014-12-16", "release", _DATA_PATH + "week_of_20141216_release.csv"],
        #["2014-12-23", "release", _DATA_PATH + "week_of_20141223_release.csv"],
        #["2014-12-30", "release", _DATA_PATH + "week_of_20141230_release.csv"]
    ]

    for entry in queue:
        print '='*10  + entry[0] + '=' + entry[1] + '='*10
        run(entry[0],entry[1],entry[2])
