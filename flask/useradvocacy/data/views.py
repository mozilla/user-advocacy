# -*- coding: utf-8 -*-

'''Server data access endpoints'''

from flask import (current_app, Flask, Blueprint, request, render_template, url_for, flash, redirect, session, send_from_directory, safe_join, Response)
from werkzeug.exceptions import Unauthorized, Forbidden, NotFound, BadRequest, Conflict
from werkzeug.datastructures import MultiDict
                    
from useradvocacy.extensions import login_manager
from flask.ext.login import current_user
import traceback
from useradvocacy.user.models import User
from useradvocacy.database import db
from useradvocacy.utils import flash_errors, check_admin, nocache
import flask.json
from functools import wraps
from .stats import stats_return
from .telemetry import telemetry_stats, telemetry_stat, telemetry_params
import os

from flask.ext.login import login_required

blueprint = Blueprint('data', __name__, static_folder="./static", 
        url_prefix="/data", template_folder="./templates")

@nocache
@blueprint.route("/api/v1/stats", methods=["GET"])
def stats_api():
    try:
        args = parse_args(request.args)
        ret = stats_return(args)
        return ret
    except Exception as e:
        return str(traceback.format_exc())

@nocache
@blueprint.route("/api/v1/telemetry/params", methods=["GET"])
def telemetry_params_api():
    try:
        return telemetry_params()
    except Exception as e:
        return str(traceback.format_exc())

@nocache
@blueprint.route("/api/v1/telemetry", methods=["GET"])
def telemetry_stats_api():
    try:
        args = parse_args(request.args)
        ret = telemetry_stats(args)
        return ret
    except Exception as e:
        return str(traceback.format_exc())

@nocache
@blueprint.route("/api/v1/telemetry_stat", methods=["GET"])
def telemetry_stat_api():
    try:
        args = parse_args(request.args)
        ret = telemetry_stat(args)
        return ret
    except Exception as e:
        return str(traceback.format_exc())

@blueprint.route("/static/json/<file>", methods=["GET"])
def json_server(file):
    return send_from_directory(os.path.join(current_app.root_path, 'data', 'static_json'), file)

def parse_args(raw_args):
    args = MultiDict()
    for (arg_name, arg_outer_values) in raw_args.iterlists():
        for arg_inner_values in arg_outer_values:
            for arg_value in arg_inner_values.split(','):
                args.add(arg_name, arg_value.strip())
    return args
