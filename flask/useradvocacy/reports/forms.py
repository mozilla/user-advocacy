from flask_wtf import Form
from wtforms.fields import *
from wtforms.validators import DataRequired
from wtforms.ext.sqlalchemy.fields import QuerySelectField
import re

from useradvocacy.user.models import User
from useradvocacy.reports.models import Report, Template

import datetime as dt

def available_templates():
    return Template.query.all()
    
def recent_reports():  
    date = dt.datetime.utcnow() - dt.timedelta(days=180)
    reports = Report.query.filter(Report.updated > date).all()
    reports.reverse()
    return reports

class EditorForm(Form):

    project_field = HiddenField()
    filename_field = HiddenField()
    template_field = QuerySelectField('Template', query_factory=available_templates, get_label='name', allow_blank=False)
    markdown_field = TextAreaField('Markdown', validators=[DataRequired()])
    listed_field = BooleanField(label='Listed')
    published_field = BooleanField(label='Published')
    new_project_field = StringField('Project')
    new_filename_field = StringField('Filename')
    save_button = SubmitField('Save')
    saveas_button = SubmitField('Save As')
    

    def __init__(self, *args, **kwargs):
        super(EditorForm, self).__init__(*args, **kwargs)
        self.project = None
        self.filename = None
        self.template = None
        self.md_content = None
        self.savemode = None
        self.old_filename = None
        self.old_project = None
        self.listed = None
        self.published = None


    def validate(self):
        initial_validation = super(EditorForm, self).validate()
        if not initial_validation:
            return False

        self.template = self.template_field.data
        if not self.template:
            self.template_field.errors.append('Unknown template' + self.template.id)
            return False
        
        if self.save_button.data:
            self.project = self.project_field.data
            self.filename = self.filename_field.data
            self.md_content = self.markdown_field.data
            self.listed = self.listed_field.data
            self.published = self.published_field.data
            self.savemode = 'save'
            return True
        
        if self.saveas_button.data:
            if not re.match('[a-zA-Z0-9_-]+$',self.new_project_field.data):
                self.new_project_field.errors.append('Invalid Project Name')
                return False
            if not re.match('[a-zA-Z0-9_-]+$',self.new_filename_field.data):
                self.new_filename_field.errors.append('Invalid Filename')
                return False
            if len(Report.query.filter_by(filename = self.new_filename_field.data, 
                    project = self.new_project_field.data).all()) > 0:
                self.new_filename_field.errors.append('Report already exists: ' + \
                    self.new_project_field.data + "/" + self.new_filename_field.data)
                return False
            self.project = self.new_project_field.data
            self.filename = self.new_filename_field.data
            self.old_project = self.project_field.data
            self.old_filename = self.filename_field.data
            self.md_content = self.markdown_field.data
            self.listed = self.listed_field.data
            self.published = self.published_field.data
            self.savemode = 'saveas'
            return True
        
        self.save_button.errors.append("No Save Button Pressed")
        return False

class SelectorForm(Form):
    project_filename = QuerySelectField('Select existing report', 
        query_factory=recent_reports, allow_blank=True)
    new_project_field = StringField('Project')
    new_filename_field = StringField('Filename')
    go_button = SubmitField('Go')
    rerender_button = SubmitField('Rerender all reports')
    saveas_button = SubmitField('Make new report')

    def __init__(self, *args, **kwargs):
        super(SelectorForm, self).__init__(*args, **kwargs)
        self.project = None
        self.filename = None
        self.action = None

    def validate(self):
        initial_validation = super(SelectorForm, self).validate()
        if not initial_validation:
            return False
        
        if self.rerender_button.data:
            self.action = "rerender"
            return True

        if self.go_button.data:
            if not self.project_filename.data:
                self.project_filename.errors.append('No report selected')
                return False
            self.project = self.project_filename.data.project
            self.filename = self.project_filename.data.filename
            self.action = "report"
            return True
        
        if self.saveas_button.data:
            if not re.match('[a-zA-Z0-9_-]+$',self.new_project_field.data):
                self.new_project_field.errors.append('Invalid Project Name')
                return False
            if not re.match('[a-zA-Z0-9_-]+$',self.new_filename_field.data):
                self.new_filename_field.errors.append('Invalid Filename')
                return False
            if len(Report.query.filter_by(filename = self.new_filename_field.data, 
                    project = self.new_project_field.data).all()) > 0:
                self.new_filename_field.errors.append('Report already exists: ' + \
                    self.new_project_field.data + "/" + self.new_filename_field.data)
                return False
            self.project = self.new_project_field.data
            self.filename = self.new_filename_field.data
            self.action = "report"
            return True
        
        self.save_button.errors.append("No Save Button Pressed")
        return False

class PreviewForm(Form):
    markdown_preview_field = HiddenField()
    template_preview_field = HiddenField()

    def __init__(self, *args, **kwargs):
        super(PreviewForm, self).__init__(*args, **kwargs)
        self.template_id = None
        self.md_content = None
        
    def validate(self):
        self.template_id = self.template_preview_field.data
        self.md_content = self.markdown_preview_field.data
        return True

