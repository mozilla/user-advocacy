#!/usr/local/bin/python

import sys
from os import path
#sys.path.append(path.normpath(path.join(path.dirname(__file__), '..', '..')))
#from lib.database.backend_db import Db
import csv
import json
import requests
import datetime

import operator
import re
from collections import defaultdict

sys.path.append('/home/rrayborn/user-advocacy')
from lib.language.similarity import Simplifier
from lib.language.word_types import WordClassifier

_TIMEFRAME = 12 # Hours
_PAST_TIMEFRAME = 3 # Weeks



def main():
    input_db = Db('input')
    
    old_data_sql = """
        SELECT description
        FROM remote_feedback_response fr
        WHERE
        created > DATE_SUB(NOW(), INTERVAL :old WEEK) AND
        created < DATE_SUB(NOW(), INTERVAL :new HOUR)
        AND product LIKE 'firefox'
        AND locale = 'en-US'
        AND happy = 0
        AND (campaign IS NULL or campaign = '')
        AND (source IS NULL or source = '')
        AND (version NOT RLIKE '[^a.0-9]')
        AND (platform LIKE 'Windows%' OR platform LIKE 'OS X' OR platform LIKE 'OS X')
    """
    
    results = telemetry_db.execute_sql(old_data_sql, { 
        'old' : _PAST_TIMEFRAME, 'new' : _TIMEFRAME 
        })


    {stemmed_word:<Word object>} = CommentWordCounter().process(results)
#    for row in results:
#        # Process stuff here
#        print row
        
    new_data_sql = """
        SELECT description
        FROM remote_feedback_response fr
        WHERE
        created > DATE_SUB(NOW(), INTERVAL :new HOUR) AND
        created < NOW()
        AND product LIKE 'firefox'
        AND locale = 'en-US'
        AND happy = 0
        AND (campaign IS NULL or campaign = '')
        AND (source IS NULL or source = '')
        AND (version NOT RLIKE '[^a.0-9]')
        AND (platform LIKE 'Windows%' OR platform LIKE 'OS X' OR platform LIKE 'OS X')
    """
    
    results = telemetry_db.execute_sql(new_data_sql, { 'new' : _TIMEFRAME })

    for row in results:
        # Process stuff here
        print row




class CommentWordCounter(object):

    def __init__(self):
        self.words = defaultdict(Word)
        self.classifier = WordClassifier()


    def process(self, comments):
        wc = self.classifier
        for comment_id, comment in comments.iteritems():

            words_dict = self._parse_comment(comment)
            for key, words in words_dict.iteritems():
                self.words[key].insert(words,comment_id)

        # Finalize data
        for key, word in self.words.iteritems():
            word.finalize(key)
        return self.words


    #TODO(rrayborn): remove any non [a-z] characters, replacing accented  
    #  characters with non-accented counterparts, if possible.
    def _parse_comment(self, comment):
        comment = comment.lower()
        # Tokenize
        words      = re.split(r"[|,]|\s+|[^\w'.-]+|[-.'](\s|$)", comment)

        is_spam    = False
        s          = Simplifier()
        words_dict = defaultdict(set)
        wc = self.classifier 
        for word in words:
            if word is None or word=='': #TODO(rrayborn): this shouldn't happen but it is
                continue
            # Apply Mappings
            new_word = wc.translate_mapping(word)
            # Remove common [Pre]
            if wc.is_common(new_word):
                continue
            # Check for spam
            if wc.is_spam(new_word):
                return None
            # Stem
            new_word = s.simplify(new_word)
            # Remove common [Post]
            if wc.is_common(new_word):
                continue
            words_dict[new_word].add(word)

        return words_dict


class Word(object):
    def __init__(self, key = None):
        self.key             = key
        self.max_word        = '' # determined by vote in finalize
        self.count           = 0
        self.words           = defaultdict(int)
        self.ids             = set()

    def insert(self, words, comment_id, key = None):
        if key:
            self.key = key
        for word in words:
            self.words[word] += 1
        self.ids.add(comment_id)
        self.count       += 1

    def finalize(self, key = None):
        if key:
            self.key = key
        
        self.max_word = max(self.words.iteritems(), 
                            key=operator.itemgetter(1))[0]

    def __str__(self):
        return 'Word with key %s, max_word %s, count %d, words %s, ids, %s' % (
                self.key,
                self.max_word,
                self.count,
                list(self.words),
                list(self.ids)
            )



if __name__ == '__main__':

#    cwc = CommentWordCounter()
#    words = cwc.process({
#            1:'hello it is crashing, I hate when it crashes so crashed',
#            2:'hello it is crashing, and it is slow',
#            3:'I\'m having issues with sync',
#        })
#    for key,word in words.iteritems():
#        print [key,str(word)]
    main()

