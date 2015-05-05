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

_GAP_PENALTY = 1
_SWITCH_PENALTY = 1


class LevenClassifier(object):
    def __init__(self, entries = None, gap_penalty = _GAP_PENALTY, 
                switch_penalty = _SWITCH_PENALTY, min_len = 3, threshold_ratio = .75):
        self.min_len          = min_len
        self.threshold_ratio  = threshold_ratio
        self.leven_trie       = LevenTrie(entries = entries, 
                                          gap_penalty = gap_penalty,
                                          switch_penalty = switch_penalty)

    def unique_list(self, entries):
        ret = []
        for entry in entries:
            is_unique = self.is_unique(entry)
            if is_unique:
                ret.append(entry)
        return ret

    def unique_dict(self, entries):
        ret = {}
        for entry_key, entry in entries.iteritems():
            is_unique = self.is_unique(entry)
            if is_unique:
                ret[entry_key] = entry
        return ret

    def is_unique(self, entry):

        if len(entry) <= self.min_len:
            return True
        threshold = 1 + (1 - self.threshold_ratio) * len(entry) # just a heuristic

        if self.leven_trie._num_sub_entries > 0:
            match = self.leven_trie.search(entry, threshold)
        else:
            match = False

        if match:
            return False
        else:
            self.leven_trie.insert(entry)
            return True



class LevenTrie(object):
    def __init__(self, entries = None, gap_penalty = _GAP_PENALTY, 
                switch_penalty = _SWITCH_PENALTY):
        self._sub_trie = {}
        self._num_sub_entries = 0
        self._sub_trie_min_depth = 0
        self._node = None
        self._node_count = 0

        #TODO setters
        self.gap_penalty = gap_penalty
        self.switch_penalty = switch_penalty

        self.insert_list(entries)

    # INSERT
    def insert_list(self, entries):
        if not entries:
            return
        for entry in entries:
            self.insert(entry)

    def insert(self, entry):
        if not entry:
            return
        if len(entry) < self._sub_trie_min_depth:
            self._sub_trie_min_depth = len(entry) 
        self._insert(entry)

    def _insert(self, entry, whole_entry = None):
        self._num_sub_entries += 1
        if not whole_entry:
            whole_entry = str(entry)
        if len(entry) == 0:
            self._node = whole_entry
            self._node_count += 1
            return 1
        
        if not entry[0] in self._sub_trie:
                self._sub_trie[entry[0]] = LevenTrie(
                        gap_penalty = self.gap_penalty,
                        switch_penalty = self.switch_penalty
                    )    
        return self._sub_trie[entry[0]]._insert(entry[1:], whole_entry)
   
    # SEARCH 
    def search(self, entry, threshold = 1.5):
        tmp = self._search(entry, threshold)
        return tmp[0]

    def _search(self, entry, threshold, tries = None):

        record = [None, None]
        if threshold < 0:
            return record

        if tries is None:
            tries = {}
        key = self.__repr__() + str(entry)
        if key in tries.keys():
            if threshold < tries[key]:
                return record
        tries[key] = threshold


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
                return [self._node, threshold]
            elif threshold < self.gap_penalty*min_diff:
                return record
        else:
            # shorten entry
            record = self._list_max(record, 
                    self._search(entry[1:], threshold - self.gap_penalty, tries = tries))

        if search_trie:
            for k,v in self._sub_trie.items():
                # shorten words
                record = self._list_max(record, 
                        v._search(entry, threshold - self.gap_penalty, tries = tries))
                # shorten entry and words
                if shorten_entry:
                    record = self._list_max(record, 
                            v._search(entry[1:], threshold - self._diff(entry[0], k), tries = tries))
        
        return record
    
    # CSV loader/saver
    def load_csv(self, filename):
        with open(filename, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='\"')
            for row in csv_reader:
                self.abusive_words_trie.insert_list(row)
    
    def save_csv(self, filename):
        with open(filename, 'wb') as csv_file:
            csv_writer = csv.writer(csv_file, delimiter=',',
                            quotechar='\"', quoting=csv.QUOTE_MINIMAL)
            csv_writer.writerow(self.get_list())

    def get_list(self, ):
        l = []
        if self._node:
            for i in range(0, self._node_count):
                l.append(self._node)
        for ld in self._sub_trie.values():
            l.extend(ld.get_list())
        return l

    # HELPER FUNCTIONS
    def _diff(self, v1, v2):
        return 0 if v1 == v2 else self.switch_penalty

    def _list_max(self, l1, l2):
        return l2 if l2[1] >= l1[1] else l1
    
    # STR FUNCTION
    def __str__(self):
        return self._get_str()[1:]

    def _get_str(self, count = 0):
        s = ''
        if self._node:
            s += '\n' + count * '\t' + self._node + ' ' + str(self._node_count) + ' ' + str(self._sub_trie_min_depth)
            count += 1
        for ld in self._sub_trie.values():
            s += ld._get_str(count)
        return s



##TODO: move this to the tests
#def main():
#    #d = LevenTrie()
#    #d.insert_list(['cats', 'cats', 'cots', 'digs', 'face', 'faces', 'facebook'])
#    #print ['cats', 'cats', 'cots', 'digs', 'face', 'faces', 'facebook']
#    #print ['cats', d.search('cats')]
#    #print ['cost', d.search('cost')]
#    #print ['cot', d.search('cot')]
#    #print ['fac', d.search('fac')]
#    #print ['facebok', d.search('facebok')]
#    #print ['tractor', d.search('tractor')]
#    from lib.language.word_types import dumb_tokenize
#
#    d1 = LevenClassifier()
#    l1 = d1.unique_list([
#            dumb_tokenize('blah blah blah! cat_browser is better'),
#            dumb_tokenize('blah blah blah! cat_browser is good'),
#            dumb_tokenize('blah blah blah! cat_browser is better!'),
#            dumb_tokenize('blah blah blah! cat_browser is much better!'),
#            dumb_tokenize('blah blah blah! cat_browser should be considered'),
#            dumb_tokenize('crash crash crash')
#        ])
#    print l1
#    d2 = LevenClassifier()
#    l2 = d2.unique_dict({
#            'id_a':dumb_tokenize('blah blah blah! cat_browser is better'),
#            'id_b':dumb_tokenize('blah blah blah! cat_browser is good'),
#            'id_c':dumb_tokenize('blah blah blah! cat_browser is better!'),
#            'id_d':dumb_tokenize('blah blah blah! cat_browser is much better!'),
#            'id_e':dumb_tokenize('blah blah blah! cat_browser should be considered'),
#            'id_f':dumb_tokenize('crash crash crash')
#        })
#    print l2
#
#
#if __name__ == '__main__':
#    main()
