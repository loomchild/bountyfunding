from flask.ext.wtf import Form
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import ValidationError, Required, Email, Length, Regexp, EqualTo

from bountyfunding.core.models import Account


class LoginForm(Form):
    email = StringField('Email', validators=[Required(), Email()])
    password = PasswordField('Password', validators=[Required()])
    submit = SubmitField('Log In')


class RegisterForm(Form):
    email = StringField('Email', validators=[Required(), Email()])
    password = PasswordField('Password', validators=[Required(), Length(6)])
    password2 = PasswordField('Repeat password', validators=[Required(), EqualTo("password", message="Passwords must match")])
    name = StringField('Name', validators=[Required(), Length(1, 64), Regexp(r'^[A-Za-z0-9_\- ]+$', 0, 'Name must have only letters, numbers, spaces, dots, dashes or underscores')])
    submit = SubmitField('Register')

    def validate_email(self, field):
        if Account.query.filter_by(email=field.data).first():
            raise ValidationError("Email already registered")

