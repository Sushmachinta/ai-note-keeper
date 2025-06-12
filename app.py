from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
import speech_recognition as sr
import pyttsx3
from werkzeug.security import generate_password_hash, check_password_hash
import os
from voice_input import voice_to_text

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "3f809921c4b224f0f5a05e5a1ce7ed3c")

db = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", "1234"),
    database=os.getenv("DB_NAME", "ai_note_keeper")
)
cursor = db.cursor(dictionary=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
        db.commit()
        return redirect('/login')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        cursor.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cursor.fetchone()
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            return redirect('/')
        return "Invalid credentials"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect('/login')
    cursor.execute("SELECT * FROM notes WHERE user_id = %s", (session['user_id'],))
    notes = cursor.fetchall()
    return render_template('index.html', notes=notes)

@app.route('/add', methods=['POST'])
def add_note():
    note = request.form['note']
    cursor.execute("INSERT INTO notes (content, user_id) VALUES (%s, %s)", (note, session['user_id']))
    db.commit()
    return redirect('/')

@app.route('/voice', methods=['POST'])
def add_voice_note():
    note = voice_to_text()
    cursor.execute("INSERT INTO notes (content, user_id) VALUES (%s, %s)", (note, session['user_id']))
    db.commit()
    return redirect('/')

from flask import jsonify
from flask import abort

@app.route('/speak/<int:id>')
def speak_note(id):
    cursor.execute("SELECT content FROM notes WHERE id = %s AND user_id = %s", (id, session['user_id']))
    note = cursor.fetchone()
    if note:
        return jsonify({'content': note['content']})
    else:
        return jsonify({'error': 'Note not found'}), 404

@app.route('/delete/<int:id>')
def delete_note(id):
    cursor.execute("DELETE FROM notes WHERE id = %s AND user_id = %s", (id, session['user_id']))
    db.commit()
    return redirect('/')

if __name__ == "__main__":
    app.run(debug=True)
