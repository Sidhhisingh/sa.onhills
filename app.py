from flask import Flask, render_template, request, redirect
import sqlite3
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    # POSTS
    cur.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        image TEXT
    )
    ''')

    # PRIVATE POSTS
    cur.execute('''
    CREATE TABLE IF NOT EXISTS private_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file TEXT
    )
    ''')

    # MUSIC
    cur.execute('''
    CREATE TABLE IF NOT EXISTS music (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        file TEXT
    )
    ''')

    # POETRY
    cur.execute('''
    CREATE TABLE IF NOT EXISTS poetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT
    )
    ''')

    # PINNED (MAX 3)
    cur.execute('''
    CREATE TABLE IF NOT EXISTS pinned (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        post_id INTEGER
    )
    ''')

    conn.commit()
    conn.close()

init_db()


# ---------- HOME ----------
@app.route('/', methods=['GET', 'POST'])
def home():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if request.method == 'POST':
        message = request.form.get('message')
        file = request.files.get('photo')

        filename = ""
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filename = str(int(time.time())) + "_" + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        cur.execute("INSERT INTO posts (message, image) VALUES (?, ?)", (message, filename))
        conn.commit()

    # FETCH
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cur.fetchall()

    cur.execute("SELECT * FROM music ORDER BY id DESC")
    songs = cur.fetchall()

    cur.execute("SELECT * FROM poetry ORDER BY id DESC")
    poetry = cur.fetchall()

    conn.close()

    return render_template('index.html', posts=posts, songs=songs, poetry=poetry)


# ---------- DELETE POST ----------
@app.route('/delete_post/<int:id>')
def delete_post(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM posts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')


# ---------- MUSIC ----------
@app.route('/music', methods=['GET', 'POST'])
def music():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if request.method == 'POST':
        title = request.form.get('title')
        file = request.files.get('song')

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filename = str(int(time.time())) + "_" + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            cur.execute("INSERT INTO music (title, file) VALUES (?, ?)", (title, filename))
            conn.commit()

    cur.execute("SELECT * FROM music ORDER BY id DESC")
    songs = cur.fetchall()

    conn.close()

    return render_template('music.html', songs=songs)


# ---------- DELETE MUSIC ----------
@app.route('/delete_song/<int:id>')
def delete_song(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM music WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/music')


# ---------- POETRY ----------
@app.route('/poetry', methods=['GET', 'POST'])
def poetry():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if request.method == 'POST':
        text = request.form.get('text')

        if text:
            cur.execute("INSERT INTO poetry (text) VALUES (?)", (text,))
            conn.commit()

    cur.execute("SELECT * FROM poetry ORDER BY id DESC")
    data = cur.fetchall()

    conn.close()

    return render_template('poetry.html', data=data)


# ---------- DELETE POETRY ----------
@app.route('/delete_poetry/<int:id>')
def delete_poetry(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM poetry WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/poetry')


# ---------- SADIL LOGIN ----------
@app.route('/sadil', methods=['GET', 'POST'])
def sadil():
    if request.method == 'POST':
        password = request.form.get('password')

        if password == "sadil123":
            conn = sqlite3.connect('database.db')
            cur = conn.cursor()
            cur.execute("SELECT * FROM private_posts ORDER BY id DESC")
            data = cur.fetchall()
            conn.close()

            return render_template('sadil.html', data=data)

        else:
            return "<h1 style='text-align:center; margin-top:100px;'>❌ aap sadil h ? nhi na to chliye jaiye yha se😤</h1>"

    return render_template('login.html')


# ---------- PRIVATE UPLOAD (FIXED) ----------
@app.route('/upload_private', methods=['POST'])
def upload_private():
    file = request.files.get('file')

    if file and file.filename != "":
        filename = secure_filename(file.filename)
        filename = str(int(time.time())) + "_" + filename

        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        conn = sqlite3.connect('database.db')
        cur = conn.cursor()
        cur.execute("INSERT INTO private_posts (file) VALUES (?)", (filename,))
        conn.commit()
        conn.close()

    return redirect('/sadil')   # 🔥 IMPORTANT FIX


# ---------- PIN (MAX 3) ----------
@app.route('/pin/<int:id>')
def pin(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM pinned")
    count = cur.fetchone()[0]

    if count < 3:
        cur.execute("INSERT INTO pinned (post_id) VALUES (?)", (id,))
        conn.commit()

    conn.close()
    return redirect('/sadil') 

# ---------- phtos.html ----------
@app.route('/photos')
def photos():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    data = cur.fetchall()

    conn.close()

    return render_template('photos.html', data=data)


# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)