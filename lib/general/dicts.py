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


class CountDict(object):
    def __init__(self, entries = None):
        self._entries = {}
        self._count = 0

        self.insert_list(entries)

    def insert_list(self, entries):
        if entries:
            for entry in entries:
                self.insert(entry)

    def insert(self, entry):
        if not (entry in self._entries):
            self._entries[entry] = 1
        else:
            self._entries[entry] += 1
        self._count += 1

    def get(self, entry):
        if entry not in self._entries.keys():
            raise Warning("CountDict does not contain key %s" % entry)
            return 0
        return self._entries[entry]

    def get_dict(self):
        return self._entries

    def get_count(self, entry):
        return self._count

    def __str__(self):
        return str(self._entries)
