# -*- coding: utf-8 -*-
'''Helper utilities and decorators.'''
from flask import flash, current_app
from flask.ext.login import current_user
from functools import wraps
from werkzeug.exceptions import Unauthorized, Forbidden, NotFound, BadRequest, Conflict


def flash_errors(form, category="warning"):
    '''Flash all errors for a form.'''
    for field, errors in form.errors.items():
        for error in errors:
            flash("{0} - {1}"
                    .format(getattr(form, field).label.text, error), category)


def check_admin(fn):
    @wraps(fn)
    def new_fn(*args, **kwargs):
        if current_user.is_admin:
            return fn(*args, **kwargs)
        else:
            return current_app.login_manager.unauthorized()
    return new_fn

def nocache(view):
    @wraps(view)
    def no_cache(*args, **kwargs):
        response = make_response(view(*args, **kwargs))
        response.headers['Last-Modified'] = datetime.now()
        response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '-1'
        return response
        return update_wrapper(no_cache, view)
