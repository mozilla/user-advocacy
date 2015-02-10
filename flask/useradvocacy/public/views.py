# -*- coding: utf-8 -*-
'''Public section, including homepage and signup.'''
from flask import (Blueprint, request, render_template, flash, url_for,
                    redirect, session)
from flask.ext.login import login_user, login_required, logout_user, current_user

from useradvocacy.extensions import login_manager
from useradvocacy.user.models import User
from useradvocacy.public.forms import LoginForm
from useradvocacy.user.forms import RegisterForm
from useradvocacy.utils import flash_errors
from useradvocacy.database import db

blueprint = Blueprint('public', __name__, static_folder="./static", static_url_path="")

@login_manager.user_loader
def load_user(id):
    return User.get_by_id(int(id))


@blueprint.route("/", methods=["GET"])
def home():
    return render_template("public/home.html")

@blueprint.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    # Handle logging in
    if request.method == 'POST':
        if form.validate_on_submit():
            login_user(form.user)
            flash("You are logged in.", 'success')
            redirect_url = request.args.get("next") or url_for("public.home")
            return redirect(redirect_url)
        else:
            flash_errors(form)
    if (request.referrer or request.args.get("next")):
        next_url = request.args.get("next") or request.referrer
        return render_template('public/login.html', login_form=form, 
            next_url=next_url)
    else:
        return render_template('public/login.html', login_form=form)
        

@blueprint.route('/logout/')
def logout():
    if (current_user and not current_user.is_anonymous()):
        logout_user()
        flash('You are logged out.', 'info')
    else:
        flash('You were not logged in.', 'info')
    return redirect(url_for('public.home'))

@blueprint.route("/register/", methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form, csrf_enabled=False)
    if form.validate_on_submit():
        new_user = User.create(username=form.username.data,
                        email=form.email.data,
                        password=form.password.data,
                        active=True)
        flash("Thank you for registering. You can now log in.", 'success')
        return redirect(url_for('public.home'))
    else:
        flash_errors(form)
    return render_template('public/register.html', form=form)

@blueprint.route("/about/")
def about():
    form = LoginForm(request.form)
    return render_template("public/about.html", form=form)
