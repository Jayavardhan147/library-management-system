from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
import csv
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask import session

app = Flask(__name__)
app.secret_key = 'your_secret_key' 

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  
    return conn



def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # Create table for books
    c.execute('''CREATE TABLE IF NOT EXISTS books (
        id INTEGER PRIMARY KEY,
        title TEXT,
        author TEXT,
        isbn TEXT,
        publication_date TEXT,
        genre TEXT,
        book_count INTEGER)''')
    
    # Create table for students
    c.execute('''CREATE TABLE IF NOT EXISTS students (
        roll_number TEXT PRIMARY KEY,
        name TEXT,
        email TEXT,
        mobile_number TEXT,
        course TEXT,
        department TEXT,
        password TEXT)''')
    
    # Create table for issued books
    c.execute('''CREATE TABLE IF NOT EXISTS issued_books (
        book_id INTEGER,
        roll_number TEXT,
        issue_date TEXT,
        return_date TEXT,
        FOREIGN KEY(book_id) REFERENCES books(id),
        FOREIGN KEY(roll_number) REFERENCES students(roll_number))''')

    conn.commit()

@app.route('/logout', methods=['GET'])
def logout():
    # Clear all session data
    session.clear()
    # Redirect to the home or login page
    return redirect(url_for('login'))

@app.route('/')
def login():
    return render_template('login.html')

# Route for librarian dashboard
@app.route('/librarian-dashboard', methods=['GET','POST'])
def librarian_dashboard():
    return render_template('librarian_dashboard.html')

# Route to add a book
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    if request.method == 'POST':
        book_id = request.form['id']
        title = request.form['title']
        author = request.form['author']
        isbn = request.form['isbn']
        publication_date = request.form['publication_date']
        genre = request.form['genre']
        book_count = request.form['book_count']

        conn = get_db()
        c = conn.cursor()
        c.execute("INSERT INTO books (title, author, isbn, publication_date, genre, book_count) VALUES (?, ?, ?, ?, ?, ?)",
                  (title, author, isbn, publication_date, genre, book_count))
        conn.commit()
        return redirect(url_for('librarian_dashboard'))
    
    return render_template('add_book.html')

# Route to remove a book
@app.route('/remove_book', methods=['GET', 'POST'])
def remove_book():
    if request.method == 'POST':
        book_id = request.form['book_id']
        title = request.form['title']

        conn = get_db()
        c = conn.cursor()
        c.execute("DELETE FROM books WHERE id=?", (book_id,))
        conn.commit()
        return redirect(url_for('librarian_dashboard'))

    return render_template('remove_book.html')

# Route to upload books via CSV
@app.route('/add_books_csv', methods=['GET', 'POST'])
def add_books_csv():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        
        if file and file.filename.endswith('.csv'):
            file_content = file.read().decode('utf-8').splitlines()
            csv_reader = csv.reader(file_content)

            conn = get_db()
            c = conn.cursor()

            next(csv_reader, None)

            try:
                for row in csv_reader:
                    title, author, isbn, publication_date, genre, book_count = row
                    if not title or not author or not isbn or not book_count:
                        flash('Missing required fields in CSV')
                        continue
                    
                    c.execute("INSERT INTO books (title, author, isbn, publication_date, genre, book_count) VALUES (?, ?, ?, ?, ?, ?)",
                              (title, author, isbn, publication_date, genre, int(book_count)))
                
                conn.commit()
                flash('Books added successfully!')
                return redirect(url_for('librarian_dashboard'))  
            
            except Exception as e:
                flash(f'Error occurred: {str(e)}')
                conn.rollback()  
            finally:
                conn.close()

        else:
            flash('Invalid file format. Please upload a CSV file.')
            return redirect(request.url)

    return render_template('add_books_csv.html')



