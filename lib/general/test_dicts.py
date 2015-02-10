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
from dicts import CountDict,Counter
import unittest


class TestCountDict(unittest.TestCase):
    #def setUp(self):
        
    def test_countdict(self):
        cd = CountDict()
        self.assertEqual(len(cd.get_dict()),0)

        cd = CountDict(['cat', 'cat', 'dog', 'cat', 'pig'])
        self.assertEqual(len(cd.get_dict()),3)
        self.assertEqual(cd.get('cat'),3)
        self.assertEqual(cd.get('pig'),1)

        cd.insert_list(['cat', 'dog', 'goat'])
        self.assertEqual(len(cd.get_dict()),4)
        self.assertEqual(cd.get('cat'),4)
        self.assertEqual(cd.get('dog'),2)
        self.assertEqual(cd.get('pig'),1)
        # should raise an exception for an immutable sequence
        with self.assertRaises(Warning):
            cnt = cd.get('dinosaur')
            self.assertEqual(cnt,0)


if __name__ == '__main__':
    unittest.main()