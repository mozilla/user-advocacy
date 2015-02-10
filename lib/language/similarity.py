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

#TODO: Make sure that our stemmer/lemmatizer support custom mapping.  
# 	If not implement a preprocessing function that does so (might be easier to
# 	do this approach regardless)

#TODO: organize this
_STEMMER = SnowballStemmer("english")
_WNL = WordNetLemmatizer()


def get_language_stemmer(language):
    return SnowballStemmer(language)


def stem_list(words, language_stemmer = _STEMMER):
    stem_lambda = lambda w: stem(w,language_stemmer)
    return map(stem_lambda, words)


def lemmatize_list(words):
    return map(lemmatize, words)


def simplify_list(words, language_stemmer = _STEMMER):
    simplify_lambda = lambda w: simplify(w,language_stemmer)
    return map(simplify_lambda, words)


def stem(word, language_stemmer = _STEMMER):
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
	return stemmer.stem(translate_mappings(word))


def lemmatize(word):
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
	return _WNL.lemmatize(translate_mappings(word))


def simplify(word, language_stemmer = _STEMMER):
	"""
	Simplfies a word using the most advanced methods we have implemented at the 
	moment.	This allows us a layer of abstraction to not have to refactor our 
	code if we come up with a better grouping methodology

	Args:
		word (string): The word that needs simplified

	Returns:
		str: The simplified word

	Examples:
		>>> simplify("better")
		"good"
	"""
	return stem(lemmatize(word), language_stemmer)


def simplify_and_count(words, fn = simplify_list):
    #TODO: Test this and fix any issues
    """
    Applies a simplifying function to a list of words and counts the result.

    Args:
        word (string): The word that needs simplified

    Returns:
        TODO

    Examples:
        TODO
    """
    counter = CountDict()

    for word in simplify_list(words):
        #TODO: make this exist
        counter.insert(word)
    
    return counter.get_dict()

