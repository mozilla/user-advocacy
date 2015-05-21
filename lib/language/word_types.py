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
from math import log, pow
from os import path

import enchant

from lib.language.similarity import Simplifier
from lib.database.backend_db  import Db as UA_DB

# globals
_PATH = path.dirname(path.realpath(__file__))+'/'
_SPAM_WORDS_CSV          = _PATH + 'spam_words.csv'
_INAPPROPRIATE_WORDS_CSV = _PATH + 'inappropriate_words.csv'
_COMMON_WORDS_CSV        = _PATH + 'common_words.csv'
_WORD_MAPPINGS_CSV       = _PATH + 'word_mappings.csv'
_TLD_CSV                 = _PATH + 'tlds.csv'

_DEFAULT_CLASSIFIER      = None
_SIMPLIFIER              = None

_VERBOSE = False

def _get_simplifier():
    global _SIMPLIFIER
    if not _SIMPLIFIER:
        _SIMPLIFIER = Simplifier()
    return _SIMPLIFIER

def _get_default_classifier():
    global _DEFAULT_CLASSIFIER
    if not _DEFAULT_CLASSIFIER:
        _DEFAULT_CLASSIFIER = WordClassifier()
    return _DEFAULT_CLASSIFIER


def tokenize(comment, input_id = None, word_classifier = None):
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
        word_classifier = _get_default_classifier()

    # Standardize encoding
    comment = standardize_encoding(comment)

    # Parse    
    return word_classifier.parse_comment(comment, input_id)

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

def _mylower(my_func):
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

    @_mylower
    def is_spam(self, word):
        return word in self.spam_words

    @_mylower
    def is_inappropriate(self, word):
        return word in self.inappropriate_words

    @_mylower
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

    def parse_comment(self, comment, input_id = None):
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
        helpfulness = Scorer().get_helpfulness(comment, input_id)

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

        simplifier = _get_simplifier()

        word_classifier = _get_default_classifier()
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

def _bound(floor = 0.0, ceiling = 1.0, verbose = _VERBOSE, round_dec = None):
    '''
    A decorator for bouding score outputs.
    
    Args:
        floor        (float): The minimum return val [Default: 0.0]
        ceiling      (float): The maximum return val [Default: 1.0]
        verbose       (bool): Whether to print diagnostics [Default: _VERBOSE]
        round_dec      (int): What decimal point to round to [Default: None]

    Returns:
        the bounded value of the function return

    '''
    def _bound_decorator(score_func):
        def _internal_func(*args,**kwargs):
            score = max(floor, min(ceiling, score_func(*args,**kwargs)))
            if round_dec is not None:
                score = round(score, round_dec)

            if verbose:
                print (score_func.__name__ + ':' + 30*' ')[:30]  + '%.2f' % \
                        score
            return score
        return _internal_func
    return _bound_decorator

@_bound(floor = 0.0, verbose=False)
def _log_score(val, divisor = 1.0, log_power = 10):
    '''
    Calculates a log based score.
    
    Args:
        val        (float): The value to score.
        divisor    (float): A number to divide value by prior to logging.
                            [Default: 1.0]
        log_power    (int): The log base [Default: 10]

    Returns:
        score (float): LOG((log_power - 1) * val / divisor  +  1.0), log_power)

    '''
    if divisor < 0.0: # make sure that NaN is impossible.
        divisor = .0001
    if val <= 0 or log_power < 1: # return 0 if obviously out of bounds
        return 0.0
    return log((log_power - 1) * val / divisor + 1.0, log_power)


