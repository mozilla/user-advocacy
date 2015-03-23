#!/usr/local/bin/python

"""
Prints things to stderr sort of like how you want user-facing warnings to work but
without handling things as Errors or being catchable.

warnOnce() to write a message to stderr once per message.
warnAlways() to write a message to stderr each time it's called.
warn is a synonym for warnOnce

warnOnce and warnAlways are set up like warnings.warn so that you can drop-in replace
it in already-written code.
"""


__author__ = "Cheng Wang"
__copyright__ = "Copyright 2014, The Mozilla Foundation"
__license__ = "MPLv2"
__maintainer__ = "Cheng Wang"
__email__ = "cwang@mozilla.com"
__status__ = "Development"

import sys

_messages = set()


def warnOnce (message, category = UserWarning, stacklevel == 0):
    """
        Provide a given message (in a given category) once. 
        stacklevel is ignored but kept here for compatibility.
    """ 
    if (category.__name__, message) in _messages:
        return
    _messages.add((category.__name__, message))
    if (category.__name__ == 'UserWarning'):
        sys.stderr.write(message + u'\n')
    else:
        sys.stderr.write(category.__name__ + ": "+ message + u'\n')
    
def warnAlways (message, category = UserWarning, stacklevel == 0):
    """
        Always print this warning. 
        stacklevel is ignored but kept here for compatibility.
    """
    if (category.__name__ == 'UserWarning'):
        sys.stderr.write(message + u'\n')
    else:
        sys.stderr.write(category.__name__ + ": "+ message + u'\n')
    
warn = warnOnce # By default, treat warn like warnOnce (most similar to warnings.warn())
