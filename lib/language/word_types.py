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

#TODO(rrayborn): Better helpfulness

# import external language library
import csv
import re
import string
import unicodedata
from collections import defaultdict,Counter
from math import log10, pow
from os import path

import enchant

from lib.language.similarity import Simplifier


# globals
_PATH = path.dirname(path.realpath(__file__))+'/'
_SPAM_WORDS_CSV          = _PATH + 'spam_words.csv'
_INAPPROPRIATE_WORDS_CSV = _PATH + 'inappropriate_words.csv'
_COMMON_WORDS_CSV        = _PATH + 'common_words.csv'
_WORD_MAPPINGS_CSV       = _PATH + 'word_mappings.csv'
_TLD_CSV                 = _PATH + 'tlds.csv'

_DEFAULT_CLASSIFIER      = None
_SIMPLIFIER              = Simplifier()

_VERBOSE = False

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
    comment = standardize_encoding(comment)

    # Parse    
    return word_classifier.parse_comment(comment)

def standardize_encoding(comment):
    if isinstance(comment, str):
        comment = comment.decode('utf-8')
    elif (not isinstance(comment, unicode)):
        raise TypeError('comment should be str or unicode. Got ' + \
                type(comment))
    return ''.join(c for c in unicodedata.normalize('NFD', comment) \
                      if unicodedata.category(c) != 'Mn')

def dumb_tokenize(comment):
    comment = standardize_encoding(comment)
    return filter(None, re.split(r"[|,]|\s+|[^\w'.-]+|[-.'](\s|$)", 
                  comment.encode('utf-8')))

# =========== WORD TYPES ==============================================

def mylower(my_func):
    def internal_func(self, word):
        return my_func(self, word.lower())
    return internal_func


class WordClassifier(object):
    '''
    An object for classifying comments.  ONLY USED IF YOU WANT TO USE N
    ON-DEFAULT CSV PATHS TO POPULATE THE VALUES.  This is unlikely, but a nice
    to have option.
    '''
    def __init__(self, 
                 spam_csv          = _SPAM_WORDS_CSV, 
                 inappropriate_csv = _INAPPROPRIATE_WORDS_CSV, 
                 common_csv        = _COMMON_WORDS_CSV, 
                 mapping_csv       = _WORD_MAPPINGS_CSV):
        
        self.spam_words          = self._parse_csv(spam_csv)
        self.inappropriate_words = self._parse_csv(inappropriate_csv)
        self.common_words        = self._parse_csv(common_csv)
        self.word_mappings       = {}
        self.phrase_mappings     = {}
        self._load_mapping_csv(mapping_csv)

    @mylower
    def is_spam(self, word):
        return word in self.spam_words

    @mylower
    def is_inappropriate(self, word):
        return word in self.inappropriate_words

    @mylower
    def is_common(self, word):
        return word in self.common_words

    def translate_word(self, word):
        is_mapping = (word.lower() in self.word_mappings.keys())
        return self.word_mappings[word.lower()] if is_mapping else word
    
    def _parse_phrases(self, comment):
        comment = ' ' + comment + ' '

        # Parse the phrases out
        for phrase, resolution in self.phrase_mappings.iteritems():
            if phrase in comment:
                regex = re.compile(r'([\W]+)(%s)([\W^]+)' % phrase)
                regex_iter = regex.finditer(comment)
                i = 0
                for match in regex_iter:
                    current_resolution = match.group(1) + \
                            resolution + match.group(3)
                    comment = comment[:match.start() - i] + \
                            current_resolution + comment[match.end() - i:]
                    len_old = len(match.group(0))
                    len_new = len(current_resolution)
                    i = len_old - len_new
        return comment[1:-1]

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

        # Parse out phrases
        comment = self._parse_phrases(comment)
                
        # Score
        helpfulness = scorer().score(comment)

        # Regex Matches
        comment = self._parse_comment_with_regexes(comment, words_dict)


        # Tokenize
        words = dumb_tokenize(comment)
        for word in words:
            min(self._parse_word(word, words_dict = words_dict), helpfulness)

        # Catch weird cases
        for k in words_dict.keys():
            if k:
                if k.strip() != k:
                    new_k = k.strip()
                    if new_k in words_dict.keys():
                        words_dict[new_k] = words_dict[new_k].union(words_dict[k])
                    else:
                        words_dict[new_k] = words_dict[k]
                    del words_dict[k]
                words_dict[k] = set([e.strip() for e in words_dict[k]])
            else:
                del words_dict[k]


        return words_dict, helpfulness

    def _parse_word(self, word, words_dict, original = None):
        '''
        Parses a word to it's simplified value. Has a 
        side-effect of updating the words_dict.

        Args:
            word (string):                The raw word
            words_dict(defaultdict(set)): The words_dict to update
            original (string):            Overrides the key value to update in words_dict

        Returns:
            word (str):       The simplified word value

        '''
        simplifier = _SIMPLIFIER
        nonword_regex = re.compile(r'\W+')
        version_regex = re.compile(r'^(v|ver|version|ff|fx|firefox)?[\d.a]*$')

        if not original:
            original = word
        if not word or nonword_regex.match(word) or version_regex.match(word):
            return
        # Apply Mappings
        word = self.translate_word(word)
        # Remove common [Pre] and check for spam
        if self.is_common(word) or self.is_spam(word):
            return
        # Stem
        word = simplifier.simplify(word)
        # Remove common [Post]
        if self.is_common(word):
            return
        
        words_dict[word].add(original)

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
                    raise Warning('File %s does not have 2 columns as required'\
                                  % filename)

    def _parse_csv(self, filename):
        ret = set()
        with open(filename, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='\"')
            for row in csv_reader:
                if len(row) == 1:
                    ret.add(row[0])
                else:
                    raise Warning('File %s does not have 1 column as required' \
                                  % filename)
        return ret

    # === REGEX-BASED PARSING ==================================================

    def _get_url_regex(self, filename = _TLD_CSV):
        '''Returns a compiled URL regex with domains as specified in <filename>'''
        
        # create regex
        base_regex = r'(?:http[s]?://)?([a-zA-Z0-9]*\.)*' + \
                r'(?P<domain>[a-zA-Z0-9]+)\.(?:%s)+' + \
                r'(?:\/(?:[\S])*)?([/a-zA-Z0-9])'

        tlds = []
        with open(filename, 'rb') as csv_file:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='\"')
            for row in csv_reader:
                if len(row) == 1:
                    tlds.append(row[0].replace('.','\\.'))
                else:
                    raise Warning('File %s does not have 1 column as required' \
                                  % filename)

        return re.compile(base_regex % '|'.join(tlds))

