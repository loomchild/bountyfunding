from bountyfunding.api import api

from bountyfunding.api.data import *
from bountyfunding.api.const import *

from bountyfunding.api.payment.factory import payment_factory
from bountyfunding.api.errors import APIException

from bountyfunding.api import security
from bountyfunding.api.config import config

from flask import Flask, url_for, render_template, make_response, redirect, abort, jsonify, request, g, current_app


@api.route('/version', methods=['GET'])
def status():
    return jsonify(version=config.VERSION)

@api.route("/issues", methods=['GET'])
def get_issues():
    issues = retrieve_issues(g.project_id)
    issues = {'data': map(mapify_issue, issues)}
    response = jsonify(issues)
    return response

@api.route("/issues", methods=['POST'])
def post_issue():
    ref = request.values.get('ref')
    status = IssueStatus.from_string(request.values.get('status'))
    title = request.values.get('title')
    link = request.values.get('link')
    owner_name = request.values.get('owner')

    if ref == None or status == None or title == None or link == None:
        return jsonify(error="ref, status, title and link parameters are required"), 400
    
    if not link.startswith('/'):
        return jsonify(error="Link must be relative to the issue tracker URL and start with /"), 400

    owner_id = None
    if owner_name != None:
        owner = retrieve_create_user(g.project_id, owner_name)
        owner_id = owner.user_id

    issue = retrieve_issue(g.project_id, ref)

    if issue != None:        
        return jsonify(error="Issue already exists"), 409
    
    issue = create_issue(g.project_id, ref, status, title, link, owner_id)

    return jsonify(message='OK')

@api.route("/issue/<issue_ref>", methods=['GET'])
def get_issue(issue_ref):
    issue = retrieve_issue(g.project_id, issue_ref)

    if issue == None:
        return jsonify(error='Issue not found'), 404

    return jsonify(mapify_issue(issue))

@api.route("/issue/<issue_ref>", methods=['PUT'])
def put_issue(issue_ref):
    # Does not allow to create new issue despite it could because we know the ID. 
    # This is done for simplicity and to provide only one way of doing one thing.
    status = IssueStatus.from_string(request.values.get('status'))
    title = request.values.get('title')
    link = request.values.get('link')
    owner_name = request.values.get('owner')

    # TODO: in addition could be more clever actually report if issue has been updated or not
    if status == None and title == None and link == None and owner_name == None:
        return jsonify(error="At least one parameter is required when updating an issue"), 400

    if link != None and not link.startswith('/'):
        return jsonify(error="Link must be relative to the issue tracker URL and start with /"), 400

    owner = None
    if owner_name != None:
        owner = retrieve_create_user(g.project_id, owner_name)

    issue = retrieve_issue(g.project_id, issue_ref)

    if issue == None:
        return jsonify(error='Issue not found'), 404
        
    if status != None and status != issue.status:
        issue.status = status
        # Nothing to do for default status
        # TODO: be more clever to avoid sending repeated emails
        if status == IssueStatus.READY:
            pass
        elif status == IssueStatus.STARTED:
            body = 'The task you have sponsored has been started. Please deposit the promised amount. To do that please go to project issue tracker, log in, find this issue and select Confirm.'
            notify_sponsors(g.project_id, issue.issue_id, SponsorshipStatus.PLEDGED, body)
        elif status == IssueStatus.COMPLETED:
            body_confirmed = 'The task you have sponsored has been completed by the developer. Please validate it. To do that please go to project issue tracker, log in, find an issue and select Validate.'
            notify_sponsors(g.project_id, issue.issue_id, SponsorshipStatus.CONFIRMED, body_confirmed)
            body_pledged = 'The task you have sponsored has been completed by the developer. Please deposit the promised amout and validate it. To do that please go to project issue tracker, log in, find an issue and select Confirm and then Validate.'
            notify_sponsors(g.project_id, issue.issue_id, SponsorshipStatus.PLEDGED, body_pledged)
        else:
            return jsonify(error="Unknown status"), 400

    if title != None and title != issue.title:
        issue.title = title

    if link != None and link != issue.link:
        issue.link = link

    if owner != None and owner.user_id != issue.owner_id:
        issue.owner_id = owner.user_id

    update_issue(issue)

    return jsonify(message='OK')

