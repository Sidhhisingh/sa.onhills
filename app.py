from flask import Flask, render_template, request, redirect, session
import sqlite3
import os
import time
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = "naye_waali_key_123"

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

PRIVATE_FOLDER = 'static/private'
os.makedirs(PRIVATE_FOLDER, exist_ok=True)


# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        message TEXT,
        image TEXT,
        video TEXT,
        username TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS private_posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS music (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        file TEXT,
        username TEXT
    )
    ''')

    cur.execute('''
    CREATE TABLE IF NOT EXISTS poetry (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text TEXT,
        username TEXT
    )
    ''')

    conn.commit()
    conn.close()

init_db()


# ---------- HOME ----------
# ---------- HOME (INDEX) ----------
@app.route('/', methods=['GET', 'POST'])
def home():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    if request.method == 'POST':
        # Agar session mein username nahi hai aur form se aaya hai, toh set karo
        form_username = request.form.get('username')
        if form_username:
            session['username'] = form_username

        username = session.get('username')

        # Agar abhi bhi username nahi hai, toh prompt dikhao
        if not username:
            return "⚠️ Pehle apna naam daalo home page par!"

        message = request.form.get('message')
        
        # Ek hi dabba handling (Donon mein se jo bhi aaye)
        file = request.files.get('photo') 
        
        image_name = ""
        video_name = ""

        if file and file.filename != "":
            filename = secure_filename(file.filename)
            filename = str(int(time.time())) + "_" + filename
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            
            # Check if it's a video or image based on extension
            ext = filename.split('.')[-1].lower()
            if ext in ['mp4', 'mov', 'avi']:
                video_name = filename
            else:
                image_name = filename

        cur.execute(
            "INSERT INTO posts (message, image, video, username) VALUES (?, ?, ?, ?)",
            (message, image_name, video_name, username)
        )
        conn.commit()

    cur.execute("SELECT * FROM posts ORDER BY id DESC")
    posts = cur.fetchall()
    conn.close()
    return render_template('index.html', posts=posts)
# ---------- DELETE POST ----------
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


# ---------- POETRY ----------
# ---------- POETRY (Link Fix) ----------
@app.route('/poetry', methods=['GET', 'POST'])
def poetry():
    username = session.get('username')
    if not username:
        return "⚠️ Pehle Home page pe jaake apna naam set karo!"

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

# ---------- DELETE POETRY ----------
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

#-------- SADIL LOGIN ----------
@app.route('/sadil', methods=['GET', 'POST'])
def sadil():
    # Force logout karne ke liye ye check: 
    # Agar url me ?logout=1 ho toh session clear kar do
    if request.args.get('logout'):
        session.pop('is_sadil', None)
        return redirect('/sadil')

    # 1. Agar session 'is_sadil' True nahi hai, toh login karwao
    if not session.get('is_sadil'):
        if request.method == 'POST':
            password = request.form.get('password')
            print(f"Password entered: {password}") # Terminal me check karo
            if password == "sadil123":
                session['is_sadil'] = True
                return redirect('/sadil')
            else:
                return "<h1 style='color:white;text-align:center;'>❌ Galat Password! <a href='/sadil'>Try Again</a></h1>"
        
        # Ye line pakka check karo ki templates folder me login.html hai
        return render_template('login.html')

    # 2. Agar session True hai, tabhi content dikhao
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM private_posts ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return render_template('sadil.html', data=data)

# ---------- MUSIC ----------
@app.route('/music', methods=['GET', 'POST'])
def music():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    username = session.get('username', 'anonymous')

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


# ---------- DELETE MUSIC ----------
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


# ---------- PRIVATE UPLOAD ----------
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


# ---------- DELETE PRIVATE ----------
@app.route('/delete_private/<int:id>', methods=['POST'])
def delete_private(id):
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("DELETE FROM private_posts WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/sadil')


# ---------- PHOTOS ----------
@app.route('/photos')
def photos():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM posts WHERE image != '' ORDER BY id DESC")
    data = cur.fetchall()
    conn.close()
    return render_template('photos.html', data=data)


# ---------- VIDEOS ----------
@app.route('/videos', methods=['GET', 'POST'])
def videos():
    conn = sqlite3.connect('database.db')
    cur = conn.cursor()

    username = session.get('username', 'anonymous')

    if request.method == 'POST':
        video = request.files.get('video')

        if video and video.filename != "":
            filename = secure_filename(video.filename)
            filename = str(int(time.time())) + "_" + filename
            video.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            cur.execute(
                "INSERT INTO posts (message, image, video, username) VALUES (?, ?, ?, ?)",
                ("", "", filename, username)
            )
            conn.commit()

    cur.execute("SELECT * FROM posts WHERE video != '' ORDER BY id DESC")
    data = cur.fetchall()

    conn.close()
    return render_template('videos.html', data=data)


# ---------- RUN ----------
if __name__ == '__main__':
    app.run(debug=True)