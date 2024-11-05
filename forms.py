from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField
from wtforms.validators import DataRequired, Length

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    role = SelectField('Role', choices=[('student', 'Student'), ('teacher', 'Teacher')], validators=[DataRequired()])
    submit = SubmitField('登録')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('ログイン!')

class PortfolioForm(FlaskForm):
    title = StringField('タイトル', validators=[DataRequired(), Length(max=128)])
    content = TextAreaField('概要', validators=[DataRequired()])
    submit = SubmitField('保存')

class ProfileEditForm(FlaskForm):
    student_number = StringField('学籍番号', validators=[Length(max=20)])
    name = StringField('Name', validators=[Length(max=100)])
    grade = StringField('Grade', validators=[Length(max=10)])
    graduation_year = StringField('Graduation Year', validators=[Length(max=4)])
    bio = TextAreaField('Bio', validators=[Length(max=500)])
    submit = SubmitField('Save Changes')

class SearchForm(FlaskForm):
    search_query = StringField('username', validators=[DataRequired()])
    submit = SubmitField('検索')

class CommentForm(FlaskForm):
    comment = TextAreaField('コメント', validators=[DataRequired()])
    rating = SelectField('評価', choices=[('★☆☆☆☆', '1'), ('★★☆☆☆', '2'), ('★★★☆☆', '3'), ('★★★★☆', '4'), ('★★★★★', '5')], validators=[DataRequired()])
    submit = SubmitField('送信')