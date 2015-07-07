# -*- coding: utf-8 -*-

'''Server data access endpoints'''

import os
import traceback

import flask.json
from flask import (current_app, Flask, Blueprint, request, render_template, url_for, flash, redirect, session, send_from_directory, safe_join, Response)
from flask.ext.login import current_user
from flask.ext.login import login_required
from functools import wraps

from werkzeug.exceptions import Unauthorized, Forbidden, NotFound, BadRequest, Conflict
from werkzeug.datastructures import MultiDict

from useradvocacy.user.models import User
from useradvocacy.database import db
from useradvocacy.extensions import login_manager
from useradvocacy.utils import flash_errors, check_admin, nocache, jsonerror

from .stats import stats_return
from .heartbeat_stats import heartbeat_stats_return
from .telemetry import telemetry_stats, telemetry_stat, telemetry_params



blueprint = Blueprint('data', __name__, static_folder="./static",
        url_prefix="/data", template_folder="./templates")

@nocache
@blueprint.route("/api/v1/stats", methods=["GET"])
@jsonerror
def stats_api():
    args = parse_args(request.args)
    ret = stats_return(args)
    return ret

@nocache
@blueprint.route("/api/v1/heartbeat_stats", methods=["GET"])
@jsonerror
def heartbeat_stats_api():
    args = parse_args(request.args)
    ret = heartbeat_stats_return(args) #TODO(rrayborn)
    return ret

@nocache
@blueprint.route("/api/v1/telemetry/params", methods=["GET"])
@jsonerror
def telemetry_params_api():
    return telemetry_params()

@nocache
@blueprint.route("/api/v1/telemetry", methods=["GET"])
@jsonerror
def telemetry_stats_api():
    args = parse_args(request.args)
    ret = telemetry_stats(args)
    return ret

@nocache
@blueprint.route("/api/v1/telemetry_stat", methods=["GET"])
@jsonerror
def telemetry_stat_api():
    args = parse_args(request.args)
    ret = telemetry_stat(args)
    return ret

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
