from bountyfunding.gui import gui
from bountyfunding.gui.forms import LoginForm
from bountyfunding.core.models import User, Project, Issue
from bountyfunding.core.data import retrieve_all_sponsorships

from flask import redirect, render_template, request, url_for, flash
from flask.ext.login import LoginManager, login_required, login_user, logout_user
from flask_bootstrap import Bootstrap


login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = '.login'


@gui.record_once
def record_once(state):
    login_manager.init_app(state.app)
    Bootstrap(state.app)
    state.app.config['BOOTSTRAP_SERVE_LOCAL'] = True

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


@gui.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(name=form.name.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            next = request.values.get('next')
            return redirect(next or "/")
        flash('Invalid username or password.')
    return render_template('login.html', form=form)

@gui.route("/projects/<project_name>/issues/<issue_ref>.html", methods=['GET'])
@login_required
def issue(project_name, issue_ref):
    #TODO: retrieve user from db, but first need to make users project-agnostic
    user_name = 'dev'
    project = Project.query.filter_by(name=project_name).first()
    issue = Issue.query.filter_by(issue_ref=issue_ref).first()
    sponsorships = retrieve_all_sponsorships(issue.issue_id)
    bounty = sum(s.amount for s in sponsorships)
    sponsorship_map = {s.user.name: s for s in sponsorships} 
    user_sponsorship = sponsorship_map.get('dev')
    user_bounty = user_sponsorship.amount if user_sponsorship else 0

    return render_template('issue.html', project=project.name, 
        id=issue.issue_ref, title=issue.title, url=issue.full_link, 
        bounty=bounty, user_bounty=user_bounty)

@gui.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect("/")

@gui.route("/test", methods=['GET'])
@login_required
def test():
    return "Test"


