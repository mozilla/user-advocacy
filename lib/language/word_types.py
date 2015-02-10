#!/usr/local/bin/python

"""
Data structures that classify word types
"""

__author__ = "Rob Rayborn"
__copyright__ = "Copyright 2014, The Mozilla Foundation"
__license__ = "MPLv2"
__maintainer__ = "Rob Rayborn"
__email__ = "rrayborn@mozilla.com"
__status__ = "Development"

# import external language library
import csv

# globals
_ABUSIVE_WORDS_CSV = "abusive_words.csv"
_UNIMPORTANT_WORDS_CSV = "unimportant_words.csv"
_COMMON_WORDS_CSV = "common_words.csv"
_WORD_MAPPINGS_CSV = "word_mappings.csv"


class WordTypes(object):
    def __init__(self, 
                abusive_csv = ABUSIVE_CSV, 
                unimportant_csv = UNIMPORTANT_CSV, 
                common_csv = COMMON_CSV, 
                mapping_csv = _WORD_MAPPINGS_CSV):
        
        self._abusive_words_trie = LevenDict()
        self._abusive_words_trie.load_csv(abusive_csv)

        self._unimportant_words_trie = LevenDict()
        self._unimportant_words_trie.load_csv(unimportant_csv)

        self._common_words_trie = LevenDict()
        self._common_words_trie.load_csv(common_csv)

        self.load_mapping_csv(mapping_csv)

    """
    def get_abusive_words_trie():
        return self._abusive_words_trie

    def get_unimportant_words_trie():
        return self._unimportant_words_trie

    def get_common_words_trie():
        return self._common_words_trie
    """

    def is_abusive(self, word):
        return self._abusive_words_trie.search(word)

    def is_unimportant(self, word):
        return self._unimportant_words_trie.search(word)

    def is_common(self, word):
        return self._common_words_trie.search(word)

    def load_mapping_csv(self, filename):
        self._word_mappings = {}
        with open(filename, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='\"')
            for row in csv_reader:
                if len(row) == 2:
                    self._word_mappings[row[0]] = row[1]
                else: 
                    raise Warning("File %s does not match the pattern \".*,.*\"." % filename)

    def translate_mapping(self, word):
        return self._word_mappings[word] if (word in self._word_mappings.keys()) else word


