#!/usr/local/bin/python
# -*- coding: utf-8 -*-

'''
Data structures that classify word types
'''

__author__ = "Rob Rayborn"
__copyright__ = "Copyright 2014, The Mozilla Foundation"
__license__ = "MPLv2"
__maintainer__ = "Rob Rayborn"
__email__ = "rrayborn@mozilla.com"
__status__ = "Development"

#TODO(rrayborn): Better URL parsing
#TODO(rrayborn): Better helpfulness

# import external language library
import csv
import re
import string
import unicodedata

from collections import defaultdict
from os import path
from lib.language.similarity import Simplifier

# globals
_PATH = path.dirname(path.realpath(__file__))+'/'
_SPAM_WORDS_CSV    = _PATH + "spam_words.csv"
_COMMON_WORDS_CSV  = _PATH + "common_words.csv"
_WORD_MAPPINGS_CSV = _PATH + "word_mappings.csv"
_TLD_CSV           = _PATH + "tlds.csv"

_DEFAULT_CLASSIFIER = None
_SIMPLIFIER         = Simplifier()

_HELPFULNESS_NUM_WORDS = 7

def tokenize(comment, word_classifier = None):
    '''
    Takes a comment in str or unicode, returns dict of stemmed words and realwords as
    str object

    Args:
        comment (string/unicode):         The raw comment string
        word_classifier (WordClassifier): The processor object, this is only 
            used if you want to use non-default classifier CSV _parse_comment_with_regexes
            [Default: WordClassifier()]

    Returns:
        words_dict(defaultdict(set)): {<simplified word>: (<original words)}
        helfulness (int):            A score of the comment's helfulness

    '''
    # Instantiate classifier
    if not word_classifier:
        global _DEFAULT_CLASSIFIER
        if not _DEFAULT_CLASSIFIER:
            _DEFAULT_CLASSIFIER = WordClassifier()
        word_classifier = _DEFAULT_CLASSIFIER

    # Standardize encoding
    if isinstance(comment, str):
        comment = comment.decode('utf-8')
    elif (not isinstance(comment, unicode)):
        raise TypeError("comment should be str or unicode. Got " + type(comment))
    comment = ''.join(c for c in unicodedata.normalize('NFD', comment) \
                      if unicodedata.category(c) != 'Mn')

    # Parse    
    return word_classifier.parse_comment(comment)


class WordClassifier(object):
    '''
    An object for classifying comments.  ONLY USED IF YOU WANT TO USE N
    ON-DEFAULT CSV PATHS TO POPULATE THE VALUES.  This is unlikely, but a nice
    to have option.
    '''
    def __init__(self, 
                 spam_csv    = _SPAM_WORDS_CSV, 
                 common_csv  = _COMMON_WORDS_CSV, 
                 mapping_csv = _WORD_MAPPINGS_CSV):
        
        self.spam_words      = self._parse_csv(spam_csv)
        self.common_words    = self._parse_csv(common_csv)
        self.word_mappings   = {}
        self.phrase_mappings = {}
        self._load_mapping_csv(mapping_csv)


    def is_spam(self, word):
        return word in self.spam_words

    def is_common(self, word):
        return word in self.common_words

    def translate_word(self, word):
        return self.word_mappings[word] if (word in self.word_mappings.keys()) else word
    
    def parse_comment(self, comment):
        '''
        Parses a comment to it's components/helpfulness

        Args:
            comment (string): The raw comment string

        Returns:
            words_dict(defaultdict(set)): {<simplified word>: (<original words)}
            helfulness (int):             A score of the comment's helfulness

        '''
        words_dict  = defaultdict(set)

        comment = comment.lower()
        comment = ' ' + comment + ' '

        # Parse the phrases out
        for phrase, resolution in self.phrase_mappings.iteritems():
            if phrase in comment:
                regex = re.compile(r'([\W]+)(%s)([\W^]+)' % phrase)
                regex_iter = regex.finditer(comment)
                i = 0
                for match in regex_iter:
                    current_resolution = match.group(1) + resolution + match.group(3)
                    comment = comment[:match.start() - i] + current_resolution + comment[match.end() - i:]
                    len_old = len(match.group(0))
                    len_new = len(current_resolution)
                    i = len_old - len_new
        comment = comment[1:-1]
                
        # Regex Matches
        #comment = self._parse_comment_with_regexes(comment, words_dict)

        # Tokenize
        words = re.split(r"[|,]|\s+|[^\w'.-]+|[-.'](\s|$)", comment.encode('utf-8'))

        num_words = len(words)/2
        helpfulness = 10 if num_words > _HELPFULNESS_NUM_WORDS else 6
        for word in words:

            helpfulness = min(self._parse_word(word, words_dict = words_dict), helpfulness)

        return words_dict, helpfulness

    def _parse_word(self, word, words_dict = None, original = None):
        '''
        Parses a word to it's helpfulness rating and simplified value. Has a 
        side-effect of updating the words_dict.

        Args:
            word (string):                The raw word
            words_dict(defaultdict(set)): The words_dict to update
            original (string):            Overrides the key value to update in words_dict

        Returns:
            helfulness (int): A score of the comment's helfulness
            word (str):       The simplified word value

        '''
        simplifier = _SIMPLIFIER
        nonword_regex = re.compile(r'\W+')
        if not original:
            original = word
        helpfulness = 10

        if not word or nonword_regex.match(word): #TODO(rrayborn): this shouldn't happen but it is
            return helpfulness, None

        # Apply Mappings
        word = self.translate_word(word)
        # Remove common [Pre]
        if self.is_common(word):
            return helpfulness, None
        # Check for spam
        if self.is_spam(word):
            helpfulness = 0
            return helpfulness, None
        # Stem
        word = simplifier.simplify(word)
        # Remove common [Post]
        if self.is_common(word):
            return helpfulness, None
        if words_dict is not None:
            words_dict[word].add(original)
        return helpfulness, word

    # === FILE LOADERS =========================================================

    def _load_mapping_csv(self, filename = _WORD_MAPPINGS_CSV):
        with open(filename, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='\"')
            for row in csv_reader:
                if len(row) == 2:
                    self.phrase_mappings[row[0]] = row[1]
                    original = row[0]
                    new = row[1]
                    delim_re = re.compile('[\W_ ]+')
                    if delim_re.search(original):
                        self.phrase_mappings[original] = new
                    else:
                        self.word_mappings[original]   = new
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

    # === REGEX-BASED PARSING ==================================================

    def _get_simple_url_regex(self, filename = _TLD_CSV):
        '''Returns a compIled URL regex with domains as specified in <filename>'''
        # create regex
        base_regex = r'([a-zA-Z0-9]+)\.(?:%s)+(?:\/(?:[^ ])*)?' # 

        tlds = []
        with open(filename, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='\"')
            for row in csv_reader:
                if len(row) == 1:
                    tlds.append(row[0].replace('.','\\.'))
                else:
                    raise Warning("File %s does not have 1 column as required" % filename)

        return re.compile(base_regex % '|'.join(tlds))

    def _get_complex_url_regex(self, filename = _TLD_CSV):
        '''Returns a compIled URL regex with domains as specified in <filename>'''
        
        # create regex
        base_regex = r'(?:http[s]?://)?[a-zA-Z0-9]*\.?([a-zA-Z0-9]+)\.(?:%s)+(?:\/(?:[^ ])*)?' # 

        tlds = []
        with open(filename, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='\"')
            for row in csv_reader:
                if len(row) == 1:
                    tlds.append(row[0].replace('.','\\.'))
                else:
                    raise Warning("File %s does not have 1 column as required" % filename)

        return re.compile(base_regex % '|'.join(tlds))

    def _get_version_regex(self):
        '''Returns a complied version regex'''
        regex = r'(?:firefox|version|release|firefox version|firefox release)[\W]{1,3}[0-9]{1,3}'
        return re.compile(regex)


    def _parse_comment_with_regexes(self, comment, words_dict):
        '''Applies all of our regexes to parse the comment'''
        comment = self._parse_comment_with_regex(
                comment, self._get_simple_url_regex(), words_dict = words_dict
            )
