from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, PasswordField
from wtforms.validators import DataRequired, Email


class RegisterForm(FlaskForm):
    firstName = StringField(label='First Name', validators=[DataRequired()])
    lastName = StringField(label='last Name', validators=[DataRequired()])
    email = StringField(label='Email', validators=[DataRequired(), Email()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    repeatPassword = PasswordField(label=' Re-enter Password', validators=[DataRequired()])
    submit = SubmitField(label='Register')

