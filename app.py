import sqlite3
import bcrypt
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import requests as rq
import datetime as dt

app = Flask(__name__)
app.config['SECRET_KEY'] = "webdevelopmentturnedouttobehellahard"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin):
    def __init__(self, username):
        self.id = username

@login_manager.user_loader
def load_user(user_id):
    with sqlite3.connect('users.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM admins WHERE username = ?", (user_id,))
        admin = cursor.fetchone()
        if admin:
            return User(admin[0])
    return None

def initialize_db():

    """Initializes the database to store 
    admins password.
    Mainly useless but why not"""

    admin_username = 'admin'
    admin_password = 'admin123'
    with sqlite3.connect('users.db') as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                username TEXT PRIMARY KEY,
                password BLOB NOT NULL
            );
                     
        ''')

        """password hasing """

        hashed_password = hash_password(admin_password)
        conn.execute('INSERT OR IGNORE INTO admins (username, password) VALUES (?, ?)', 
                     (admin_username, hashed_password))
        conn.commit()

def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(hashed_password, password):
    """Checks if the password is valid"""
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode()
    return bcrypt.checkpw(password.encode(), hashed_password)

initialize_db()

@app.route("/login", methods=["GET", "POST"])
def login():

    next_page = request.args.get('next')
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        with sqlite3.connect('users.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM admins WHERE username = ?", (username,))
            admin = cursor.fetchone()

            if admin and check_password(admin[1], password):
                login_user(User(username))
                flash("Logged in successfully.")
                return redirect(next_page or url_for('home'))
            else:
                flash("Invalid username or password.")
    
    return render_template("base.html", logged_in=current_user.is_authenticated)

@app.route("/logout")
@login_required
def logout():
    next_page = request.args.get('next')
    logout_user()
    """Redirects user to the page on which they were before logging out"""
    return redirect(next_page or url_for('home'))

@app.route('/')
def home():
    return render_template('base.html', logged_in=current_user.is_authenticated)

@app.route('/projects')
def projects():
    fetched = fetch("VED2RISE")
    return render_template('projects.html', fetched=fetched, logged_in=current_user.is_authenticated)

@app.route("/posts")
def show_posts():
    try:
        with sqlite3.connect("posts.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts ORDER BY post_id DESC")
            posts = [{'post_id': row[0], 'time': row[2], 'content': row[1]} for row in cursor.fetchall()]
        return render_template("posts_admin.html", posts=posts, logged_in=current_user.is_authenticated)
    except sqlite3.Error as e:
        print(f"Database error: {e}")

@login_required
@app.route("/create_post", methods=["POST"])
def create_posts():
    """Post creation"""
    time_posted = dt.datetime.now().strftime("%d-%m-%Y")
    post_content = request.form["post_content"]

    try:
        with sqlite3.connect("posts.db") as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS posts (
                    post_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    post_content TEXT,
                    post_time TEXT
                );   
            """)
            conn.execute("INSERT INTO posts (post_content, post_time) VALUES (?, ?)", (post_content, time_posted))
            conn.commit()

        with sqlite3.connect("posts.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM posts ORDER BY post_id DESC")
            posts = [{'post_id': row[0], 'time': row[2], 'content': row[1]} for row in cursor.fetchall()]
            print(posts)

        return redirect(url_for("show_posts"))

    except sqlite3.Error as e:
        print(f"Database error: {e}")

@app.route("/delete_post/<int:post_id>", methods = ["POST"])
def delete_post(post_id):
    with sqlite3.connect("posts.db") as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM posts WHERE post_id = ?", (post_id,))
        conn.commit()
    flash('Post deleted successfully.')

    return redirect(url_for('show_posts'))

@app.route("/about_me", methods = ["POST", "GET"])
def bio():
    return render_template("about_me.html")

def fetch(username):
    """GITHUB's API to fetch my repos"""
    try:
        endpoint = f"https://api.github.com/users/{username}/repos"
        params = {"type": "public"}
        response = rq.get(url=endpoint, params=params)
        response.raise_for_status()
        repos = response.json()
        repo_info = [
            {
                "name": repo["name"],
                "url": repo["html_url"],
                "description": repo["description"] or "No description"
            } for repo in repos
        ]

        return repo_info

    except rq.HTTPError as e:
        print(f"HTTP error occurred: {e}")
        return []
    except rq.RequestException as e:
        print(f"Request error occurred: {e}")
        return []

if __name__ == '__main__':
    app.run(debug=True)