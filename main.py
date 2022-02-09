from flask import Flask, render_template, request, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from forms import LoginForm, RegisterForm
import requests


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///books-tracker.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# Bootstrap(app)


# CREATE DATABASES
class User(UserMixin, db.Model):
    __tablename__ = "users_table"
    id = db.Column(db.Integer, primary_key=True)
    first = db.Column(db.String(250))
    last = db.Column(db.String(250))
    email = db.Column(db.String(250))
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
    # return render_template('read_later.html')
    return render_template('index.html')


@app.route('/login')
def login_user():
    return render_template('login.html')


@app.route('/logout')
def logout_user():
    return render_template('index.html')


@app.route('/register')
def register_user():
    form = RegisterForm()
    if form.validate_on_submit():
        new_user = User()
        new_user.first = form.firstName.data
        new_user.last = form.lastName.data
        new_user.email = form.email.data
        new_user.password = form.password.data

        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('read_in_progress.html'))

    return render_template('register.html')


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
    app.run(debug=True)
