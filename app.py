from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import random
import os
from dotenv import load_dotenv
from datetime import datetime

# ------------------ LOAD ENVIRONMENT VARIABLES ------------------
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", os.urandom(24))

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
        # Check if this is the exam number validation from modal
        if 'exam_number' in request.form and 'score' not in request.form:
            exam_number = request.form.get('exam_number')
            name = request.form.get('name', '')
            
            # Validate exam number exists in database
            cursor.execute("SELECT * FROM exam_numbers WHERE exam_number=%s", (exam_number,))
            exam_record = cursor.fetchone()
            
            if not exam_record:
                flash('Invalid examination number. Please check and try again.', 'error')
                return redirect(url_for('index'))
            
            # Clear any previous exam attempts for this exam number
            cursor.execute("DELETE FROM exam_attempts WHERE exam_number=%s", (exam_number,))
            db.commit()
            
            # Store in session
            session['exam_number'] = exam_number
            session['name'] = name if name else exam_record.get('student_name', 'Student')
            
            # Redirect to GET request to show exam
            return redirect(url_for('exam'))
        
        # This is exam submission
        else:
            answers = request.form
            score = 0
            username = session.get('name', 'Student')
            exam_number = session.get('exam_number', 'Unknown')
            total_questions = 0

            # Process each answer and save to exam_attempts
            for q_id, selected in answers.items():
                if q_id in ['username', 'exam_number', 'name']:
                    continue
                
                total_questions += 1
                cursor.execute("SELECT correct_option FROM questions WHERE id=%s", (q_id,))
                result = cursor.fetchone()
                
                if result:
                    correct = result['correct_option']
                    is_correct = (int(selected) == correct)
                    
                    if is_correct:
                        score += 1
                    
                    # Save this answer to exam_attempts table
                    cursor.execute("""
                        INSERT INTO exam_attempts (exam_number, student_name, question_id, selected_option, is_correct)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (exam_number, username, q_id, int(selected), is_correct))
            
            db.commit()

            # Save overall result
            cursor.execute("INSERT INTO results (user_name, score) VALUES (%s, %s)", (username, score))
            db.commit()
            
            # Store score in session for review page
            session['last_score'] = score
            session['total_questions'] = total_questions

            return render_template('result.html', score=score, username=username, total_questions=total_questions)
    
    # Check if user has valid exam number in session
    if 'exam_number' not in session:
        return redirect(url_for('index'))
    
    # Show exam questions
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

# ------------------ REVIEW ANSWERS PAGE ------------------
@app.route('/review')
def review():
    exam_number = session.get('exam_number')
    
    if not exam_number:
        flash('No exam session found.', 'error')
        return redirect(url_for('index'))
    
    # Get all attempts for this exam number (most recent attempt)
    cursor.execute("""
        SELECT ea.*, q.question_text, q.option1, q.option2, q.option3, q.option4, 
               q.correct_option, q.explanation
        FROM exam_attempts ea
        JOIN questions q ON ea.question_id = q.id
        WHERE ea.exam_number = %s
        ORDER BY ea.timestamp DESC, ea.question_id
    """, (exam_number,))
    
    attempts = cursor.fetchall()
    
    if not attempts:
        flash('No exam attempts found to review.', 'error')
        return redirect(url_for('index'))
    
    # Separate correct and incorrect answers
    correct_answers = [a for a in attempts if a['is_correct']]
    incorrect_answers = [a for a in attempts if not a['is_correct']]
    
    return render_template('review.html', 
                         correct_answers=correct_answers, 
                         incorrect_answers=incorrect_answers,
                         username=session.get('name', 'Student'),
                         score=session.get('last_score', 0),
                         total=session.get('total_questions', len(attempts)))

# ------------------ ADMIN LOGIN ------------------
@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    error = ""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute("SELECT * FROM admins WHERE username=%s AND password=%s", (username, password))
        admin = cursor.fetchone()

        if admin:
            session['admin_logged_in'] = True
            return redirect(url_for('admin'))
        else:
            error = "Invalid username or password"

    return render_template('admin_login.html', error=error)

# ------------------ ADMIN PAGE ------------------
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    if request.method == 'POST':
        # Add Question
        if 'question_text' in request.form and 'question_id' not in request.form:
            question_text = request.form['question_text']
            option1 = request.form['option1']
            option2 = request.form['option2']
            option3 = request.form['option3']
            option4 = request.form['option4']
            correct_option = request.form['correct_option']
            explanation = request.form.get('explanation', '')

            cursor.execute("""
                INSERT INTO questions (question_text, option1, option2, option3, option4, correct_option, explanation)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (question_text, option1, option2, option3, option4, correct_option, explanation))
            db.commit()
            flash('Question added successfully!', 'success')
            return redirect(url_for('admin'))
        
        # Edit Question
        elif 'question_id' in request.form:
            question_id = request.form['question_id']
            question_text = request.form['question_text']
            option1 = request.form['option1']
            option2 = request.form['option2']
            option3 = request.form['option3']
            option4 = request.form['option4']
            correct_option = request.form['correct_option']
            explanation = request.form.get('explanation', '')
            
            cursor.execute("""
                UPDATE questions 
                SET question_text=%s, option1=%s, option2=%s, option3=%s, option4=%s, 
                    correct_option=%s, explanation=%s
                WHERE id=%s
            """, (question_text, option1, option2, option3, option4, correct_option, explanation, question_id))
            db.commit()
            flash('Question updated successfully!', 'success')
            return redirect(url_for('admin'))
        
        # Add Exam Number
        elif 'exam_number' in request.form:
            exam_number = request.form['exam_number']
            student_name = request.form.get('student_name', '')
            
            cursor.execute("SELECT * FROM exam_numbers WHERE exam_number=%s", (exam_number,))
            existing = cursor.fetchone()
            
            if existing:
                flash('Exam number already exists!', 'error')
            else:
                cursor.execute("""
                    INSERT INTO exam_numbers (exam_number, student_name)
                    VALUES (%s, %s)
                """, (exam_number, student_name))
                db.commit()
                flash('Exam number added successfully!', 'success')
            
            return redirect(url_for('admin'))

    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    
    cursor.execute("SELECT * FROM exam_numbers ORDER BY created_at DESC")
    exam_numbers = cursor.fetchall()
    
    return render_template('admin.html', questions=questions, exam_numbers=exam_numbers)

# ------------------ GET QUESTION FOR EDIT ------------------
@app.route('/get-question/<int:id>')
def get_question(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))
    
    cursor.execute("SELECT * FROM questions WHERE id=%s", (id,))
    question = cursor.fetchone()
    
    if question:
        return render_template('edit_question.html', question=question)
    else:
        flash('Question not found!', 'error')
        return redirect(url_for('admin'))

# ------------------ DELETE QUESTION ------------------
@app.route('/delete/<int:id>')
def delete_question(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    cursor.execute("DELETE FROM questions WHERE id = %s", (id,))
    db.commit()
    flash('Question deleted!', 'success')
    return redirect(url_for('admin'))

# ------------------ DELETE EXAM NUMBER ------------------
@app.route('/delete-exam-number/<int:id>')
def delete_exam_number(id):
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_login'))

    cursor.execute("DELETE FROM exam_numbers WHERE id = %s", (id,))
    db.commit()
    flash('Exam number deleted!', 'success')
    return redirect(url_for('admin'))

# ------------------ CLEAR SESSION ------------------
@app.route('/clear-session')
def clear_session():
    session.pop('exam_number', None)
    session.pop('name', None)
    session.pop('last_score', None)
    session.pop('total_questions', None)
    return redirect(url_for('index'))

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