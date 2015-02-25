from bountyfunding.gui import gui
from bountyfunding.api.models import User
from bountyfunding.gui.forms import LoginForm
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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

