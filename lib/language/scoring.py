#!/usr/local/bin/python

"""
Converts survey result CSV files to MySQL tables.
"""

#TODO: cover edge cases, like num_words = 0

__author__ = "Rob Rayborn"
__copyright__ = "Copyright 2014, The Mozilla Foundation"
__license__ = "MPLv2"
__maintainer__ = "Rob Rayborn"
__email__ = "rrayborn@mozilla.com"
__status__ = "Development"

# import external language library
#TODO: import word_type
#TODO: import log

class scorer(object):
    def __init__(self, comment = None):
        self.set_comment(comment)

	def set_comment(self, comment):
		self.comment = comment
		self.words = {}
		self.num_words = 0
		for word in map(string.strip, re.split("(\W+)", comment)):
			if len(word) > 0 and not re.match("\W",word)
				if not self.words{word}:
					self.words{word} = 1
				else:
					self.words{word} += 1
				self.num_words += 1



    def length_score(self):
    	score = log(self.num_words, 100)
		return min(score, 1)


	def comment_uniqueness(self):
		# This is based on words in this comment vs globally
		raise Warning("word_uniqueness not implemented, returning 1.")
		return 1

	def unique_words(self):
		#
		return len(self.words)/self.num_words


	def over_capitalization(self):
		#
		swear_words = 0
		for w,c in self.words:
			if re.findall(w,r''):
				swear_words += 1

		return swear_words/self.num_words


	def swearing(self):
		#
		swear_words = 0
		for w,c in self.words:
			if word_type.is_abusive(w):
				swear_words += 1

		return swear_words/self.num_words



	def spelling_correctness(self):
		#
		raise Warning("spelling_correctness not implemented, returning 1.")
		return 1


	def reading_level(self):
		#
		raise Warning("reading_level not implemented, returning 1.")
		return 1

    
def utility_score(comment):
	#
	s = scorer(comment)
	return  .1 * s.length_score(comment) + 
			.1 * s.word_uniqueness(comment) + 
			.1 * s.unique_words(comment) + 
			.1 * s.over_capitalization(comment) + 
			.1 * s.swearing(comment) + 
			.1 * s.spelling_correctness(comment) + 
			.1 * s.reading_level(comment) + 