#TODO(rrayborn): fix this to cover complex URLs (i.e. sub-domains/www/http)
#        comment = self._parse_comment_with_regex(
#                comment, self._get_complex_url_regex(), words_dict = words_dict
#            )
        comment = self._parse_comment_with_regex(
                comment, self._get_version_regex(), replacement = ''
            )

        return comment

    def _parse_comment_with_regex(self, comment, regex, words_dict = None, replacement = None):
        '''Applies a regex to parse the comment'''
        match = regex.search(comment)
        if match:
            # print ['match',match.group(0)]
            if replacement is None:
                ignore, rep = self._parse_word(match.group(1))
            else:
                rep = replacement
            if words_dict is not None:
                words_dict[rep].add(match.group(0))
                comment = comment[:match.start()] + '' + \
                        self._parse_comment_with_regex(
                                comment[match.end():], regex, 
                                words_dict = words_dict, replacement = replacement
                            )
            else:
                comment = comment[:match.start()] + ' ' + rep + ' ' + \
                        self._parse_comment_with_regex(
                                comment[match.end():], regex, 
                                words_dict = words_dict, replacement = replacement
                            )

        return comment

#def main():
#    _word_classifier = WordClassifier()
#    print ["_word_classifier.is_spam('palemoon')          ", _word_classifier.is_spam('palemoon')]
#    print ["_word_classifier.is_spam('palemoom')          ", _word_classifier.is_spam('palemoom')]
#    print ["_word_classifier.is_common('a')               ", _word_classifier.is_common('a')]
#    print ["_word_classifier.is_common('apple')           ", _word_classifier.is_common('apple')]
#    print ["_word_classifier.translate_word('ff')      ", _word_classifier.translate_word('ff')]
#    print ["_word_classifier.translate_word('firefox') ", _word_classifier.translate_word('firefox')]
#    print ["_word_classifier.translate_word('cats')    ", _word_classifier.translate_word('cats')]
#    examples = [
#            ' Fire fox 35 is crashing on youtube . I don\'t  like when fire fox crashes on youtube. Tést',
#            ' Stack Overflow is a question and answer site for professional and enthusiast programmers. It\'s 100 free, no registration required.',
#            'fire fox crash'
#        ]
#    for example in examples:
#        print example
#        a,b = tokenize(example)
#        print a
#        print b
#
#
#if __name__ == '__main__':
#    main()
