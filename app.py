from flask import Flask, render_template, request, redirect, url_for, session
import mysql.connector
import random
import os
from dotenv import load_dotenv

# ------------------ LOAD ENVIRONMENT VARIABLES ------------------
load_dotenv()  # this loads .env file variables into the environment

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))  # fallback to random key if missing

# ------------------ DATABASE CONNECTION ------------------
db = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASS"),
    database=os.getenv("DB_NAME", "exam_app")
)
cursor = db.cursor(dictionary=True)


# ------------------ HOME PAGE ------------------
@app.route('/')
def index():
    return render_template('index.html')

# ------------------ EXAM PAGE ------------------
@app.route('/exam', methods=['GET', 'POST'])
def exam():
    if request.method == 'POST':
        answers = request.form
        score = 0
        username = answers.get('username', 'Guest')

        for q_id, selected in answers.items():
            if q_id == 'username':
                continue
            cursor.execute("SELECT correct_option FROM questions WHERE id=%s", (q_id,))
            correct = cursor.fetchone()['correct_option']
            if int(selected) == correct:
                score += 1

        cursor.execute("SELECT COUNT(*) AS total FROM questions")
        total_questions = cursor.fetchone()['total']

        cursor.execute("INSERT INTO results (user_name, score) VALUES (%s, %s)", (username, score))
        db.commit()

        return render_template('result.html', score=score, username=username, total_questions=total_questions)

    cursor.execute("SELECT id FROM questions")
    all_ids = [q['id'] for q in cursor.fetchall()]
    random.shuffle(all_ids)
    selected_ids = all_ids[:50]

    if selected_ids:
        format_strings = ','.join(['%s'] * len(selected_ids))
        query = f"SELECT * FROM questions WHERE id IN ({format_strings})"
        cursor.execute(query, tuple(selected_ids))
        questions = cursor.fetchall()
        random.shuffle(questions)
    else:
        questions = []

    return render_template('exam.html', questions=questions)

# ------------------ ADMIN LOGIN ------------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Query MySQL for the admin credentials
        cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s", (username, password))
        admin = cursor.fetchone()

        if admin:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = "Invalid username or password"

    # Pass error to template; will be empty string if GET request
    return render_template('admin_login.html', error=error)

# ------------------ ADMIN PAGE ------------------
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        question_text = request.form['question_text']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        option4 = request.form['option4']
        correct_option = request.form['correct_option']

        cursor.execute("""
            INSERT INTO questions (question_text, option1, option2, option3, option4, correct_option)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (question_text, option1, option2, option3, option4, correct_option))
        db.commit()
        return redirect(url_for('admin'))

    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    return render_template('admin.html', questions=questions)

# ------------------ DELETE QUESTION ------------------
@app.route('/delete/<int:id>')
def delete_question(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    cursor.execute("DELETE FROM questions WHERE id = %s", (id,))
    db.commit()
    return redirect(url_for('admin'))

# ------------------ LOGOUT ------------------
@app.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('index'))

# ------------------ RUN APP ------------------
if __name__ == '__main__':
    app.run(
        debug=True,
        use_reloader=True,
        extra_files=[
            'templates/',
            'static/'
        ]
    )
