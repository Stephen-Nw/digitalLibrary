from flask import Flask, render_template, request, redirect, url_for, flash
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
    book_id = db.Column(db.String(250), unique=True, nullable=False)
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
            return redirect(url_for('in_progress'))
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
            new_user.password = generate_password_hash(form.password.data, rounds=12)
        else:
            flash("Passwords do not match!!")
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
        book_title = data['book_needed']
        print(book_title)

        parameters = {
            "q": book_title,

        }

        response = requests.get("https://www.googleapis.com/books/v1/volumes", params=parameters)
        response.raise_for_status()
        book_data = response.json()
        book_list = book_data['items']

        return render_template('search.html', books=book_list)
    else:
        return render_template('index.html')


@app.route('/reading')
def in_progress():
    """Retrieves books currently being read by user"""
    return render_template('read_in_progress.html')


@app.route('/complete')
def completed_reading():
    """Retrieves books that have been read by user"""
    return render_template('read_complete.html')


@app.route('/future')
def later_reading():
    """Retrieves books to be read later by user"""
    return render_template('read_later.html')







if __name__ == "__main__":
    app.run()