#We're now parsing this at the word level, not at the comment level
#    def _get_version_regex(self):
#        '''Returns a complied version regex'''
#        regex = r'(?:firefox|version|release|firefox version|firefox release)[\W]{1,3}[0-9]{1,3}'
#        return re.compile(regex)


    def _parse_comment_with_regexes(self, comment, words_dict):
        '''Applies all of our regexes to parse the comment'''
        comment = self._parse_comment_with_regex(
                comment, self._get_url_regex(), words_dict = words_dict
            )
#           comment = self._parse_comment_with_regex(
#                   comment, self._get_version_regex(), replacement = ''
#               )

        return comment

    def _parse_comment_with_regex(self, comment, regex, words_dict = None, 
                                  replacement = None):
        '''Applies a regex to parse the comment'''
        match = regex.search(comment)
        if match:
            # print ['match',match.group(0)]
            if replacement:
                rep = replacement
            else:
                try:
                    ignore, rep = self._parse_word(match.group('domain'))
                except Exception:
                    return comment
            if words_dict is not None:
                words_dict[rep].add(match.group(0))
                comment = comment[:match.start()] + '' + \
                        self._parse_comment_with_regex(
                                comment[match.end():], regex, 
                                words_dict = words_dict,
                                replacement = replacement
                            )
            else:
                comment = comment[:match.start()] + ' ' + rep + ' ' + \
                        self._parse_comment_with_regex(
                                comment[match.end():], regex, 
                                words_dict = words_dict,
                                replacement = replacement
                            )

        return comment



# =========== HELPFULNESS SCORING ==============================================

def bound(floor = 0.0, ceiling = 1.0, verbose = _VERBOSE):
    def bound_decorator(score_func):
        def internal_func(*args,**kwargs):
            score = max(floor, min(ceiling, score_func(*args,**kwargs)))
            if verbose:
                print (score_func.__name__ + ':' + 30*' ')[:30]  + '%.2f' % \
                        round(score,2)
            return score
        return internal_func
    return bound_decorator

@bound(floor = 0.0, verbose=False)
def _log_score(val, multiplier = 10.0, divisor = 1.0):
    if divisor < 0.0:
        divisor = .0001
    if val <= 0 or multiplier <= 0:
        return 0.0
    return log10(multiplier / divisor * val)


