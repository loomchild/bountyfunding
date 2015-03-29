from bountyfunding.gui import gui
from bountyfunding.gui.forms import LoginForm, RegisterForm
from bountyfunding.core.models import db, Account, Project, Issue
from bountyfunding.core.data import retrieve_all_sponsorships

from flask import redirect, render_template, request, url_for, flash, abort
from flask.ext.login import LoginManager, login_required, login_user, logout_user, current_user as current_account
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
def load_user(account_id):
    return Account.query.get(int(account_id))

@gui.context_processor
def utility_processor():
    return dict(current_account=current_account)

@gui.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@gui.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        account = Account.query.filter_by(email=form.email.data).first()
        if account is not None and account.verify_password(form.password.data):
            login_user(account)
            next = request.values.get('next')
            return redirect(next or "/")
        flash('Invalid username or password.')
    return render_template('login.html', form=form)

@gui.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect("/")

@gui.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        account = Account(form.email.data, form.name.data, form.password.data)
        db.session.add(account)
        db.session.commit()
        flash('Account has been registered, please log in.')
        return redirect(url_for(".login"))
    return render_template('register.html', form=form)

@gui.route("/projects/<project_name>/issues/<issue_ref>.html", methods=['GET'])
@login_required
def issue(project_name, issue_ref):
    project = Project.query.filter_by(name=project_name).first()
    issue = Issue.query.filter_by(issue_ref=issue_ref).first()
    if project == None or issue == None:
        abort(404)
    
    sponsorships = retrieve_all_sponsorships(issue.issue_id)
    bounty = sum(s.amount for s in sponsorships)
    sponsorship_map = {s.user.name: s for s in sponsorships} 
    
    user = current_account.get_user(project.project_id)
    if user != None and user.name in sponsorship_map:
        user_bounty = sponsorship_map[user.name].amount
    else:
        user_bounty = 0

    return render_template('issue.html', project=project.name, 
        id=issue.issue_ref, title=issue.title, url=issue.full_link, 
        bounty=bounty, user_bounty=user_bounty)


