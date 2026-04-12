from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "naye_waali_key_123"

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute('CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY AUTOINCREMENT, message TEXT, image TEXT, video TEXT, username TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS private_posts (id INTEGER PRIMARY KEY AUTOINCREMENT, file TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS music (id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, file TEXT, username TEXT)')
    cur.execute('CREATE TABLE IF NOT EXISTS poetry (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, username TEXT)')
    conn.commit()
    conn.close()

init_db()

# ---------- HOME ----------
@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        form_username = request.form.get('username')
        if form_username:
            session['username'] = form_username
            return redirect('/') # Naam save karke page refresh karo

    session.pop('is_sadil', None) 
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cur.fetchall()
    conn.close()
    return render_template('index.html', posts=posts, username=session.get('username'))
#---------- name logout krne ke liye ----------
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
# ---------- POETRY ----------
@app.route('/poetry', methods=['GET', 'POST'])
def poetry():
    username = session.get('username')
    if not username: return redirect('/') # Bina naam ke No Entry

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    if request.method == 'POST':
        text = request.form.get('text')
        if text:
            cur.execute("INSERT INTO poetry (text, username) VALUES (?, ?)", (text, username))
            conn.commit()
    cur.execute("SELECT * FROM poetry ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return render_template('poetry.html', data=data)

# ---------- MUSIC ----------
@app.route('/music', methods=['GET', 'POST'])
def music():
    username = session.get('username')
    if not username: return redirect('/')

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    if request.method == 'POST':
        title = request.form.get('title')
        file = request.files.get('song')
        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filename = str(int(time.time())) + "_" + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute("INSERT INTO music (title, file, username) VALUES (?, ?, ?)", (title, filename, username))
            conn.commit()
    cur.execute("SELECT * FROM music ORDER BY id DESC")
    songs = cur.fetchall()
    conn.close()
    return render_template('music.html', songs=songs)

# -------- SADIL LOGIN & VAULT ----------
@app.route('/sadil', methods=['GET', 'POST'])
def sadil():
    username = session.get('username')
    if not username: return redirect('/')

    error = None
    if not session.get('is_sadil'):
        if request.method == 'POST':
            password = request.form.get('password')
            if password == "sadil123":
                session['is_sadil'] = True
                return redirect('/sadil')
            else:
                error = "Aap Sadil hain? Nahi na... toh chaliye jaiye yahan se!"
        return render_template('login.html', error=error)

    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM private_posts ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return render_template('sadil.html', data=data)

# ---------- DELETE ROUTES ----------
@app.route('/delete_post/<int:id>', methods=['POST'])
def delete_post(id):
    username = session.get('username')
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT username FROM posts WHERE id=?", (id,))
    owner = cur.fetchone()
    if owner and owner[0] == username:
        cur.execute("DELETE FROM posts WHERE id=?", (id,))
        conn.commit()
    conn.close()
    return redirect('/')

@app.route('/delete_poetry/<int:id>', methods=['POST'])
def delete_poetry(id):
    username = session.get('username')
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT username FROM poetry WHERE id=?", (id,))
    owner = cur.fetchone()
    if owner and owner[0] == username:
        cur.execute("DELETE FROM poetry WHERE id=?", (id,))
        conn.commit()
    conn.close()
    return redirect('/poetry')

@app.route('/delete_song/<int:id>', methods=['POST'])
def delete_song(id):
    username = session.get('username')
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT username FROM music WHERE id=?", (id,))
    owner = cur.fetchone()
    if owner and owner[0] == username:
        cur.execute("DELETE FROM music WHERE id=?", (id,))
        conn.commit()
    conn.close()
    return redirect('/music')

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
    return redirect('/sadil')

@app.route('/delete_private/<int:id>', methods=['POST'])
def delete_private(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM private_posts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/sadil')

# ---------- PHOTOS & VIDEOS ----------
@app.route('/photos')
def photos():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE image != '' ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return render_template('photos.html', data=data)

@app.route('/videos', methods=['GET', 'POST'])
def videos():
    username = session.get('username', 'anonymous')
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    if request.method == 'POST':
        video = request.files.get('video')
        if video and video.filename != "":
            filename = secure_filename(video.filename)
            filename = str(int(time.time())) + "_" + filename
            video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            cur.execute("INSERT INTO posts (message, image, video, username) VALUES (?, ?, ?, ?)", ("", "", filename, username))
            conn.commit()
    cur.execute("SELECT * FROM posts WHERE video != '' ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return render_template('videos.html', data=data)

if __name__ == '__main__':
    app.run(debug=True)