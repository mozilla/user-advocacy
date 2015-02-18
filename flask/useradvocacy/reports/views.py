# -*- coding: utf-8 -*-

'''Templating engine for reports'''


from flask import (current_app, Flask, Blueprint, request, render_template, url_for, flash, redirect, session, send_from_directory, safe_join, Response)
from werkzeug.exceptions import Unauthorized, Forbidden, NotFound, BadRequest, Conflict
                    
from useradvocacy.extensions import login_manager
from flask.ext.login import current_user
from useradvocacy.user.models import User
from useradvocacy.database import db
from useradvocacy.reports.models import User, Template, Report
from .forms import EditorForm, SelectorForm, PreviewForm
from useradvocacy.utils import flash_errors, check_admin
import os
import re
import flask.json
from functools import wraps
from werkzeug.utils import secure_filename
from .markdown2html import convert_md
import shutil

from flask.ext.login import login_required

blueprint = Blueprint('reports', __name__, static_folder="./static", 
        url_prefix="/reports", template_folder="./templates")

def upload_path():
    if current_app.config.['UPLOAD_PATH']:
        upload = os.path.join(current_app.config['UPLOAD_PATH'], 'reports')
    else:
        upload = os.path.join(current_app.root_path, 'reports', 'uploads')
    print upload
    return upload

def validate_project_filename(fn):
    @wraps(fn)
    def new_fn(project, filename, *args, **kwargs):
        if re.match('[a-zA-Z0-9_-]+$',project) or re.match('[a-zA-Z0-9_-]+$',filename):
            return fn(project, filename, *args, **kwargs)
        else:
            raise BadRequest()
    return new_fn
    

def allowed_file(name):
    if re.match('[^/.\'\\\\"]+\\.(css|js|png|jpg|jpeg|gif|json|csv|tsv|xml|pdf|key)$', name, flags=re.IGNORECASE):
        return True
    else:
        return False

@blueprint.route("/", methods=["GET"])
def home():
    reports = Report.query.order_by("updated").all()
    reports.reverse()
    projects = db.session.query(Report.project.label('name'), db.func.bit_or(db.and_(Report.published, Report.listed)).label('shown')).group_by('name').all()
    print projects[0].shown
    return render_template('reports.html', list = reports, projects = projects)

@blueprint.route("/css/<file>", methods=["GET"])
def serve_css(file):
    return send_from_directory(safe_join(current_app.root_path, "reports/static/css"), file)
    
@blueprint.route("/img/<file>", methods=["GET"])
def serve_img(file):
    return send_from_directory(safe_join(current_app.root_path, "reports/static/img"), file)
    
@blueprint.route("/js/<file>", methods=["GET"])
def serve_js(file):
    return send_from_directory(safe_join(current_app.root_path, "reports/static/js"), file)

@blueprint.route("/edit", methods=["GET", "POST"])
@login_required
@check_admin
def selector():
    form = SelectorForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            if form.action == "report":
                return redirect('/reports/' + form.project + '/' + form.filename 
                    + '/edit', 302)
            if form.action == "rerender":
                reports = Report.query.all()
                for report in reports:
                    report.save_render_html()
        else:
            flash_errors(form)
    return render_template('selector.html',form=form)
    
@blueprint.route("/<project>/", methods=["GET"])
def home_project(project):
    return redirect(url_for(".home") + "#" + project)


@blueprint.route("/<project>/<filename>/", methods=["GET", "POST"])
@validate_project_filename
def display(project, filename):
    report = Report.query.filter_by(filename = filename, project = project).first()
    if report:
        if report.published or (not current_user.is_anonymous() and
            current_user.is_admin):
            return report.html_content
        else:
            raise NotFound()
    else:
        raise NotFound()