@app.route('/register_student', methods=['GET', 'POST'])
def register_student():
    if request.method == 'POST':
        roll_number = request.form['roll_number']
        name = request.form['name']
        email = request.form['email']
        mobile_number = request.form['mobile_number']
        course = request.form['course']
        department = request.form['department']
        password = request.form['password']

        
        hashed_password = generate_password_hash(password)

        # Insert the student data into the database
        try:
            conn = get_db()
            c = conn.cursor()
            c.execute('''
                INSERT INTO students (roll_number, name, email, mobile_number, course, department, password)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (roll_number, name, email, mobile_number, course, department, hashed_password))
            conn.commit()

            flash(f'Student {roll_number} registered successfully!', 'success')
        except sqlite3.IntegrityError:
            flash(f'Error: Student with Roll Number {roll_number} already exists.', 'error')
        return redirect(url_for('librarian_dashboard'))

    return render_template('register_student.html')


@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    if request.method == 'POST':
        book_id = request.form['book_id']
        roll_number = request.form['roll_number']
        course = request.form['course']
        department = request.form['department']

        conn = get_db()
        c = conn.cursor()

        
        c.execute("SELECT book_count FROM books WHERE id = ?", (book_id,))
        book = c.fetchone()
        if not book:
            flash('Book ID not found!', 'error')
            return redirect(url_for('issue_book'))

        if book['book_count'] <= 0:
            flash('No copies of the book are available!', 'error')
            return redirect(url_for('issue_book'))

        # Check if the student exists
        c.execute("SELECT * FROM students WHERE roll_number = ?", (roll_number,))
        student = c.fetchone()
        if not student:
            flash('Student Roll Number not found!', 'error')
            return redirect(url_for('issue_book'))

        # Calculate issue and return date
        issue_date = datetime.now()
        return_date = issue_date + timedelta(days=20)

        # Insert into the issued_books table
        c.execute('''
            INSERT INTO issued_books (book_id, roll_number, issue_date, return_date)
            VALUES (?, ?, ?, ?)
        ''', (book_id, roll_number, issue_date, return_date))

        # Reduce the book count
        c.execute("UPDATE books SET book_count = book_count - 1 WHERE id = ?", (book_id,))
        conn.commit()

        # Calculate days left
        days_left = (return_date - issue_date).days
        flash(f"Book issued to {student['name']} (Roll No: {roll_number}). {days_left} days left to return.", 'success')
        return redirect(url_for('librarian_dashboard'))

    return render_template('issue_book.html')

@app.route('/search_book', methods=['GET', 'POST'])
def search_book():
    conn = get_db()
    c = conn.cursor()

    books = []
    if request.method == 'POST':
        # Collect search criteria
        search_query = request.form['search_query']

        # Search in the database
        c.execute('''
            SELECT 
                books.id AS book_id,
                books.title,
                books.author,
                books.isbn,
            
                books.genre,
                issued_books.roll_number AS issued_to
            FROM books
            LEFT JOIN issued_books ON books.id = issued_books.book_id
            WHERE books.id LIKE ? OR books.title LIKE ?  OR books.isbn LIKE ?
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        books = c.fetchall()

    return render_template('search_book.html', books=books)


@app.route('/student-dashboard', methods=['GET'])
def student_dashboard():
    return render_template('student_dashboard.html')


@app.route('/student-login', methods=['POST'])
def student_login():
    username = request.form['username']
    password = request.form['password']

    conn = get_db()
    c = conn.cursor()
    c.execute('SELECT * FROM students WHERE roll_number = ?', (username,))
    student = c.fetchone()

    if student and check_password_hash(student['password'], password):
        session['student_roll_number'] = student['roll_number']  # Store roll number in session
        flash(f'Welcome, {student["name"]}!', 'success')
        return redirect(url_for('student_dashboard'))  # Redirect to the student's dashboard
    else:
        flash('Invalid username or password', 'error')
        return redirect('/')


@app.route('/books_issued', methods=['GET'])
def books_issued():


    roll_number = session['student_roll_number']
    
    conn = get_db()
    c = conn.cursor()

    # Get the books issued by the student
    c.execute('''SELECT books.title, books.author, issued_books.issue_date, issued_books.return_date
                 FROM books
                 JOIN issued_books ON books.id = issued_books.book_id
                 WHERE issued_books.roll_number = ?''', (roll_number,))
    issued_books = c.fetchall()

    # Check if no books are issued
    if not issued_books:
        flash('You have no books issued.', 'info')

    # Calculate days left for each book
    today = datetime.now()
    updated_books = []
    for book in issued_books:
        book_dict = dict(book)  # Convert Row to dictionary

        try:
            return_date = datetime.strptime(book_dict['return_date'], '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            
            return_date = datetime.strptime(book_dict['return_date'], '%Y-%m-%d %H:%M:%S')

        days_left = (return_date - today).days
        book_dict['days_left'] = days_left  

        updated_books.append(book_dict)

    return render_template('books_issued.html', books=updated_books)




@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        username = request.form['username']
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        # Check if new password and confirm password match
        if new_password != confirm_password:
            flash('New password and confirm password do not match', 'error')
            return redirect(url_for('change_password'))

        conn = get_db()
        c = conn.cursor()
        c.execute('SELECT * FROM students WHERE roll_number = ?', (username,))
        student = c.fetchone()

        if student and check_password_hash(student['password'], old_password):
            # Update the password
            hashed_new_password = generate_password_hash(new_password)
            c.execute('UPDATE students SET password = ? WHERE roll_number = ?', (hashed_new_password, username))
            conn.commit()
            flash('Password changed successfully!', 'success')
            return redirect('/student-dashboard')  
        else:
            flash('Invalid credentials', 'error')

    return render_template('change_password.html')

@app.route('/book_search', methods=['GET', 'POST'])
def book_search():
    conn = get_db()
    c = conn.cursor()

    books = []
    if request.method == 'POST':
        # Collect search criteria
        search_query = request.form['search_query']

        # Search in the database
        c.execute('''
            SELECT 
                books.id AS book_id,
                books.title,
                books.author,
                books.isbn,
                books.genre
            FROM books
            WHERE books.id LIKE ? OR books.title LIKE ? OR books.isbn LIKE ?
        ''', (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        books = c.fetchall()

    return render_template('book_search.html', books=books)





if __name__ == '__main__':
    init_db()
    app.run(debug=True)
