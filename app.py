from flask import Flask, render_template, redirect, url_for, session, request, flash
from forms import RegistrationForm, LoginForm, PortfolioForm
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
            role TEXT NOT NULL
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

if __name__ == '__main__':
    app.run(debug=True)