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
import dicts

_GAP_PENALTY = 1
_SWITCH_PENALTY = 1

class LevenTrie(object):
    def __init__(self, entries = None, gap_penalty = _GAP_PENALTY, 
                switch_penalty = _SWITCH_PENALTY):
        self._sub_trie = {}
        self._num_sub_entries = 0
        self._sub_trie_min_depth = 0
        self._node = None
        self._node_count = 0

        #TODO setters
        self._gap_penalty = gap_penalty
        self._switch_penalty = switch_penalty

        self.insert_list(entries)

    # INSERT
    def insert_list(self, entries):
        if not entries:
            return
        if entries:
            for entry in entries:
                self.insert(entry)

    def insert(self, entry):
        if not entry:
            return
        if len(entry) < self._sub_trie_min_depth:
            self._sub_trie_min_depth = len(entry) 
        self._insert(self._sanitize(entry))

    def _insert(self, entry, whole_word = None):
        self._num_sub_entries += 1
        if not whole_word:
            whole_word = entry
        if len(entry) == 0:
            self._node = whole_word
            self._node_count += 1
            return 1
        
        if not entry[0] in self._sub_trie:
                self._sub_trie[entry[0]] = LevenTrie()    
        return self._sub_trie[entry[0]]._insert(entry[1:], whole_word)
   
    # SEARCH 
    def search(self, entry, threshold = 1.5):
        threshold = threshold*len(entry)/4
        tmp = self._search(self._sanitize(entry), threshold)
        return tmp[0]

    def _search(self, entry, threshold, counter = 0):
        counter += 1
        #
        #print '===================================================='
        #print entry
        #print self
        record = [None, None]
        if threshold < 0:
            return record

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
            elif threshold < self._gap_penalty*min_diff:
                return record
        else:
            # shorten entry
            record = self._list_max(record, 
                    self._search(entry[1:], threshold - self._gap_penalty, counter))

        if search_trie:
            for k,v in self._sub_trie.items():
                # shorten words
                record = self._list_max(record, 
                        v._search(entry, threshold - self._gap_penalty, counter))
                # shorten entry and words
                if shorten_entry:
                    record = self._list_max(record, 
                            v._search(entry[1:], threshold - self._diff(entry[0], k), counter))
        
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

    # GETTERS/SETTERS

    def get_gap_penalty(self, n):
        return self._gap_penalty
    
    def set_gap_penalty(self, n):
        self._gap_penalty = n
    
    def get_switch_penalty(self, n):
        return self._switch_penalty
    
    def set_switch_penalty(self, n):
        self._switch_penalty = n

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
        return 0 if v1 == v2 else self._switch_penalty

    def _list_max(self, l1, l2):
        return l2 if l2[1] >= l1[1] else l1

    def _sanitize(self, word):
        return re.sub(r'[\W_0-9]+', '', word).lower()
    
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



#TODO: move this to the tests
def tmp():
    d = LevenTrie()
    d.insert_list(['cats', 'cats', 'cots', 'digs', 'face', 'faces', 'facebook'])
    print ['cats', 'cats', 'cots', 'digs', 'face', 'faces', 'facebook']
    print ['cats', d.search('cats')]
    print ['cost', d.search('cost')]
    print ['cot', d.search('cot')]
    print ['fac', d.search('fac')]
    print ['facebok', d.search('facebok')]
    print ['tractor', d.search('tractor')]


if __name__ == '__main__':
    tmp()
