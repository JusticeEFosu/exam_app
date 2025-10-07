from flask import Flask, render_template, request, redirect, url_for
import mysql.connector
import random

app = Flask(__name__)

# Connect to MySQL
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="Justice1999",  # your MySQL password
    database="exam_app"
)
cursor = db.cursor(dictionary=True)


@app.route('/')
def index():
    return render_template('index.html')


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

        # Get total number of questions
        cursor.execute("SELECT COUNT(*) AS total FROM questions")
        total_questions = cursor.fetchone()['total']

        # Save result to database
        cursor.execute("INSERT INTO results (user_name, score) VALUES (%s, %s)", (username, score))
        db.commit()

        # Render result page with total questions included
        return render_template('result.html', score=score, username=username, total_questions=total_questions)

    # Fetch all question IDs
    cursor.execute("SELECT id FROM questions")
    all_ids = [q['id'] for q in cursor.fetchall()]

    # Shuffle and pick 50 (or all if less than 50)
    random.shuffle(all_ids)
    selected_ids = all_ids[:50]

    # Fetch only the selected questions
    format_strings = ','.join(['%s'] * len(selected_ids))
    query = f"SELECT * FROM questions WHERE id IN ({format_strings})"
    cursor.execute(query, tuple(selected_ids))
    questions = cursor.fetchall()

    random.shuffle(questions)  # optional: shuffle again for variety

    return render_template('exam.html', questions=questions)


# ---------- ADMIN PAGE ----------
@app.route('/admin', methods=['GET', 'POST'])
def admin():
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


@app.route('/delete/<int:id>')
def delete_question(id):
    cursor.execute("DELETE FROM questions WHERE id = %s", (id,))
    db.commit()
    return redirect(url_for('admin'))


if __name__ == '__main__':
    app.run(debug=True)
