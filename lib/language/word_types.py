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
from os import path

# globals
_PATH = path.dirname(path.realpath(__file__))+'/'
_SPAM_WORDS_CSV    = _PATH + "spam_words.csv"
_COMMON_WORDS_CSV  = _PATH + "common_words.csv"
_WORD_MAPPINGS_CSV = _PATH + "word_mappings.csv"


class WordClassifier(object):
    def __init__(self, 
                spam_csv    = _SPAM_WORDS_CSV, 
                common_csv  = _COMMON_WORDS_CSV, 
                mapping_csv = _WORD_MAPPINGS_CSV):
        
        self.spam_words = self._parse_csv(spam_csv)
        self.common_words = self._parse_csv(common_csv)
        self.word_mappings = {}
        self._load_mapping_csv(mapping_csv)


    def is_spam(self, word):
        return word in self.spam_words

    def is_common(self, word):
        return word in self.common_words

    def translate_mapping(self, word):
        return self.word_mappings[word] if (word in self.word_mappings.keys()) else word

    def _load_mapping_csv(self, filename):
        with open(filename, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='\"')
            for row in csv_reader:
                if len(row) == 2:
                    self.word_mappings[row[0]] = row[1]
                else: 
                    raise Warning("File %s does not have 2 columns as required" % filename)

    def _parse_csv(self, filename):
        ret = set()
        with open(filename, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='\"')
            for row in csv_reader:
                if len(row) == 1:
                    ret.add(row[0])
                else:
                    raise Warning("File %s does not have 1 column as required" % filename)
        return ret


#def main():
#    wc = WordClassifier()
#    print ["wc.is_spam('palemoon')          ", wc.is_spam('palemoon')]
#    print ["wc.is_spam('palemoom')          ", wc.is_spam('palemoom')]
#    print ["wc.is_common('a')               ", wc.is_common('a')]
#    print ["wc.is_common('apple')           ", wc.is_common('apple')]
#    print ["wc.translate_mapping('ff')      ", wc.translate_mapping('ff')]
#    print ["wc.translate_mapping('firefox') ", wc.translate_mapping('firefox')]
#    print ["wc.translate_mapping('cats')    ", wc.translate_mapping('cats')]
#if __name__ == '__main__':
#    main()