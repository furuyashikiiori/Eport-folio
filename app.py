from flask import Flask, render_template, redirect, url_for, session, request, flash
from forms import RegistrationForm, LoginForm, PortfolioForm, ProfileEditForm
from models import User, Portfolio
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
DATABASE = 'eportfolio.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            student_number TEXT,
            name TEXT,
            grade TEXT,
            graduation_year TEXT,
            bio TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id)
        )
    ''')
    conn.commit()
    conn.close()

# アプリ初回実行時にテーブルを作成
create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data
        role = form.role.data
        hash_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO user (username, password, role) VALUES (?, ?, ?)",
                       (username, hash_password, role))
        conn.commit()
        conn.close()

        flash('Registration successful!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        password = form.password.data

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE username = ?", (username,))
        user_row = cursor.fetchone()
        conn.close()

        if user_row and check_password_hash(user_row['password'], password):
            user = User(user_row['id'], user_row['username'], user_row['password'], user_row['role'])
            session['user_id'] = user.id
            session['role'] = user.role
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and/or password.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))

@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio():
    if 'user_id' not in session:
        flash('You need to be logged in to view this page.', 'danger')
        return redirect(url_for('login'))
    form = PortfolioForm()
    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO portfolio (user_id, title, content) VALUES (?, ?, ?)",
                       (session['user_id'], title, content))
        conn.commit()
        conn.close()

        flash('Portfolio entry added!', 'success')
        return redirect(url_for('portfolio'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio WHERE user_id = ?", (session['user_id'],))
    portfolio_rows = cursor.fetchall()
    conn.close()

    portfolios = [Portfolio(row['id'], row['user_id'], row['title'], row['content'], row['created_at'])
                  for row in portfolio_rows]

    return render_template('portfolio.html', form=form, portfolios=portfolios)

@app.route('/portfolio/<int:portfolio_id>')
def show_portfolio(portfolio_id):
    if 'user_id' not in session:
        flash('You need to be logged in to view this page.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio WHERE id = ?", (portfolio_id,))
    portfolio_row = cursor.fetchone()
    conn.close()

    if portfolio_row:
        portfolio = Portfolio(portfolio_row['id'], portfolio_row['user_id'], portfolio_row['title'], portfolio_row['content'], portfolio_row['created_at'])
        return render_template('portfolio_detail.html', portfolio=portfolio)
    else:
        flash('Portfolio not found.', 'danger')
        return redirect(url_for('portfolio'))

@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('You need to be logged in to view this page.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    user_row = cursor.fetchone()
    conn.close()

    if user_row:
        user_dict = dict(user_row)
        user = User(
            user_dict['id'], user_dict['username'], user_dict['password'], user_dict['role'],
            user_dict.get('student_number', ''), user_dict.get('name', ''), user_dict.get('grade', ''),
            user_dict.get('graduation_year', ''), user_dict.get('bio', '')
        )
        return render_template('profile.html', user=user)
    else:
        flash('User not found.', 'danger')
        return redirect(url_for('index'))

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        flash('You need to be logged in to view this page.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (session['user_id'],))
    user_row = cursor.fetchone()

    form = ProfileEditForm()

    if request.method == 'POST' and form.validate_on_submit():
        student_number = form.student_number.data
        name = form.name.data
        grade = form.grade.data
        graduation_year = form.graduation_year.data
        bio = form.bio.data

        cursor.execute('''
            UPDATE user
            SET student_number = ?, name = ?, grade = ?, graduation_year = ?, bio = ?
            WHERE id = ?
        ''', (student_number, name, grade, graduation_year, bio, session['user_id']))
        conn.commit()
        conn.close()

        flash('Profile updated successfully', 'success')
        return redirect(url_for('profile'))

    if user_row:
        user_dict = dict(user_row)
        user = User(user_dict['id'], user_dict['username'], user_dict['password'], user_dict['role'],
                     user_dict.get('student_number', ''), user_dict.get('name', ''), user_dict.get('grade', ''),
                     user_dict.get('graduation_year', ''), user_dict.get('bio', ''))
        form.student_number.data = user.student_number
        form.name.data = user.name
        form.grade.data = user.grade
        form.graduation_year.data = user.graduation_year
        form.bio.data = user.bio
        conn.close()
        return render_template('edit_profile.html', form=form, user=user)
    else:
        conn.close()
        flash('User not found.', 'danger')
        return redirect(url_for('profile'))

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1')  # ポートオプションもデフォルトの5000を使用