from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher')], validators=[DataRequired()])
    submit = SubmitField('Register')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PortfolioForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(max=128)])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Save')

class ProfileEditForm(FlaskForm):
    student_number = StringField('Student Number', validators=[Length(max=20)])
    name = StringField('Name', validators=[Length(max=100)])
    grade = StringField('Grade', validators=[Length(max=10)])
    graduation_year = StringField('Graduation Year', validators=[Length(max=4)])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    submit = SubmitField('Save Changes')

class SearchForm(FlaskForm):
    search_query = StringField('Search Student', validators=[DataRequired()])
    submit = SubmitField('Search')