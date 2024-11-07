from flask import Flask, render_template, redirect, url_for, session, request, flash
from forms import RegistrationForm, LoginForm, PortfolioForm, ProfileEditForm, SearchForm, CommentForm
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            portfolio_id INTEGER,
            teacher_id INTEGER,
            comment TEXT,
            rating INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
            FOREIGN KEY (teacher_id) REFERENCES user (id)
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    ''')

    # ポートフォリオとタグの関係を保存するテーブル
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS portfolio_tags (
            portfolio_id INTEGER,
            tag_id INTEGER,
            FOREIGN KEY (portfolio_id) REFERENCES portfolio (id),
            FOREIGN KEY (tag_id) REFERENCES tags (id),
            PRIMARY KEY (portfolio_id, tag_id)
        )
    ''')
    conn.commit()
    conn.close()

# アプリ初回実行時にテーブルを作成
create_tables()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST']) # ユーザー登録
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

@app.route('/login', methods=['GET', 'POST']) # ログイン
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

            if user.role == 'teacher':
                return redirect(url_for('teacher_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            flash('Login failed. Check your username and/or password.', 'danger')

    return render_template('login.html', form=form)

@app.route('/logout') # ログアウト
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('index'))


@app.route('/portfolio', methods=['GET', 'POST'])
def portfolio():
    if 'user_id' not in session:
        flash('You need to be logged in to view this page.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # フォームにタグの選択肢を追加
    form = PortfolioForm()
    form.tags.choices = [(tag['id'], tag['name']) for tag in cursor.execute("SELECT * FROM tags").fetchall()]

    if form.validate_on_submit():
        title = form.title.data
        content = form.content.data

        # ポートフォリオの作成
        cursor.execute("INSERT INTO portfolio (user_id, title, content) VALUES (?, ?, ?)",
                       (session['user_id'], title, content))
        portfolio_id = cursor.lastrowid

        # 選択されたタグを保存
        for tag_id in form.tags.data:
            cursor.execute("INSERT INTO portfolio_tags (portfolio_id, tag_id) VALUES (?, ?)",
                           (portfolio_id, tag_id))

        conn.commit()
        conn.close()

        flash('Portfolio entry added!', 'success')
        return redirect(url_for('portfolio'))

    cursor.execute("SELECT * FROM portfolio WHERE user_id = ?", (session['user_id'],))
    portfolio_rows = cursor.fetchall()
    conn.close()

    portfolios = [Portfolio(row['id'], row['user_id'], row['title'], row['content'], row['created_at']) 
                  for row in portfolio_rows]

    return render_template('portfolio.html', form=form, portfolios=portfolios)

@app.route('/profile') # プロフィール
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

@app.route('/edit_profile', methods=['GET', 'POST']) # プロフィール編集
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
    
@app.route('/teacher_dashboard', methods=['GET', 'POST']) # 教師ダッシュボード
def teacher_dashboard():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash('You need to be logged in as a teacher to view this page.', 'danger')
        return redirect(url_for('login'))

    form = SearchForm()
    students = []
    
    if form.validate_on_submit():
        search_query = form.search_query.data
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM user WHERE role = 'student' AND username LIKE ?", ('%' + search_query + '%',))
        students = cursor.fetchall()
        conn.close()

    return render_template('teacher_dashboard.html', form=form, students=students)


@app.route('/students_list') # 生徒一覧
def students_list():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash('You need to be logged in as a teacher to view this page.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE role = 'student'")
    students = cursor.fetchall()
    conn.close()

    return render_template('students_list.html', students=students)

@app.route('/view_portfolio/<int:student_id>') # ポートフォリオ一覧
def view_portfolio(student_id):
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash('You need to be logged in as a teacher to view this page.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM user WHERE id = ?", (student_id,))
    student = cursor.fetchone()

    if not student:
        flash('Student not found.', 'danger')
        return redirect(url_for('teacher_dashboard'))

    cursor.execute("SELECT * FROM portfolio WHERE user_id = ?", (student_id,))
    portfolio_rows = cursor.fetchall()
    conn.close()

    portfolios = [Portfolio(row['id'], row['user_id'], row['title'], row['content'], row['created_at'])
                  for row in portfolio_rows]

    return render_template('view_portfolio.html', student=student, portfolios=portfolios)

@app.route('/portfolio/<int:portfolio_id>', methods=['GET', 'POST']) # ポートフォリオ詳細
def show_portfolio_with_comment(portfolio_id):
    if 'user_id' not in session:
        flash('You need to be logged in to view this page.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio WHERE id = ?", (portfolio_id,))
    portfolio_row = cursor.fetchone()
    
    if not portfolio_row:
        flash('Portfolio not found.', 'danger')
        conn.close()
        return redirect(url_for('portfolio'))
        
    portfolio = Portfolio(portfolio_row['id'], portfolio_row['user_id'], portfolio_row['title'], portfolio_row['content'], portfolio_row['created_at'])
    
    cursor.execute('''
        SELECT tags.name
        FROM tags
        JOIN portfolio_tags ON tags.id = portfolio_tags.tag_id
        WHERE portfolio_tags.portfolio_id = ?
    ''', (portfolio_id,))
    tags = cursor.fetchall()

    cursor.execute("SELECT * FROM comments WHERE portfolio_id = ?", (portfolio_id,))
    comments = cursor.fetchall()
    
    form = CommentForm()
    if form.validate_on_submit():
        comment_text = form.comment.data
        rating = form.rating.data
        cursor.execute("INSERT INTO comments (portfolio_id, teacher_id, comment, rating) VALUES (?, ?, ?, ?)",
                       (portfolio_id, session['user_id'], comment_text, rating))
        conn.commit()
        flash('Comment added!', 'success')
        return redirect(url_for('show_portfolio_with_comment', portfolio_id=portfolio_id))
    
    conn.close()

    if session.get('role') == 'teacher':
        template = 'teacher_portfolio_detail.html'
    else:
        template = 'portfolio_detail.html'

    return render_template(template, portfolio=portfolio, comments=comments, tags=tags, form=form)

@app.route('/portfolio/<int:portfolio_id>/edit', methods=['GET', 'POST']) # ポートフォリオ編集
def edit_portfolio(portfolio_id):
    if 'user_id' not in session:
        flash('You need to be logged in to edit a portfolio.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio WHERE id = ? AND user_id = ?", (portfolio_id, session['user_id']))
    portfolio_row = cursor.fetchone()
    
    if not portfolio_row:
        flash('Portfolio not found or you do not have permission to edit.', 'danger')
        conn.close()
        return redirect(url_for('portfolio'))

    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        cursor.execute("UPDATE portfolio SET title = ?, content = ? WHERE id = ?", (title, content, portfolio_id))
        conn.commit()
        conn.close()
        flash('Portfolio has been updated!', 'success')
        return redirect(url_for('show_portfolio_with_comment', portfolio_id=portfolio_id))
    
    conn.close()
    return render_template('edit_portfolio.html', portfolio=portfolio_row)

@app.route('/portfolio/<int:portfolio_id>/delete') # ポートフォリオ削除
def delete_portfolio(portfolio_id):
    if 'user_id' not in session:
        flash('You need to be logged in to delete a portfolio.', 'danger')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM portfolio WHERE id = ? AND user_id = ?", (portfolio_id, session['user_id']))
    portfolio_row = cursor.fetchone()
    
    if not portfolio_row:
        flash('Portfolio not found or you do not have permission to delete.', 'danger')
        conn.close()
        return redirect(url_for('portfolio'))

    cursor.execute("DELETE FROM portfolio WHERE id = ?", (portfolio_id,))
    conn.commit()
    conn.close()
    flash('Portfolio has been deleted!', 'success')
    return redirect(url_for('portfolio'))

# タグを管理するルート（教師専用）
@app.route('/tags', methods=['GET', 'POST'])
def manage_tags():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash('You need to be logged in as a teacher to manage tags.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        tag_name = request.form['tag_name']
        cursor.execute("INSERT INTO tags (name) VALUES (?)", (tag_name,))
        conn.commit()
        flash('Tag added!', 'success')
    
    cursor.execute("SELECT * FROM tags")
    tags = cursor.fetchall()
    conn.close()

    return render_template('manage_tags.html', tags=tags)

# ポートフォリオにタグを追加するルート（生徒専用）
@app.route('/portfolio/<int:portfolio_id>/tags', methods=['GET', 'POST'])
def add_tags_to_portfolio(portfolio_id):
    if 'user_id' not in session or session.get('role') != 'student':
        flash('You need to be logged in as a student to add tags.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        selected_tags = request.form.getlist('tag_ids')
        cursor.execute("DELETE FROM portfolio_tags WHERE portfolio_id = ?", (portfolio_id,))
        for tag_id in selected_tags:
            cursor.execute("INSERT INTO portfolio_tags (portfolio_id, tag_id) VALUES (?, ?)", (portfolio_id, tag_id))
        conn.commit()
        flash('Tags updated!', 'success')
    
    cursor.execute("SELECT * FROM tags")
    tags = cursor.fetchall()
    
    cursor.execute("SELECT tag_id FROM portfolio_tags WHERE portfolio_id = ?", (portfolio_id,))
    portfolio_tags = [tag['tag_id'] for tag in cursor.fetchall()]
    conn.close()

    return render_template('add_tags_to_portfolio.html', tags=tags, portfolio_tags=portfolio_tags)

# タグによる検索のルート（教師専用）
@app.route('/search_by_tag', methods=['GET', 'POST'])
def search_by_tag():
    if 'user_id' not in session or session.get('role') != 'teacher':
        flash('You need to be logged in as a teacher to search by tags.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    if request.method == 'POST':
        selected_tag_id = request.form['tag_id']
        cursor.execute('''
            SELECT portfolio.* FROM portfolio
            INNER JOIN portfolio_tags ON portfolio.id = portfolio_tags.portfolio_id
            WHERE portfolio_tags.tag_id = ?
        ''', (selected_tag_id,))
        portfolios = cursor.fetchall()
    else:
        portfolios = []
    
    cursor.execute("SELECT * FROM tags")
    tags = cursor.fetchall()
    conn.close()
    
    return render_template('search_by_tag.html', portfolios=portfolios, tags=tags)

@app.route('/view_portfolio_by_tag/<int:portfolio_id>', methods=['GET', 'POST'])
def view_portfolio_by_tag(portfolio_id):
    if 'user_id' not in session:
        flash('You need to be logged in to view this page.', 'danger')
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM portfolio WHERE id = ?", (portfolio_id,))
    portfolio_row = cursor.fetchone()
    
    if not portfolio_row:
        flash('Portfolio not found.', 'danger')
        conn.close()
        return redirect(url_for('search_by_tag'))
        
    portfolio = {
        'id': portfolio_row['id'],
        'user_id': portfolio_row['user_id'],
        'title': portfolio_row['title'],
        'content': portfolio_row['content'],
        'created_at': portfolio_row['created_at']
    }

    cursor.execute('''
        SELECT tags.name
        FROM tags
        JOIN portfolio_tags ON tags.id = portfolio_tags.tag_id
        WHERE portfolio_tags.portfolio_id = ?
    ''', (portfolio_id,))
    tags = cursor.fetchall()

    print(tags)  # デバッグ出力

    cursor.execute("SELECT * FROM comments WHERE portfolio_id = ?", (portfolio_id,))
    comments = cursor.fetchall()
    
    form = CommentForm()
    if form.validate_on_submit():
        comment_text = form.comment.data
        rating = form.rating.data
        cursor.execute(
            "INSERT INTO comments (portfolio_id, teacher_id, comment, rating) VALUES (?, ?, ?, ?)",
            (portfolio_id, session['user_id'], comment_text, rating)
        )
        conn.commit()
        flash('Comment added!', 'success')
        return redirect(url_for('view_portfolio_by_tag', portfolio_id=portfolio_id))
    
    conn.close()

    if session.get('role') == 'teacher':
        template = 'teacher_portfolio_detail.html'
    else:
        template = 'portfolio_detail.html'

    return render_template(template, portfolio=portfolio, comments=comments, form=form, tags=tags)

# if __name__ == '__main__':
#     app.run(debug=True, host='127.0.0.1')  # ポートオプション-デフォルトの5000を使用

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5003)  # ここでポート番号を変更