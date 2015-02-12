#!/usr/local/bin/python

"""
Converts survey result CSV files to MySQL tables.
"""

__author__ = "Rob Rayborn"
__copyright__ = "Copyright 2014, The Mozilla Foundation"
__license__ = "MPLv2"
__maintainer__ = "Rob Rayborn"
__email__ = "rrayborn@mozilla.com"
__status__ = "Development"

# import external language library
from nltk.stem import WordNetLemmatizer
from nltk.stem.snowball import SnowballStemmer

def main():
    s = Simplifier()
    for word in ['cats','cat','car','disses']:
        print ['stem %s' % word,      s.stem(word)]
        print ['lemmatize %s' % word, s.lemmatize(word)]
        print ['simplify %s' % word,  s.simplify(word)]


class Simplifier(object):

    def __init__(self, stemmer = SnowballStemmer("english"), 
                 lemmatizer = WordNetLemmatizer()):
        self.stemmer    = stemmer
        self.lemmatizer = lemmatizer


    def stem(self, word):
        """
        Stems a word

        Args:
            word (string): The word that needs stemming

        Returns:
            str: The stemmed word

        Examples:
            >>> stem("cars")
            "cars"
        """
        return self.stemmer.stem(word)


    def lemmatize(self, word):
        """
        Lemmatize a word

        Args:
            word (string): The word that needs lemmatized

        Returns:
            str: The lemmatized word

        Examples:
            >>> lemmatize("better")
            "good"
        """
        return self.lemmatizer.lemmatize(word)


    def simplify(self, word):
        """
        Simplfies a word using the most advanced methods we have implemented at the 
        moment.    This allows us a layer of abstraction to not have to refactor our 
        code if we come up with a better grouping methodology

        Args:
            word (string): The word that needs simplified

        Returns:
            str: The simplified word

        Examples:
            >>> simplify("better")
            "good"
        """
        return self.stem(self.lemmatize(word))

if __name__ == '__main__':
    main()

#TODO(rrayborn): I'm not worrying about this more advanced functionality for now
#    def stem_list(self, words):
#        stem_lambda = lambda w: stem(w, self.stemmer)
#        return map(self.stem_lambda, words)
#
#    def lemmatize_list(self, words):
#        return map(self.lemmatize, words)
#
#    def simplify_list(self, words):
#        simplify_lambda = lambda w: simplify(w, self.stemmer)
#        return map(self.simplify_lambda, words)
#
#    def simplify_and_count(self, words, fn = self.simplify_list):
#        #TODO: Test this and fix any issues
#        """
#        Applies a simplifying function to a list of words and counts the result.
#
#        Args:
#            word (string): The word that needs simplified
#
#        Returns:
#            TODO
#
#        Examples:
#            TODO
#        """
#        counter = DefaultDict(0)
#
#        for word in fn(words):
#            counter[word] += 1
#        
#        return dict(counter)
#
