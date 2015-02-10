# -*- coding: utf-8 -*-
import datetime as dt
from useradvocacy.user.models import User
from flask import current_app
from sqlalchemy import text

from useradvocacy.database import (
    Column,
    db,
    Model,
    ReferenceCol,
    relationship,
    SurrogatePK,
)

from .markdown2html import convert_md, get_md_meta

def make_filename(context):
    return context.current_parameters['name'] + '.html'

class Template(SurrogatePK, Model):
    __tablename__ = 'templates'
    name = Column(db.String(length=200), unique=True, nullable=False)
    filename = Column(db.String(length=200), unique=False, nullable=False)
    created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    md_content = Column(db.Text(), unique=False, nullable=False)

    def __init__(self, name, **kwargs):
        db.Model.__init__(self, name=name, **kwargs)

    def __repr__(self):
        return '<Template ({name})>'.format(name=self.name)
        
    def __str__(self):
        return self.name;

class Report(SurrogatePK, Model):

    __tablename__ = 'reports'
    project = Column(db.String(length=200), nullable=False)
    filename = Column(db.String(length=200), nullable=False)
    title = Column(db.String(length=1000), nullable=True)
    md_content = Column(db.Text(), unique=False, nullable=False)
    html_content = Column(db.Text(), unique=False, nullable=False)
    author_id = ReferenceCol('users')
    author = db.relationship('User', backref='users', lazy='joined')
    listed = Column(db.Boolean(), nullable=False, default=True)
    published = Column(db.Boolean(), nullable=False, default=False)
    created = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow)
    updated = Column(db.DateTime, nullable=False, default=dt.datetime.utcnow, onupdate=dt.datetime.utcnow)
    template_id = ReferenceCol('templates')
    template = db.relationship('Template', backref='reports', lazy='joined')
    
    def __init__(self, filename, project, md_content, template_id=1, **kwargs):
        db.Model.__init__(self, filename=filename, project=project, template_id=template_id, md_content = md_content, html_content="blank",  **kwargs)
        
            
    def __repr__(self):
        return '<Report({project!s}/{filename!s})>'.format(project=self.project, filename=self.filename)
    
    def save_render_html(self):
        print 'Rendering ({project!s}/{filename!s})'.format(project=self.project, filename=self.filename)
        env = current_app.create_jinja_environment()
        template_file = env.get_template(self.template.filename)
        if self.published:
            html = convert_md(self.md_content, template_file)
        else:
            warn_msg = "This file not published and only visible to UA team."
            html = convert_md(self.md_content, template_file, warning=warn_msg)
        meta = get_md_meta(self.md_content)
        title_known = ''
        if (not "title" in meta or meta["title"] == ''):
            title_known = self.project + "/" + self.filename
        else:
            title_known = meta["title"]
        self.update(html_content = html)
        self.update(title = title_known)
        self.save()
        return
    
    def __str__(self):
        return '{project!s}/{filename!s}'.format(project=self.project, filename=self.filename)
        
    @property
    def shown(self):
        return (self.listed and self.published)