@api.route("/sponsored_issues", methods=['GET'])
def get_sponsored_issues():
    issues = retrieve_sponsored_issues(g.project_id)
    response = jsonify(issues)
    return response

@api.route("/issue/<issue_ref>/sponsorships", methods=['GET'])
def get_sponsorships(issue_ref):
    sponsorships = []
    issue = retrieve_issue(g.project_id, issue_ref)

    if issue != None:
        sponsorships = retrieve_all_sponsorships(issue.issue_id)
        sponsorship_map = {s.user.name: {
                'amount': s.amount, 
                'status': SponsorshipStatus.to_string(s.status)
            } for s in sponsorships} 
        
        response = jsonify(sponsorship_map)
    else:
        response = jsonify(error='Issue not found'), 404
    return response

@api.route("/issue/<issue_ref>/sponsorships", methods=['POST'])
def post_sponsorship(issue_ref):
    user_name = request.values.get('user')
    amount = int(request.values.get('amount'))

    check_pledge_amount(g.project_id, amount)

    issue = retrieve_issue(g.project_id, issue_ref)
    if issue == None:
        return jsonify(error='Issue not found'), 404

    user = retrieve_create_user(g.project_id, user_name)
    
    sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
    if sponsorship != None:
        return jsonify(error="Sponsorship already exists"), 409
    
    sponsorship = create_sponsorship(g.project_id, issue.issue_id, user.user_id, amount)

    response = jsonify(message='Sponsorship updated')
    return response

@api.route("/issue/<issue_ref>/sponsorship/<user_name>", methods=['GET'])
def get_sponsorship(issue_ref, user_name):
    issue = retrieve_issue(g.project_id, issue_ref)
    user = retrieve_user(g.project_id, user_name)

    if issue == None:
        response = jsonify(error='Issue not found'), 404

    elif user == None:
        response = jsonify(error='User not found'), 404

    else:
        sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
        if sponsorship == None:
            response = jsonify(error='Sponsorship not found'), 404
        else:
            status = SponsorshipStatus.to_string(sponsorship.status)
            response = jsonify(status=status)
    
    return response

@api.route("/issue/<issue_ref>/sponsorship/<user_name>", methods=['DELETE'])
def delete_sponsorship(issue_ref, user_name):
    issue = retrieve_issue(g.project_id, issue_ref)
    user = retrieve_user(g.project_id, user_name)

    if issue == None:
        response = jsonify(error='Issue not found'), 404

    elif user == None:
        response = jsonify(error='User not found'), 404

    else:
        sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
        if sponsorship.status != SponsorshipStatus.PLEDGED:
            return jsonify(error='Can only delete sponsorhip in PLEDGED status'), 403

        remove_sponsorship(issue.issue_id, user.user_id)
        response = jsonify(message="Sponsorship deleted")
    
    return response
    
@api.route("/issue/<issue_ref>/sponsorship/<user_name>", methods=['PUT'])
def put_sponsorship(issue_ref, user_name):
    # Does not allow to create new sponsorship despite it could because we know the ID. 
    # This is done for simplicity and to provide only one way of doing one thing.
    status_string = request.values.get('status')
    status = SponsorshipStatus.from_string(status_string) 
    amount_string = request.values.get('amount')

    issue = retrieve_issue(g.project_id, issue_ref)
    if issue == None:
        return jsonify(error='Issue not found'), 404
    
    user = retrieve_create_user(g.project_id, user_name)
    
    sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
    if sponsorship == None:
        return jsonify(error='Sponsorship not found'), 404

    if status == None and amount_string == None:
        return jsonify(error="Nothing to update"), 400

    if status != None:
        if status == SponsorshipStatus.PLEDGED:
            return jsonify(error='Cannot change state to PLEDGED'), 400
        elif status == SponsorshipStatus.CONFIRMED:
            return jsonify(error='Confirm sponsorship by confirming the payment'), 400
        elif status == sponsorship.status:
            return jsonify(error='Status already set'), 403
        elif status == SponsorshipStatus.VALIDATED:
            if (sponsorship.status != SponsorshipStatus.CONFIRMED
                    and sponsorship.status != SponsorshipStatus.REJECTED):
                return jsonify(error='Can only validate confirmed sponsorship'), 403
            admin = retrieve_create_user(g.project_id, config.ADMIN)
            body = 'User %s has validated his/her sponsorship. Please transfer the money to the developer.'% user_name
            create_email(g.project_id, admin.user_id, issue.issue_id, body)
        elif status == SponsorshipStatus.TRANSFERRED:
            if sponsorship.status != SponsorshipStatus.VALIDATED:
                return jsonify(error='Can only transfer when sponsorship is validated'), 403
        elif status == SponsorshipStatus.REJECTED:
            if (sponsorship.status != SponsorshipStatus.CONFIRMED 
                    and sponsorship.status != SponsorshipStatus.VALIDATED):
                return jsonify(error='Can only reject confirmed sponsorship'), 403
            admin = retrieve_create_user(g.project_id, config.ADMIN)
            body = 'User %s has rejected his/her sponsorship. Please refund the money to the user.'% user_name
            create_email(g.project_id, admin.user_id, issue.issue_id, body)
        elif status == SponsorshipStatus.REFUNDED:
            if sponsorship.status != SponsorshipStatus.REJECTED:
                return jsonify(error='Can only refund rejected sponsorship'), 403
        else:
            return jsonify(error='Invalid status: %s' % status_string), 400

        sponsorship.status = status

    if amount_string != None:
        if sponsorship.status != SponsorshipStatus.PLEDGED:
            return jsonify(error='Can only change amount in PLEDGED state'), 403
        try:
            amount = int(amount_string)
        except ValueError:
            return jsonify(error="amount is not a number"), 400
        check_pledge_amount(g.project_id, amount)

        sponsorship.amount = amount

    update_sponsorship(sponsorship)

    return jsonify(message='Sponsorship updated')