class Scorer(object):
    def __init__(self,
                 enchant_en        = None,
                 classifier        = None,
                 db                = None):
        '''
        Object for scoring comments.

        Args:
            enchant_en   (enchant.Dict): Enchant Dict object, non-default
                                         discouraged [Default: None]
            classifier (WordClassifier): Classifier object, non-default
                                         discouraged [Default: None]
            db                     (DB): Database object, non-default
                                         discouraged [Default: None]
        '''
        self.enchant_en = enchant_en if enchant_en else enchant.Dict('en_US')
        self.classifier = classifier if classifier else WordClassifier()
        self.db         = db         if db         else UA_DB('input', is_persistent = True)

        # make sure the table exists
        #self.create_table() #TODO(rrayborn): permissions


    def get_helpfulness(self, comment = None, input_id = None, overwrite = False):
        '''
        Get's the helpfulness of the comment.  If it needs to be recalculated 
        then we write it out to our input.input_metadata table.

        Args:
            comment   (string): The comment text [Default: None]
            input_id     (int): The input ID, used for db writes [Default: None]
            overwrite   (bool): Whether to force an overwrite of our DB. Useful
                                for backfills.  [Default: False]

        Returns:
            score (float): The socre assigned 0.0 - 10.0

        Side-effect:
            Writes helfulness to input.input_metadata
        '''
        if overwrite: # If we want to overwrite don't fetch the score.
            score = None 
        else: # Fetch the score
            score = self._retrieve_helpfulness(input_id)
        if not comment or score: # if we haven't been provided the comment or
                                 # if we have a score to return
            return score
        #else: #we need to calculate the score
        score = self._process_comment(comment)
        
        if input_id: # if we know the input id then store it in our DB
            self.set_helpfulness(input_id, score)
        return score


    def set_helpfulness(self, input_id, score = None, comment = None):
        '''
        Stores the helpfulness score in our DB.

        Args:
            input_id     (int): The input ID, used for db writes.
            score      (float): The score to assign [Default: None]
            comment   (string): The comment text [Default: None]
            Either comment or score must be provided

        Returns:
            score (float): The socre assigned 0.0 - 10.0

        Side-effect:
            Writes helfulness to input.input_metadata
        '''

        if score is None: # if we don't know the score
            if not comment: # if we don't know the comment
                raise Warning('set_helpfulness: Either score or comment ' + \
                              'must be provided.')
                return None
            #else: # calculate the score from the comment
            score = self._process_comment(comment)
        elif comment:
            # if we have the score, we don't need the comment
            raise Warning('set_helpfulness: ignoring comment since score ' + \
                          'provided.')

        # At this point we have a score and an input ID, so we can output to DB

        query = '''
                REPLACE INTO input_metadata SET
                        input_id=%d, 
                        helpfulness_score=%d
                ;''' % (input_id, score)

        self.db.execute_sql(query)
        return score

    def create_table(self):
        '''
        Creates the input.input_metadata table if it doesn't exist.

        Side-effect:
            Creates input.input_metadata
        '''
        query = '''CREATE TABLE IF NOT EXISTS `input_metadata` (
                    `id`                 int(11)   NOT NULL AUTO_INCREMENT,
                    `input_id`           int(11)   NOT NULL,
                    `helpfulness_score`  float     NOT NULL,
                    `spam_root_input_id` int(11)   DEFAULT NULL,
                    PRIMARY KEY (`id`),
                    UNIQUE KEY (`input_id`)
                ) ENGINE=InnoDB  DEFAULT CHARSET=latin1;
            '''
        self.db.execute_sql(query)


    def _retrieve_helpfulness(self, input_id):
        # returns the helpfulness if it's know else calculates
        query = '''
                SELECT helpfulness_score
                FROM input_metadata 
                WHERE input_id = "%d"
                ;''' % input_id
        row = self.db.execute_sql(query).fetchone()
        return row[0] if row else None

    # ========== PROCESSING METHODS ================================
    @_bound(ceiling = 10, round_dec = 2)
    def _process_comment(self, comment):
        # Processes/Returns the score for a single comment

        self.words                     = None
        self.word_heuristic            = None
        self.word_counts               = Counter()
        self.num_words                 = 0.01
        self.num_english_words         = 0
        self.num_digit_words           = 0
        self.num_unclassified_words    = 0
        self.num_caps_words            = 0
        self.num_spam_words            = 0
        self.num_inappropriate_words   = 0
         
        new_comment = ''
        self.words = dumb_tokenize(comment)
        self.word_heuristic = [word[:5].lower() for word in self.words[:20]]
        for word in self.words:
            word = self.classifier.translate_word(word)
            new_comment += word
            self.word_counts[word] += 1
            self.num_words   += 1
        self.comment = new_comment

        self.num_chars         = len(self.comment)
        self.num_unique_words  = len(self.word_counts)

        for word, cnt in self.word_counts.iteritems():
            self._process_word(word, cnt)

        return 10.0 * pow( #_log_score(
                    self._words() * \
                    self._unique_words() * \
                    self._spam() * \
                    self._inappropriate() * \
                    self._spelling_correctness() * \
                    self._over_capitalization() * \
                    self._word_complexity()#,
                    #log_power = 2.0
                    , 2.0
                )

    def _process_word(self, word, cnt):
        # Processes a single word in a comment
        if word is None:
            return

        if self.enchant_en.check(word):
            self.num_english_words += 1
        elif any(char.isdigit() for char in word):
            self.num_digit_words += 1
        else:
            self.num_unclassified_words += 1

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

    # ========== ABSOLUTE METRICS ================================
    @_bound(floor=0.2)
    def _words(self):
        # score based on number of words
        return _log_score(self.num_words + 2, divisor = 20.0)

    @_bound()
    def _spam(self):
        # score based on number of spam words
        return pow(0.2,(self.num_spam_words))

    # ========== RELATIVE METRICS ================================
    @_bound(floor=0.4)
    def _unique_words(self):
        # score based on frequency of unique words
        return _log_score(self.num_unique_words, divisor = self.num_words)

    @_bound(floor=0.1)
    def _inappropriate(self):
        # score based on frequency of inappropriate words
        return _log_score(self.num_words - 10*self.num_inappropriate_words, 
                          divisor = self.num_words)

    @_bound(floor=0.1)
    def _spelling_correctness(self):
        # score based on frequency of potetentially misspelled words
        words = self.num_words - self.num_unclassified_words
        return _log_score(words - 1.2*self.num_unclassified_words, divisor = words)

    @_bound(floor=0.6)
    def _over_capitalization(self):
        # score based on frequency of OVERCAPITALIZED words
        return _log_score(self.num_words - self.num_caps_words,
                          divisor = self.num_words)

    @_bound()
    def _word_complexity(self):
        # score based on the average length of words
        return _log_score(self.num_chars, divisor = 5*self.num_words)

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
    from lib.language.leven       import SpamDetector

    dates = [
            #'2015-05-11',
            #'2015-05-12',
            #'2015-05-13',
            #'2015-05-14',
            #'2015-05-15',
            #'2015-05-16',
            '2015-05-17',
        ]
    input_db = Input_DB(is_persistent = True)

    query = '''Select id, description 
            from feedback_response 
            where 
                DATE(created) = "%s"
                and locale="en-US" 
                and product="firefox" 
            ;
        '''
    for day in dates:
        data = input_db.execute_sql(query % day)
        data_dict = {}
        for row in data:
            data_dict[row[0]] = row[1]
            a,b = tokenize(row[1], input_id=row[0])
            data_dict[row[0]] = dumb_tokenize(row[1])

        SpamDetector().check_entries_for_spam(data_dict)




if __name__ == '__main__':
    main()
