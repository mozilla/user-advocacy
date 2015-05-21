#!/usr/local/bin/python

"""
TODO
"""

__author__ = "Rob Rayborn"
__copyright__ = "Copyright 2014, The Mozilla Foundation"
__license__ = "MPLv2"
__maintainer__ = "Rob Rayborn"
__email__ = "rrayborn@mozilla.com"
__status__ = "Development"

# import external language library

import re
import csv
from lib.database.backend_db  import Db as UA_DB

_GAP_PENALTY = 1
_SWITCH_PENALTY = 1

class LevenNode(object):
    def __init__(self, entry, metadata = None):
        '''
        An object to store information relevant to a single Node on our 
        LevenTrie.

        Args:
            entry    (string):     The entry's value.
            metadata (<anything>): The entry's metadata info. [Default: None]

        '''
        self.entry              = entry
        self.metadata           = []
        self.collisions         = 0
        self.duplicates         = 0
        if metadata:
            self.metadata.append(metadata)

    def add_metadata(self, metadata):
        '''
        Adds to our metadata list. Increments the number of duplicates.

        Args:
            metadata (<anything>): The entry's metadata info.

        '''
        self.metadata.append(metadata)
        self.duplicates += 1


class LevenTrie(object):
    def __init__(self, 
                 entries        = None, 
                 gap_penalty    = _GAP_PENALTY, 
                 switch_penalty = _SWITCH_PENALTY):
        '''
        An object that builds/represents a Levenstein Trie.

        Args:
            entries        (list):  A list of entries to insert in our trie.
                           (dict):  A list of entries to insert in our trie. metadata -> entry
            gap_penalty    (float): The penalty for a missing entry.
            switch_penalty (float): The penalty for an incorrect entry.

        '''
        self._node               = None

        self._sub_trie           = {}
        self._num_sub_entries    = 0
        self._sub_trie_min_depth = 0

        self._searches           = {}

        #TODO setters
        self.gap_penalty    = gap_penalty
        self.switch_penalty = switch_penalty

        if entries:
            if isinstance(entries,list):
                self.insert_list(entries)
            elif isinstance(entries,dict):
                self.insert_dict(entries)
            else:
                Warning('entries type not recognized.')

    # INSERT
    def insert_list(self, entries):
        '''
        Inserts a list of entries into our a Levenstein Trie.

        Args:
            entries (list):  A list of entries to insert in our trie.

        '''
        for entry in entries:
            self.insert(entry)

    def insert_dict(self, entries):
        '''
        Inserts a dict of entries into our a Levenstein Trie.

        Args:
            entries (dict):  A list of entries to insert in our trie. metadata -> entry

        '''
        for metadata, entry in entries.iteritems():
            self.insert(entry, metadata = metadata)

    def insert(self, entry, metadata = None):
        '''
        Inserts an entry into our a Levenstein Trie.

        Args:
            entry    (iterable): An iterable entry.
            metadata (anything): The entry's metadata. [Default: None]

        Returns:
            success (bool): Whether the insert was unique
            node    (Node): The Node that was inserted
        '''
        # returns success, Node
        return self._insert(entry, entry, metadata = metadata)

    def _insert(self, entry, entry_name, metadata):
        self._num_sub_entries += 1
        if not entry_name:
            entry_name = str(entry)

        if len(entry) < self._sub_trie_min_depth:
            self._sub_trie_min_depth = len(entry) 

        if len(entry) == 0:
            if self._node:
                self._node.add_metadata(metadata)
                duplicate = False
            else:
                self._node = LevenNode(entry_name, metadata = metadata)
                duplicate = True
            return duplicate, self._node
        
        next_item = entry[0]
        if not next_item in self._sub_trie:
            self._sub_trie[next_item] = LevenTrie(
                    gap_penalty = self.gap_penalty,
                    switch_penalty = self.switch_penalty
                )    
        return self._sub_trie[next_item]._insert(entry[1:], entry_name = entry_name, metadata = metadata)
   
    # SEARCH 
    def search(self, entry, threshold = 1.5):
        '''
        Searches for an entry into our a Levenstein Trie.

        Args:
            entry     (iterable): An iterable entry.
            threshold (float):    The similarity threshold. [Default: 1.5]

        Returns:
            score   (bool): The similarity score (1 is completely different,0 is the same) TODO(rrayborn): should we invert this?
            node    (Node): The Node that was found
        '''
        # Returns threshold, Node
        score, match = self._search(entry, threshold)
        self._clear_searches()
        return ((threshold - score) if score else threshold)/threshold, match

    def _clear_searches(self):
        self._searches = {}
        for v in self._sub_trie.values():
            v._clear_searches()


    def _search(self, entry, threshold):
        record = [None, None]

        if threshold < 0:
            return record

        key = str(entry)
        if key in self._searches.keys():
            if threshold <= self._searches[key]:
                return record
        self._searches[key] = threshold

        min_diff = abs(len(entry) - self._sub_trie_min_depth)

        if len(entry) > 0:
            shorten_entry = True
        else:
            shorten_entry = False

        if self._num_sub_entries > 0:
            search_trie = True
        else:
            search_trie = False

        if not shorten_entry:
            # shorten neither
            if self._node:
                self._node.collisions += 1
                record = [threshold, self._node] 
                return record
            elif threshold < self.gap_penalty*min_diff:
                return record
        else:
            # shorten entry
            record = self._list_max(record, 
                    self._search(entry[1:], threshold - self.gap_penalty))

        if search_trie:
            for k,v in self._sub_trie.iteritems():
                # shorten words
                record = self._list_max(record, 
                        v._search(entry, threshold - self.gap_penalty))
                # shorten entry and words
                if shorten_entry:
                    record = self._list_max(record, 
                            v._search(entry[1:], threshold - self._diff(entry[0], k)))
        
        return record

    def _clear_collisions(self):
        if self._node:
            self._node.collisions = 0
        for v in self._sub_trie.values():
            v._clear_collisions()

