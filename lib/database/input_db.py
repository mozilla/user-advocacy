#!/usr/local/bin/python

"""
This is the database module for all input tasks. It inherits from db.py for all the
heavy lifting.
"""

import os
from . import db

os_env = os.environ

engine = db.init_engine(os_env['SQLALCHEMY_INPUT_URI'])

class Db(db.Database):
    def __init__(self, database_name, is_persistent = False):
        super(Db, self).__init__(database_name, engine, is_persistent)
