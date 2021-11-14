"""
Flask app logic for P1M3
"""
#trial commit/push

# pylint: disable=no-member
# pylint: disable=too-few-public-methods
import os
import json
import random

import flask

from dotenv import load_dotenv, find_dotenv
from flask_login import (
    login_user,
    current_user,
    LoginManager,
    UserMixin,
    login_required,
    logout_user
)
from flask_sqlalchemy import SQLAlchemy

load_dotenv(find_dotenv())

app = flask.Flask(__name__, static_folder="./build/static")
# Point SQLAlchemy to your Heroku database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL1")
# Gets rid of a warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = b"I am a secret key"

db = SQLAlchemy(app)

# first connect Heroku Postgres to SQLAlchemy
# https://help.heroku.com/ZKNTJQSK/why-is-sqlalchemy-1-4-x-not-connecting-to-heroku-postgres
uri = os.getenv("DATABASE_URL1")

# rest of connection code using the connection string `uri`

class User(UserMixin, db.Model):
    """
    Model for a) User rows in the DB and b) Flask Login object
    """

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), unique=False, nullable=False)
    #instruments = db.relationship("Instruments", backref="user", lazy=True)
    #str_lifespans = db.relationship("Stringlifespans", backref="user", lazy=True)

    def __repr__(self):
        """
        Determines what happens when we print an instance of the class
        """
        return f"<User {self.username, self.password}>"

    def get_username(self):
        """
        Getter for username attribute
        """
        return self.username
    
    def get_password(self):
        return self.password

class Instruments(db.Model):
    # TODO: Should instr_id be a compound, like Type:Name, or just an int?
    instr_id = db.Column(db.Integer, primary_key=True)
    compound_name = db.Column(db.String(240), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    strings = db.relationship("Strings", backref="user", lazy=True)
    instr_name = db.Column(db.String(120), nullable=False)
    instr_type = db.Column(db.String(120), nullable=False)


class Strings(db.Model):
    str_id = db.Column(db.Integer, primary_key=True)
    instr_id = db.Column(
        db.Integer, db.ForeignKey("instruments.instr_id"), nullable=False
    )
    str_name = db.Column(db.String(120), nullable=False)
    str_cost = db.Column(db.Integer, nullable=False)


class Stringlifespans(db.Model):
    str_lifespan_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    # string_lifespans is a JSON object stored as a string
    """
    Ex:
        - {
            "Guitar A - String B": [80, 90], 
            "Guitar B - String C": [100, 120, 130],
            }
    
    string_lifespans = db.Column(db.String(65535), nullable=False
    """

db.create_all()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_name):
    """
    Required by flask_login
    """
    return User.query.get(user_name)


@app.route("/index")
@login_required
def index():
    """
    Main page. Fetches song data and embeds it in the returned HTML. Returns
    dummy data if something goes wrong.
    """
    return flask.render_template("index.html")


@app.route("/signup")
def signup():
    """
    Signup endpoint for GET requests
    """
    return flask.render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup_post():
    """
    Handler for signup form data
    """
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    user = User.query.filter_by(username=username).first()
    if user:
        return flask.jsonify({"status": 400, "reason": "Username is already in use. Try something different."})
    else:
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

    return flask.redirect(flask.url_for("login"))


@app.route("/login")
def login():
    """
    Login endpoint for GET requests
    """
    return flask.render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    """
    Handler for login form data
    """
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    user = User.query.filter_by(username=username).first()
    if user:
        if user.password == password:
            login_user(user)
            return flask.redirect(flask.url_for("home"))
        else:
            return flask.jsonify({"status": 401, "reason": "Username or Password Error"})

    return flask.jsonify({"status": 401, "reason": "Username or Password Error"})

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for("login"))

@app.route("/")
def main():
    """
    Main page just reroutes to index or login depending on whether the
    user is authenticated
    """
    if current_user.is_authenticated:
        return flask.redirect(flask.url_for("home"))
    return flask.redirect(flask.url_for("login"))


"""
Code for String Squad's HTML:
"""


@app.route("/home")
@login_required
def home():
    # TODO: add code here
    return flask.render_template("home.html")


@app.route("/database")
@login_required
def database():
    # TODO: add code here
    return flask.render_template("database.html")


@app.route("/analytics")
@login_required
def analytics():
    # TODO: add code here
    return flask.render_template("analytics.html")


@app.route("/settings")
@login_required
def settings():
    # TODO: add code here
    return flask.render_template("settings.html")


if __name__ == "__main__":
    app.run(
        #debug = True
        host=os.getenv("IP", "0.0.0.0"),
        port=int(os.getenv("PORT", "8228")),
    )