@blueprint.route("/<project>/<filename>/edit", methods=["GET", "POST"])
@validate_project_filename
@login_required
@check_admin
def edit(project, filename):
    report = Report.query.filter_by(project = project, filename = filename).first()
    default_template = Template.query.filter_by(name = 'default').first()
    form = None
    if report:
        form = EditorForm(project_field=project, filename_field=filename, 
            template_field = report.template, markdown_field=report.md_content,
            published_field = report.published, listed_field = report.listed)
    else:
        form = EditorForm(project_field=project, filename_field=filename, 
            template_field = default_template, markdown_field=default_template.md_content)
    if request.method == 'POST':
        if form.validate_on_submit():
            save_user = None
            if current_user.is_anonymous():
                save_user = User.query.filter_by(username="<blank>").first()
            else:
                save_user = current_user
            if form.savemode is 'save':
                report = Report.query.filter_by(filename = form.filename, 
                    project = form.project).first()
                if report:
                    report.update(template_id = form.template.id, 
                        md_content = form.md_content,
                        listed = form.listed,
                        published = form.published)
                    flash("Report saved.", 'success')
                else:
                    report = Report.create(filename = form.filename, 
                        project = form.project, template = form.template, 
                        md_content = form.md_content, author = save_user,
                        listed = form.listed, published = form.published)
                    flash("New report created and saved!", 'success')
                report.save_render_html()
                form = EditorForm(project_field=form.project,
                    filename_field=form.filename, template_field=form.template,
                    markdown_field = form.md_content, listed_field = form.listed,
                    published_field = form.published)
            elif form.savemode is "saveas":
                report = Report.create(filename = form.filename, 
                    project = form.project, template = form.template, 
                    md_content = form.md_content, author = save_user,
                    listed = form.listed, published = form.published)
                report.save_render_html()
                old_path = os.path.join(upload_path(), form.old_project,
                    form.old_filename)
                new_path = os.path.join(upload_path(), form.project,
                    form.filename)
                # Move files along with copying data
                try:
                    files = os.listdir(old_path)
                except OSError:
                    pass
                else:
                    if os.path.exists(new_path):
                        flash("Files not copied!", 'error')
                    else:
                        shutil.copytree(old_path, new_path)
                        flash("Files copied!", 'success')
                flash("New report created and saved!", 'success')
                return redirect("/reports/" + form.project + "/" + 
                    form.filename + "/edit", 303)
            else:
                assert False
        else:
            flash_errors(form)
    preview_form = PreviewForm(markdown_preview_field = '', template_preview_field = '')
    return render_template('editor.html',form=form, project=project, 
        filename=filename, preview_form=preview_form)

@blueprint.route("/<project>/<filename>/upload", methods=["POST"])
@validate_project_filename
@login_required
@check_admin
def upload_file(project, filename):
    file = request.files['file']
    if file and allowed_file(file.filename):
        file_save = secure_filename(file.filename)
        try:
            os.makedirs(os.path.join(upload_path(), project, filename))
        except OSError:
            pass
        try:
            file.save(os.path.join(upload_path(), project, filename, file_save))
        except (IOError, OSError) as err:
            raise Conflict("Can't save file: " + err.strerror)
            flash("Can't save file: " + err.strerror, 'error')
        else:
            return "File uploaded", 200   
    else:
        raise Conflict("File upload failed: File not allowed")
    
    raise Conflict("Bad file upload!")

    
@blueprint.route("/<project>/<filename>/preview", methods=["POST"])
@validate_project_filename
def preview_file(project, filename):
    preview_form = PreviewForm()
    if preview_form.validate_on_submit():
        print preview_form.template_id
        template_id = Template.query.get(preview_form.template_id)
        md_content = preview_form.md_content
        env = current_app.create_jinja_environment()
        template = env.get_template(template_id.filename)
        print template
        return convert_md(md_content, template)
    else:
        return NotFound()
    
@blueprint.route("/<project>/<filename>/listfiles", methods=["GET"])
@validate_project_filename
@login_required
@check_admin
def list_files(project, filename):
    try:
        files = os.listdir(os.path.join(upload_path(), project, filename))
    except OSError:
        return Response(flask.json.dumps([]), status=200, mimetype='application/json')
    out_list = []
    for file_name in files:
        file_item = {
            "name": file_name,
            "size": os.path.getsize(os.path.join(upload_path(), project, 
                filename))
            }
        out_list.append(file_item)
    return Response(flask.json.dumps(out_list), status=200, mimetype='application/json')

@blueprint.route("/<project>/<filename>/md", methods=["GET"])
@validate_project_filename
def display_md(project, filename):
    report = Report.query.filter_by(filename = filename, project = project).first()
    if report:
        return Response(report.md_content, mimetype = 'text/plain', status = 200)
    else:
        raise NotFound()

# Keep this function last as it sucks up everything else in /reports/

@blueprint.route("/<project>/<filename>/<file>", methods=["GET"])
@validate_project_filename
def file_server(project, filename, file):
    return send_from_directory(os.path.join(upload_path(), project, filename), file)


@blueprint.route("/<project>/<filename>/<file>/delete", methods=["DELETE"])
@validate_project_filename
@login_required
@check_admin
def delete_file(project, filename, file):
    if not allowed_file(file):
        raise BadRequest()
    if os.path.exists(os.path.join(upload_path(), project, filename,file)):
        os.remove(os.path.join(upload_path(), project, filename,file))
        return "File removed", 200
    else:
        raise NotFound()
