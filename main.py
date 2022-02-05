from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap
import requests


app = Flask(__name__)
Bootstrap(app)


@app.route('/')
def home():
    return render_template('in_progress.html')


@app.route('/login')
def login_user():
    return render_template('login.html')


@app.route('/register')
def register_user():
    return render_template('register.html')


@app.route('/book', methods=["POST", "GET"])
def find_book():
    data = request.form
    if request.method == "POST":
        book_title = data['book_needed']
        print(book_title)

        parameters = {
            "q": "To kill a mockingbird",

        }

        response = requests.get("https://www.googleapis.com/books/v1/volumes", params=parameters)
        response.raise_for_status()
        book_data = response.json()
        book_list = book_data['items']

        return render_template('search.html', books=book_list)
    else:
        return render_template('index.html')



if __name__ == "__main__":
    app.run(debug=True)
