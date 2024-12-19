Firstly install all the requirments bye this command "pip install -r requirements.txt" 

->In app.py, the SQLAlchemy library is used to define models and handle database interactions. The database is initialized with the db.create_all() method to create the necessary tables.
->librarians can login using their respective credentials. And Students login using credentials given by librarians and password can be changed by students later.
->Authentication is handled using Flask-Login for session management and JWT for API token-based security.

--)Librarian Functionalities
1.Add New Books:
add_book.html
Librarians can add books with details like title, author, ISBN, publication date, genre, and count.

2.Upload Books via CSV:
add_books_csv.html
Librarians can upload a CSV file to bulk-add books.

3.View Issued Books:
book_issued.html
Lists all issued books, along with student information, issue date, and return deadline.

5.Remove Books:
remove_book.html
Enables librarians to delete books from the library database.

6.Manage Book Issuance:
issue_book.html
Allows librarians to issue books to students, track deadlines, and manage availability.

7.Register Students:
register_student.html
Librarians can add new students by collecting details like roll number, email, mobile number, course, and department.


--)Student Functionalities
1.Search Books:
search_book.html
Students can search books by title, author, ISBN, or course (e.g., B.Tech, M.Tech, BCA).
View Issued Books:

2.book_issued.html
Students can see the list of books they have borrowed, with issue and return deadlines.

3.Borrow Books:
Students can borrow up to 3 books at a time. The librarian tracks availability.