@api.route("/issue/<issue_ref>/sponsorship/<user_name>/payment", methods=['GET'])
def get_payment(issue_ref, user_name):
    
    issue = retrieve_issue(g.project_id, issue_ref)
    user = retrieve_user(g.project_id, user_name)
    
    if issue == None:
        response = jsonify(error='Issue not found'), 404

    elif user == None:
        response = jsonify(error='User not found'), 404

    sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)

    payment = retrieve_last_payment(sponsorship.sponsorship_id)

    if payment != None:
        gateway = PaymentGateway.to_string(payment.gateway)
        status = PaymentStatus.to_string(payment.status)
        response = jsonify(gateway=gateway, url=payment.url, status=status)
    else:
        response = jsonify(error='Payment not found'), 404
    
    return response

@api.route("/issue/<issue_ref>/sponsorship/<user_name>/payment", methods=['PUT'])
def put_payment(issue_ref, user_name):
    status = PaymentStatus.from_string(request.values.get('status')) 
    if status != PaymentStatus.CONFIRMED:
        return jsonify(error='You can only change the status to CONFIRMED'), 403
    
    issue = retrieve_issue(g.project_id, issue_ref)
    user = retrieve_user(g.project_id, user_name)
    
    if issue == None:
        response = jsonify(error='Issue not found'), 404

    elif user == None:
        response = jsonify(error='User not found'), 404

    sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)

    payment = retrieve_last_payment(sponsorship.sponsorship_id)

    if payment != None:
        if payment.status == status:
            return jsonify(error='Payment already confirmed'), 403

        payment_gateway = payment_factory.get_payment_gateway(payment.gateway)

        approved = payment_gateway.process_payment(g.project_id, sponsorship, payment, request.values)
        if not approved:
            return jsonify(error='Payment not confirmed by the gateway'), 403
        
        payment.status = status
        update_payment(payment)
 
        sponsorship.status = SponsorshipStatus.CONFIRMED
        update_sponsorship(sponsorship)
        
        response = jsonify(message='Payment updated')
    
    else:
        response = jsonify(error='Payment not found'), 404
    
    return response

@api.route("/issue/<issue_ref>/sponsorship/<user_name>/payments", methods=['POST'])
def create_payment(issue_ref, user_name):
    gateway = PaymentGateway.from_string(request.values.get('gateway')) 
    if gateway not in config.PAYMENT_GATEWAYS:
        return jsonify(error="Payment gateway not accepted"), 400

    return_url = request.values.get('return_url')
    
    issue = retrieve_issue(g.project_id, issue_ref)
    user = retrieve_user(g.project_id, user_name)
    
    if issue == None:
        return jsonify(error='Issue not found'), 404

    if user == None:
        return jsonify(error='User not found'), 404
    
    sponsorship = retrieve_sponsorship(issue.issue_id, user.user_id)
    
    if sponsorship.status != SponsorshipStatus.PLEDGED:
        return jsonify(error="You can only create payment for PLEDGED sponsorship"), 403

    payment_gateway = payment_factory.get_payment_gateway(gateway)
    
    payment = payment_gateway.create_payment(g.project_id, sponsorship, return_url)
    update_payment(payment)
    
    return jsonify(message='Payment created')

