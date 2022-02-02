from flask import Flask, render_template, request
from flask_bootstrap import Bootstrap


app = Flask(__name__)
Bootstrap(app)


@app.route('/')
def home():
    return render_template('base.html')


@app.route('/login')
def login_user():
    return render_template('login.html')


@app.route('/register')
def register_user():
    return render_template('register.html')

@app.route('/book')
def find_book():
    data = request.form
    return render_template('index.html')



if __name__ == "__main__":
    app.run(debug=True)
