import sqlalchemy.exc
from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin, LoginManager, login_user, current_user, logout_user, login_required
from forms import LoginForm, RegisterForm
from flask_bcrypt import Bcrypt, generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship
import requests
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ['SecretKey']
Bootstrap(app)
bcrypt = Bcrypt(app)

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///books-tracker.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# CREATE TABLES
class Book(db.Model):
    __tablename__ = "books_table"
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.String(250), nullable=False)
    book_title = db.Column(db.String(350), nullable=False)
    book_author = db.Column(db.String(350), nullable=False)
    image_url = db.Column(db.String(350))
    publish_date = db.Column(db.String(250))
    category = db.Column(db.String(250), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey("users_table.id"))
    reader = relationship('User', back_populates="book_list")


class User(UserMixin, db.Model):
    __tablename__ = "users_table"
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(250))
    last = db.Column(db.String(250))
    email = db.Column(db.String(250), unique=True)
    password = db.Column(db.String(250))

    book_list = relationship('Book', back_populates="reader")


db.create_all()


# CREATE ROUTES
@app.route('/')
def home():
    """Route to cover page"""
    return render_template('index.html')


@app.route('/login', methods=["POST", "GET"])
def user_login():
    """Log user in"""
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        user = User.query.filter_by(email=email).first()

        if not user:
            flash("User does not exist", category='error')
            return redirect(url_for('user_login'))
        elif not check_password_hash(user.password, password):
            flash("Wrong password", category='error')
            return redirect(url_for('user_login'))
        else:
            login_user(user)
            return redirect(url_for('in_progress'))
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def user_logout():
    """Log user out"""
    logout_user()
    return render_template('index.html')


@app.route('/register', methods=["POST", "GET"])
def register_user():
    """Create new user account"""
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

        try:
            db.session.add(new_user)
            db.session.commit()
        except sqlalchemy.exc.IntegrityError:
            flash("That account already exists. Log in instead")
            return redirect(url_for('user_login'))
        else:
            return redirect(url_for('user_login'))

    return render_template('register.html', form=form)


@app.route('/book', methods=["POST", "GET"])
@login_required
def find_book():
    """Search for books matching user's search parameters"""
    data = request.form
    if request.method == "POST":
        title = data['book_needed']

        parameters = {
            "q": title,

        }

        response = requests.get("https://www.googleapis.com/books/v1/volumes", params=parameters)
        response.raise_for_status()
        book_data = response.json()
        print(book_data)
        try:
            book_list = book_data['items']
        except TypeError:
            return render_template('error.html')
        except KeyError:
            return render_template('error.html')
        else:
            return render_template('search.html', books=book_list)
    else:
        return render_template('index.html')


@app.route('/reading', methods=["POST", "GET"])
def in_progress():
    """Retrieves books currently being read by user"""
    all_books = Book.query.filter_by(category="In Progress").all()
    return render_template('read_in_progress.html', books=all_books, current_user=current_user)


# This route uses the book id to query the database to see if book has previously been added.
# If book is database with "In Progress" category, no action is needed
# If book is in database with any other category, update category to "In Progress"
# If book is not in database, add book.
@app.route('/add_read/<book_id>', methods=["POST", "GET"])
def add_in_progress(book_id):
    """Add book to database in progress category if not previously added"""
    book_in_db = Book.query.filter_by(book_id=f"{book_id}").first()
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
        new_book.user_id = current_user.id
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('in_progress'))
    elif book_in_db.category != "In Progress":
        book_in_db.category = "In Progress"
        db.session.commit()
        return redirect(url_for('in_progress'))
    elif book_in_db.user_id != current_user.id:  # add book to db if already in db under another user
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
        new_book.user_id = current_user.id
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('in_progress'))
    else:
        return redirect(url_for('in_progress'))


@app.route('/complete')
@login_required
def completed_reading():
    """Retrieves books that have been read by user"""
    all_books = Book.query.filter_by(category="Completed").all()
    return render_template('read_complete.html', books=all_books, current_user=current_user)


@app.route('/add_complete/<book_id>', methods=["POST", "GET"])
def add_completed_book(book_id):
    """Add book to database completed category if not previously added"""
    book_in_db = Book.query.filter_by(book_id=f"{book_id}").first()
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
        new_book.category = "Completed"
        new_book.user_id = current_user.id
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('completed_reading'))
    elif book_in_db.category != "Completed":
        book_in_db.category = "Completed"
        db.session.commit()
        return redirect(url_for('completed_reading'))
    elif book_in_db.user_id != current_user.id:  # add book to db if already in db under another user
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
        new_book.category = "Completed"
        new_book.user_id = current_user.id
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('completed_reading'))
    else:
        return redirect(url_for('completed_reading'))


@app.route('/future')
@login_required
def later_reading():
    """Retrieves books to be read later by user"""
    all_books = Book.query.filter_by(category="Read later").all()
    return render_template('read_later.html', books=all_books, current_user=current_user)


@app.route('/add_future/<book_id>', methods=["POST", "GET"])
def add_read_later(book_id):
    """Add book to database read later category if not previously added"""
    book_in_db = Book.query.filter_by(book_id=f"{book_id}").first()
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
        new_book.category = "Read later"
        new_book.user_id = current_user.id
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('later_reading'))
    elif book_in_db.category != "Read later":
        book_in_db.category = "Read later"
        db.session.commit()
        return redirect(url_for('later_reading'))
    elif book_in_db.user_id != current_user.id:  # add book to db if already in db under another user
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
        new_book.category = "Read later"
        new_book.user_id = current_user.id
        db.session.add(new_book)
        db.session.commit()
        return redirect(url_for('later_reading'))
    else:
        return redirect(url_for('later_reading'))


@app.errorhandler(500)
def page_not_found(e):
    """Error page"""
    return render_template('error.html'), 500


if __name__ == "__main__":
    app.run()
