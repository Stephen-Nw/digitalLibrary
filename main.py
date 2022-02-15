from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from forms import LoginForm, RegisterForm
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash
import requests
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SecretKey']
Bootstrap(app)
bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///books-tracker.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# CREATE DATABASES
class User(UserMixin, db.Model):
    __tablename__ = "users_table"
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(250))
    last = db.Column(db.String(250))
    email = db.Column(db.String(250), unique=True)
    password = db.Column(db.String(250))


class Book(db.Model):
    __tablename__ = "books_table"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.String(250), nullable=False)
    book_title = db.Column(db.String(350), nullable=False)
    book_author = db.Column(db.String(350), nullable=False)
    image_url = db.Column(db.String(350))
    publish_date = db.Column(db.String(250))
    category = db.Column(db.String(250), nullable=False)


db.create_all()


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/login', methods=["POST", "GET"])
def login_user():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("User does not exist", category='error')
            return redirect(url_for('login_user'))
        elif not check_password_hash(user.password, password):
            flash("Wrong password", category='error')
            return redirect(url_for('login_user'))
        else:
            return redirect(url_for('completed_reading'))
    return render_template('login.html', form=form)


@app.route('/logout')
def logout_user():
    return render_template('index.html')


@app.route('/register', methods=["POST", "GET"])
def register_user():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User()
        if form.password.data == form.repeatPassword.data:
            new_user.password = generate_password_hash(form.password.data, rounds=12).decode('utf-8')
        else:
            flash("Passwords do not match!!", category='error')
            return redirect(url_for('register_user'))
        new_user.first = form.firstName.data
        new_user.last = form.lastName.data
        new_user.email = form.email.data

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('in_progress'))

    return render_template('register.html', form=form)


@app.route('/book', methods=["POST", "GET"])
def find_book():
    data = request.form
    if request.method == "POST":
        title = data['book_needed']

        parameters = {
            "q": title,

        }

        response = requests.get("https://www.googleapis.com/books/v1/volumes", params=parameters)
        response.raise_for_status()
        book_data = response.json()
        book_list = book_data['items']

        return render_template('search.html', books=book_list)
    else:
        return render_template('index.html')


@app.route('/reading', methods=["POST", "GET"])
def in_progress():
    """Retrieves books currently being read by user"""
    all_books = db.session.query(Book).all()
    return render_template('read_in_progress.html', books=all_books)


@app.route('/add_read/<book_id>', methods=["POST", "GET"])
def add_in_progress(book_id):
    """Add book to database in progress category if not previously added"""
    book_in_db = Book.query.get(book_id)
    if not book_in_db:
        response = requests.get(f"https://www.googleapis.com/books/v1/volumes/{book_id}")
        response.raise_for_status()
        book_data = response.json()

        book_author = book_data['volumeInfo']['authors']  # This is a list that has to be converted into a string before
        # adding to db

        new_book = Book()
        new_book.book_id = book_id
        new_book.book_title = book_data['volumeInfo']['title']
        new_book.book_author = ', '.join([str(item) for item in book_author])  # Convert author list to string
        new_book.image_url = book_data['volumeInfo']['imageLinks']['thumbnail']
        new_book.publish_date = book_data['volumeInfo']['publishedDate']
        new_book.category = "In Progress"
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('in_progress'))
    elif book_in_db.category != "In Progress":
        print("Update category")
        return redirect(url_for('in_progress'))
    else:
        return redirect(url_for('in_progress'))


@app.route('/complete')
def completed_reading():
    """Retrieves books that have been read by user"""
    return render_template('read_complete.html')


@app.route('/future')
def later_reading():
    """Retrieves books to be read later by user"""
    return render_template('read_later.html')







if __name__ == "__main__":
    app.run(debug=True)