class scorer(object):
    def __init__(self, comment = None):
        self.enchant_en = enchant.Dict('en_US')
        self.classifier = WordClassifier()

        if comment:
            self.process_comment(comment)

    def process_comment(self, comment):
        self.words                     = Counter()
        self.num_words                 = 0.01
        self.num_english_words         = 0
        self.num_non_english_words     = 0
        self.num_caps_words            = 0
        self.num_spam_words            = 0
        self.num_inappropriate_words   = 0
         
        new_comment = ''
        for word in dumb_tokenize(comment):
            word = self.classifier.translate_word(word)
            new_comment += word
            self.words[word] += 1
            self.num_words   += 1
        self.comment = new_comment

        self.num_chars         = len(self.comment)
        self.num_unique_words  = len(self.words)

        for word, cnt in self.words.iteritems():
            self.process_word(word, cnt)

    def process_word(self, word, cnt):
        if self.enchant_en.check(word):
            self.num_english_words += 1
        else:
            self.num_non_english_words += 1

        if self.classifier.is_spam(word):
            self.num_spam_words += 1

        if self.classifier.is_inappropriate(word):
            self.num_inappropriate_words += 1

        is_caps = True if len(word) > 1 else False
        for letter in word[1:]:
            if letter.islower():
                return
        if is_caps:
            self.num_caps_words += 1


    @bound()
    def comment_uniqueness(self):
        # This is based on words in this comment vs globally
        raise Warning('word_uniqueness not implemented.')
        return _log_score(10.0)

    @bound(floor=0.2)
    def length(self):
        return self.num_chars / 80.0

    @bound(floor=0.4)
    def unique_words(self):
        return _log_score(self.num_unique_words, divisor = self.num_words)

    @bound()
    def spam(self):
        return pow(0.25,(self.num_spam_words))

    @bound(floor=0.1)
    def inappropriate(self):
        return _log_score(self.num_words - 10*self.num_inappropriate_words, 
                          divisor = self.num_words)

    @bound(floor=0.1)
    def spelling_correctness(self):
        return _log_score(self.num_words - self.num_non_english_words, 
                          divisor = self.num_words)

    @bound(floor=0.4)
    def over_capitalization(self):
        return _log_score((self.num_words - 10*self.num_caps_words),
                          divisor = self.num_words)

    @bound()
    def word_complexity(self):
        return _log_score(self.num_chars, divisor = 5*self.num_words)

    @bound(ceiling = 10.0)
    def score(self, comment = None):
        if comment:
            self.process_comment(comment)
        return  (\
                    10.0 * \
                    self.length() * \
                    self.unique_words() * \
                    self.spam() * \
                    self.inappropriate() * \
                    self.spelling_correctness() * \
                    self.over_capitalization() * \
                    self.word_complexity()
                )


#def main(): #,   base_comments = None):
#    #
#    s = scorer()
#    for comment in _COMMENTS:
#        #print 20 * '=' + ' ' + comment + ' '  + 20 * '='
#        actual = s.score(comment)
#        print actual
#
#
#
#if __name__ == '__main__':
#    main()

##TODO: move this to the tests
def main():
#    _word_classifier = WordClassifier()
#    print ["_word_classifier.is_spam('palemoon')          ", _word_classifier.is_spam('palemoon')]
#    print ["_word_classifier.is_spam('palemoom')          ", _word_classifier.is_spam('palemoom')]
#    print ["_word_classifier.is_common('a')               ", _word_classifier.is_common('a')]
#    print ["_word_classifier.is_common('apple')           ", _word_classifier.is_common('apple')]
#    print ["_word_classifier.translate_word('ff')      ", _word_classifier.translate_word('ff')]
#    print ["_word_classifier.translate_word('firefox') ", _word_classifier.translate_word('firefox')]
#    print ["_word_classifier.translate_word('cats')    ", _word_classifier.translate_word('cats')]
#    examples = [
#            ' Fire fox 35 is crashing on http://a.b.c.youtube.com/blah/blah/123&123+abc=efg.html. I don\'t  like when 35 crashes on youtube.com. Tést.com',
#            ' Stack Overflow is a question and answer site for professional and enthusiast programmers. It\'s 100 free, no registration required.',
#            'fire fox crash',
#            'For the paper called fuck "The gravity tunnel in a non-uniform Earth" Alexander R. Klotz, when i open the pdf in firefox on page 3, the square root sign is almost touching the text below it in equation (3) in auto zoom, see (http://imgur.com/DlX1Ogw) and it shows better when set to page width see (http://imgur.com/PRC7kW2). this has been present for many releases, hope you can add it to your list of things to fix in future pdf.js releases! thanks'
#        ]
#    for example in examples:
#        print example
#        a,b = tokenize(example)
#        print a
#        print b
#        print dumb_tokenize(example)
    
    from lib.database.input_db    import Db as Input_DB

    input_db = Input_DB(is_persistent = True)

    query = '''select description 
            from feedback_response 
            where DATE(created) = "2015-05-01" 
                and locale="en-US" 
                and product="firefox" 
            limit 100;
        '''

    data = input_db.execute_sql(query)
    #data = [['BVGVGVHFFB HFGHJUFJH']]
    for row in data:
        #print 80 * '='
        a,b = tokenize(row[0])
        print str(b) + '\t' + str([row[0]])[1:-1]



if __name__ == '__main__':
    main()
