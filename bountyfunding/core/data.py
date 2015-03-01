#This is future data access layer

from bountyfunding.core.const import *
from bountyfunding.core.models import db, Project, Issue, User, Sponsorship, Email, Payment, Change, Token
from bountyfunding.core.config import config
from bountyfunding.core.errors import Error

import re, requests, threading, random, string 
from flask import current_app


#TODO: move to config, 0 means no notifications, set for tests, automatically when in-memory-database in config
NOTIFY_INTERVAL = 5

#TODO: generic update and delete methods, use constructors to create

#TODO: move trivial queries back to the views, trivial creates too

#TODO: replace mapify with iter https://stackoverflow.com/questions/23252370/overloading-dict-on-python-class

def create_database():
    db.drop_all()
    db.create_all()

def retrieve_user(project_id, name):
    user = User.query.filter_by(project_id=project_id, name=name).first()
    return user

def create_project(name, description):
    project = Project(name, description, ProjectType.NORMAL)
    db.session.add(project)

    token = Token(project.project_id, generate_token())
    db.session.add(token)

    db.session.commit()
    return project, token

def retrieve_project(token):
    return Project.query.join(Token).filter_by(token=token).scalar()

def update_project(project):
    db.session.add(project)
    db.session.commit()

def mapify_project(project):
    type = ProjectType.to_string(project.type)
    return dict(name=project.name, description=project.description, type=type)

def generate_token():
    return ''.join(random.choice(string.ascii_lowercase) for _ in xrange(32))


def retrieve_issues(project_id):
    issues = Issue.query.filter_by(project_id=project_id).all()
    return issues

def retrieve_issue(project_id, issue_ref):
    issue = Issue.query.filter_by(project_id=project_id, issue_ref=issue_ref).first()
    return issue

def create_issue(project_id, ref, status, title, link, owner_id):
    issue = Issue(project_id, ref, status, title, link, owner_id)
    db.session.add(issue)
    db.session.commit()
    return issue

def update_issue(issue):
    db.session.add(issue)
    db.session.commit()

def mapify_issue(issue):
    result = dict(ref=issue.issue_ref, title=issue.title)	

    result['status'] = IssueStatus.to_string(issue.status)
    result['link'] = issue.full_link

    if issue.owner != None:
        result['owner'] = issue.owner.name

    return result

def retrieve_sponsored_issues(project_id):
    issues = db.engine.execute("""
        SELECT i.issue_ref, i.status, i.title, i.link, sum(s.amount) AS amount
        FROM issue AS i JOIN sponsorship AS s ON (i.issue_id = s.issue_id) 
        WHERE i.project_id = :1
        GROUP BY i.issue_id
        HAVING amount > 0
        ORDER BY amount DESC
    """, [project_id]).fetchall()

    issues = {'data': map(lambda i: {
        'ref': i[0],
        'status': IssueStatus.to_string(i[1]),
        'title': i[2],
        'link': config[project_id].TRACKER_URL + i[3],
        'amount': i[4]
    }, issues)}
    
    return issues


def retrieve_create_user(project_id, name):
    user = retrieve_user(project_id, name)
    if user == None:
        user = User(project_id=project_id, name=name)
        db.session.add(user)
        db.session.commit()
    return user

def update_user(user):
    db.session.add(user)
    db.session.commit()

def mapify_user(user):
    result = dict(name=user.name, paypal_email=user.paypal_email)

    # Remove empty values
    result = {k: v for k, v in result.items() if v != None}

    return result

def create_sponsorship(project_id, issue_id, user_id, amount):
    sponsorship = Sponsorship(project_id, issue_id, user_id, amount)
    db.session.add(sponsorship)
    db.session.commit()
    return sponsorship.sponsorship_id

def retrieve_sponsorship(issue_id, user_id):
    sponsorship = Sponsorship.query.filter_by(issue_id=issue_id, user_id=user_id).first()
    return sponsorship

def retrieve_all_sponsorships(issue_id):
    sponsorships = Sponsorship.query.filter_by(issue_id=issue_id).all()
    return sponsorships

def update_sponsorship(sponsorship):
    db.session.add(sponsorship)
    db.session.commit()

def remove_sponsorship(issue_id, user_id):
    sponsorship = retrieve_sponsorship(issue_id, user_id)
    Payment.query.filter_by(sponsorship_id=sponsorship.sponsorship_id).delete()
    db.session.delete(sponsorship)
    db.session.commit()
    

def retrieve_last_payment(sponsorship_id):
    payment = Payment.query.filter_by(sponsorship_id=sponsorship_id) \
            .order_by(Payment.payment_id.desc()).first()
    return payment

def update_payment(payment):
    db.session.add(payment)
    db.session.commit()

def create_change(project_id, method, path, arguments):
    change = Change(project_id, method, path, arguments)
    db.session.add(change)
    db.session.commit()
    return change.change_id

def update_change(change_id, status, response):
    change = Change.query.get(change_id)
    if change == None:
        current_app.logger.warn('Change %s not found', change_id)
        return
    change.status = status
    change.response = response
    db.session.add(change)
    db.session.commit()

def notify_sponsors(project_id, issue_id, status, body):
    sponsorships = Sponsorship.query.filter_by(issue_id=issue_id, status=status)
    for sponsorship in sponsorships:
        create_email(project_id, sponsorship.user.user_id, issue_id, body)

def create_email(project_id, user_id, issue_id, body):
    email = Email(project_id, user_id, issue_id, body)
    db.session.add(email)
    db.session.commit()

def retrieve_all_emails():
    return Email.query.all()

def retrieve_email(email_id):
    email = Email.query.get(email_id)
    return email

def remove_email(email):
    db.session.delete(email)
    db.session.commit()

def check_pledge_amount(project_id, amount):
    if amount <= 0:
        raise Error("Amount must be positive")
    max_pledge_amount = config[project_id].MAX_PLEDGE_AMOUNT
    if amount > max_pledge_amount:
        raise Error("Amount may be up to %d" % max_pledge_amount)

def send_emails():
    emails = Email.query.all()
    if len(emails) > 0:
        project_ids = set(map(lambda email: email.project_id, emails))
        for project_id in project_ids:
            notify_url = config[project_id].TRACKER_URL + '/bountyfunding/email'
            try:
                requests.get(notify_url, timeout=1)
            except requests.exceptions.RequestException:
                current_app.logger.warn('Unable to connect to issue tracker at ' + notify_url)

def notify():
    send_emails()
    t = threading.Timer(NOTIFY_INTERVAL, notify)
    t.daemon = True
    t.start()