# THIS IS NOW OUT OF DATE AND UNUSED
#    # CSV loader/saver
#    def load_csv(self, filename):
#        with open(filename, 'rb') as csv_file:
#            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='\"')
#            for row in csv_reader:
#                self.abusive_words_trie.insert_list(row)
#    
#    def save_csv(self, filename):
#        with open(filename, 'wb') as csv_file:
#            csv_writer = csv.writer(csv_file, delimiter=',',
#                            quotechar='\"', quoting=csv.QUOTE_MINIMAL)
#            csv_writer.writerow(self.get_list())
#
#    def get_list(self, ):
#        l = []
#        if self.node:
#            for i in range(0, self._node_count):
#                l.append(self._node)
#        for ld in self._sub_trie.values():
#            l.extend(ld.get_list())
#        return l

    # HELPER FUNCTIONS
    def _diff(self, v1, v2):
        return 0 if v1 == v2 else self.switch_penalty

    def _list_max(self, l1, l2):
        return l2 if l2[0] >= l1[0] else l1
    


class LevenClassifier(LevenTrie):
                 #entries         = None,
            #entries          (list):  A list of entries to insert in our trie.
            #                 (dict):  A list of entries to insert in our trie. metadata -> entry
                           #entries        = entries, 
    def __init__(self,  
                 gap_penalty     = _GAP_PENALTY, 
                 switch_penalty  = _SWITCH_PENALTY, 
                 min_len         = 3,
                 max_len         = 10000, 
                 threshold_ratio = .75):
        '''
        A Levenstein Trie based classifier.

        Args:
            gap_penalty     (float): The penalty for a missing entry.
            switch_penalty  (float): The penalty for an incorrect entry.
            min_len           (int): The minimum length of an entry.
            max_len           (int): The maximum length of an entry.
            threshold_ratio (float): A ratio used in our threshold heuristic. eg
                                     1 + (1 - self.threshold_ratio) * len(entry)

        '''
        LevenTrie.__init__(self,
                           gap_penalty    = gap_penalty,
                           switch_penalty = switch_penalty)
        self.min_len          = min_len
        self.max_len          = max_len
        self.threshold_ratio  = threshold_ratio

