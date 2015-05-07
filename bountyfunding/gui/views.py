from bountyfunding.gui import gui
from bountyfunding.gui.forms import LoginForm, RegisterForm, IssueForm
from bountyfunding.core.models import db, Account, Project, Issue, Sponsorship
from bountyfunding.core.data import retrieve_all_sponsorships, create_update_sponsorship
from bountyfunding.core.const import IssueStatus, ProjectType
from bountyfunding.core.trackers.github import create_update_issue

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

@gui.route("/projects/<project_name>/issues/<issue_ref>.html", methods=['GET', 'POST'])
@login_required
def issue(project_name, issue_ref):
    project = Project.query.filter_by(name=project_name).first()
    issue = Issue.query.filter_by(issue_ref=issue_ref).first()
    
    if project == None:
        abort(404)
    
    if issue == None:
        if project.type == ProjectType.GITHUB:
            issue = create_update_issue(project.project_id, issue_ref)
    
    if issue == None:
        abort(404)

    sponsorships = retrieve_all_sponsorships(issue.issue_id)
    bounty = sum(s.amount for s in sponsorships)
    sponsorship_map = {s.account.account_id: s for s in sponsorships if s.account} 
    
    my_sponsorship = sponsorship_map.get(current_account.account_id)
    my_bounty = my_sponsorship.amount if my_sponsorship else 0

    form = IssueForm()
    if form.validate_on_submit():
        amount = form.amount.data
        create_update_sponsorship(project.project_id, issue.issue_id,
                    account_id=current_account.account_id, amount=amount)
        if amount == 0 and my_bounty > 0:
            flash('Sponsorship deleted.')
        elif amount != my_bounty:
            flash('Sponsorship updated.')
        return redirect(url_for(".issue", project_name=project_name, issue_ref=issue_ref))
    return render_template('issue.html', form=form, 
        project_name=project.name, issue_ref=issue_ref, 
        title=issue.title, url=issue.full_link, status=IssueStatus.to_string(issue.status), 
        bounty=bounty, my_bounty=my_bounty)