@api.route("/user/<user_name>", methods=['GET'])
def get_user(user_name):
    user = retrieve_user(g.project_id, user_name)

    if user == None:
        return jsonify(error='User not found'), 404

    return jsonify(mapify_user(user))

@api.route("/user/<user_name>", methods=['PUT'])
def put_user(user_name):
    paypal_email = request.values.get('paypal_email')
    
    user = retrieve_create_user(g.project_id, user_name)

    if paypal_email == None:
        return jsonify(error='Nothing to update'), 400

    if paypal_email != None:
        if paypal_email != '':
            user.paypal_email = paypal_email
        else:
            user.paypal_email = None

    update_user(user)

    return jsonify(message='User updated')

@api.route('/emails', methods=['GET'])
def get_emails():
    emails = retrieve_all_emails()

    response = []
    for email in emails:
        response.append({'id': email.email_id, 'recipient':email.user.name, 'issue_id':email.issue.issue_ref, 'body':email.body})
        
    response = jsonify(data=response)
    return response 

@api.route('/email/<email_id>', methods=['DELETE'])
def delete_email(email_id):
    email = retrieve_email(email_id)
    if email != None:
        remove_email(email)
        response = jsonify(message='Email deleted')
    else:
        response = jsonify(error='Email not found'), 404
    
    return response


@api.route('/', methods=['GET'])
def get_project():
    return jsonify(mapify_project(g.project))

@api.route('/', methods=['PUT'])
def put_project():
    name = request.values.get('name')
    description = request.values.get('description')

    project = g.project

    if not project.is_mutable():
        return jsonify(error="This project can't be modified"), 400

    if name == None and description == None:
        return jsonify(error="Nothing to modify"), 400

    if name != None:
        project.name = name

    if description != None:
        project.description = description

    update_project(project)

    return jsonify(message='OK')

@api.route('/', methods=['POST'])
def post_project():
    name = request.values.get('name')
    description = request.values.get('description')

    if not (g.project.type == ProjectType.ROOT and request.remote_addr == '127.0.0.1'):
        return jsonify(error="Insufficient permissions to create a project"), 400

    if name == None or description == None:
        return jsonify(error="All parameters are mandatory"), 400

    project, token = create_project(name, description)

    return jsonify(message='OK', token=token.token)

@api.route('/config/payment_gateways', methods=['GET'])
def get_config_payment_gateways():
    gateways = [PaymentGateway.to_string(pg) for pg in config[g.project_id].PAYMENT_GATEWAYS]
    return jsonify(gateways=gateways)


# Order of these two functions is important - first one needs to be executed
# before the second, because I need project_id to log the change
# http://t27668.web-flask-general.webdiscuss.info/priority-for-before-request-t27668.html

@api.before_request
def check_access_and_set_project():
    token = request.values.get('token')
    project = security.get_project(token)
    g.project = project
    g.project_id = project.project_id

@api.before_request
def log_change():
    if request.method == 'POST' or request.method == 'PUT' or request.method == 'DELETE':
        arguments = ", ".join(map(lambda (k, v): '%s:%s' % (k, v),\
                sorted(request.values.iteritems(True))))
        g.change_id = create_change(g.project_id, request.method, request.path, arguments)

@api.after_request
def log_change_result(response):
    # Documentation says that this may not be executed and that data will be removed - investigate
    if 'change_id' in g:
        update_change(g.change_id, response.status_code, response.data)
    return response

@api.before_app_first_request
def init():
    # For in-memory DB need to initialize memory database in the same thread
    if config.DATABASE_CREATE:
        if not config.DATABASE_IN_MEMORY:
            print "Creating database in %s" % config.DATABASE_URL
        create_database()
    
    # Multiple threads do not work with memory database
    if not config.DATABASE_IN_MEMORY:
        notify()


@api.errorhandler(APIException)
def handle_api_exception(exception):
    return jsonify(error=exception.message), exception.status_code