#    def unique_list(self, entries):
#        # returns, unique_entries, non_unique_entries
#        unique     = []
#        non_unique = []
#        for entry in entries:
#            is_unique, _ignore = self.insert_unique(entry)
#            if is_unique:
#                ret.append((entry,metadata))
#        return ret

    def unique_dict_keys(self, entries):
        '''
        Returns a dict of unique and non-unique entries.

        Args:
            entries (dict): {metadata_key -> entry}

        Returns:
            unique_dict     (dict): {unique_key     -> unique_key}
            non_unique_dict (dict): {non_unique_key -> unique_key}
        '''
        # takes {entry_key -> [entry_data]}
        # returns:
        #   {unique_key     -> unique_key}
        #   {non_unique_key -> unique_key}
        unique     = {} # unique_key     -> unique_key
        non_unique = {} # non_unique_key -> unique_key
        for entry_key, entry in entries.iteritems():
            is_unique, metadata = self.insert_unique(entry, metadata = entry_key)
            if is_unique:
                unique[metadata] = metadata
            else:
                non_unique[entry_key] = metadata
        return unique, non_unique

    # TODO(rrayborn): should below this be its own class? ======================
    def insert_unique(self, entry, metadata = None):
        '''
        Inserts the entry if it's unique.  Returns the closest entry's metadata

        Args:
            entry    (iterable): An iterable entry.
            metadata (anything): The entry's metadata. [Default: None]

        Returns:
            is_unique      (bool): Whether the entry is unique
            metadata   (anything): The metadata of the closet entry (including the current entry)
        '''

        # Returns result, metadata
        if len(entry) <= self.min_len:
            return True, metadata
        entry = entry[:self.max_len]
        threshold = self._get_threshold(entry)

        _ignore, node = self.search(entry, threshold)

        if node:
            return False, node.metadata[0]
        else:
            success, node = self.insert(entry, metadata = metadata)
            if not success:
                raise Exception('This should never execute.')
            return True, node.metadata[0]

    def _get_threshold(self, entry):
        return 1 + (1 - self.threshold_ratio) * len(entry) # just a heuristic


class SpamDetector(LevenClassifier):
                 #entries         = None, 
                #entries         = None, 
    def __init__(self,
                 gap_penalty     = _GAP_PENALTY, 
                 switch_penalty  = _SWITCH_PENALTY,
                 min_len         = 3, 
                 max_len         = 50, 
                 threshold_ratio = .75,
                 db              = None):
        '''
        An object that uses a Levenstein based heuristic of spam/similarity
        detection.

        Args:
            gap_penalty     (float): The penalty for a missing entry.
            switch_penalty  (float): The penalty for an incorrect entry.
            min_len           (int): The minimum length of an entry.
            max_len           (int): The maximum length of an entry.
            threshold_ratio (float): A ratio used in our threshold heuristic. eg
                                     1 + (1 - self.threshold_ratio) * len(entry)
            db                 (DB): Our local input database

        '''
        LevenClassifier.__init__(
                self, 
                gap_penalty     = gap_penalty,
                switch_penalty  = switch_penalty,
                min_len         = min_len,
                max_len         = max_len, 
                threshold_ratio = threshold_ratio
            )
        self.db = db if db else UA_DB('input', is_persistent = True)

    def check_entries_for_spam(self, entries):
        '''
        Checks a dict of entries for Spam.  Inserts matches in our DB.  Returns non-unique entries.

        Args:
            entries (dict): {metadata_key -> entry}

        Returns:
            non_unique (dict): {metadata_key -> entry}

        Side-Effect:
            Updates our input.input_metadata table.

        '''
        unique, non_unique = self.unique_dict_keys(entries)
        for non_unique_id, unique_id in non_unique.iteritems():
            self.insert_spam(non_unique_id, unique_id)
        return non_unique

    def insert_spam(self, input_id, spam_id):
        '''
        Inserts spam entries into input.input_metadata.

        Args:
            input_id (int): The input id of the root comment
            input_id (int): The input id of the spam comment

        Side-Effect:
            Updates our input.input_metadata table.
        '''
        query = '''
                UPDATE input_metadata SET
                    spam_root_input_id=%d
                    WHERE input_id=%d
                ;''' % (spam_id, input_id)
        self.db.execute_sql(query)
