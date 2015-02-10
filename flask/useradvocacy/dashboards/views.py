# -*- coding: utf-8 -*-

'''
Serve static files/folders that we check in as dashboards.
TODO: Add templates to served pages to give everything a nice consistent look

'''

from flask import (current_app, Flask, Blueprint, request, render_template, url_for, flash, redirect, session, send_from_directory, safe_join, Response)
from werkzeug.exceptions import Unauthorized, Forbidden, NotFound, BadRequest, Conflict
from useradvocacy.utils import flash_errors, check_admin
import os
import re
import flask.json
from functools import wraps
from werkzeug.utils import secure_filename
import shutil

from flask.ext.login import login_required


blueprint = Blueprint('dashboards', __name__, static_folder="./static", 
        url_prefix="/dashboards", template_folder=".")

@blueprint.route("/", methods=["GET"])
def home():
    return render_template('templates/dashboards.html')

@blueprint.route("static/css/<file>", methods=["GET"])
def serve_css(file):
    return send_from_directory(safe_join(current_app.root_path, "dashboards/static/css"), file)
    
@blueprint.route("static/img/<file>", methods=["GET"])
def serve_img(file):
    return send_from_directory(safe_join(current_app.root_path, "dashboards/static/img"), file)
    
@blueprint.route("static/js/<file>", methods=["GET"])
def serve_js(file):
    return send_from_directory(safe_join(current_app.root_path, "dashboards/static/js"), file)

@blueprint.route("/<name>/", methods=["GET"])
def dash_server(name):
    return render_template(safe_join(safe_join("files",name),"index.html"))
    
@blueprint.route("/<name>/<file>.html", methods=["GET"])
def dash_html_server(name, file):
    return render_template(safe_join(safe_join("files",name),file + ".html"))

@blueprint.route("/<name>/<file>", methods=["GET"])
def file_server(name, file):
    return send_from_directory(safe_join(safe_join(current_app.root_path, 'dashboards/files'), name), file)
