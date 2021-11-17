"""
Flask app logic for P1M3
"""
# pylint: disable=no-member
# pylint: disable=too-few-public-methods
from enum import unique
import os
import json
import random

import flask

from dotenv import load_dotenv, find_dotenv
from flask_login import logout_user
from flask_login import (
    login_user,
    current_user,
    LoginManager,
    UserMixin,
    login_required,
)
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


load_dotenv(find_dotenv())

app = flask.Flask(__name__, static_folder="./build/static")
# Point SQLAlchemy to your Heroku database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL1")
# Gets rid of a warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "I am a secret key"
uri = os.getenv("DATABASE_URL1")
db = SQLAlchemy(app)

# first connect Heroku Postgres to SQLAlchemy
# https://help.heroku.com/ZKNTJQSK/why-is-sqlalchemy-1-4-x-not-connecting-to-heroku-postgres


class User(UserMixin, db.Model):
    """
    Model for a) User rows in the DB and b) Flask Login object
    """

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(1000), unique=True, nullable=False)
    username = db.Column(db.String(1000), unique=True, nullable=False)
    password = db.Column(db.String(1000))

    def __init__(self, email, username, password):
        self.email = email
        self.username = username
        self.password = generate_password_hash(password)

    def __repr__(self):
        """
        Determines what happens when we print an instance of the class
        """
        return f"<User {self.email}, {self.username}>"

    def get_email(self):
        return self.email

    def get_username(self):
        """
        Getter for username attribute
        """
        return self.username

    def get_password(self):

        return self.password

    def verify_password(self, password):
        return check_password_hash(self.password, password)


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


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return flask.redirect(flask.url_for("login"))


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
    email = flask.request.form.get("email")
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    user = User.query.filter_by(username=username).first()
    if user:
        return flask.redirect(flask.url_for("login"))
    else:
        user = User(email=email, username=username, password=password)
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
    email = flask.request.form.get("email")
    password = flask.request.form.get("password")
    user = User.query.filter_by(email=email).first()
    if user and user.verify_password(password):
        login_user(user)
        return flask.redirect(flask.url_for("home"))
    return flask.render_template("login.html")


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


@app.route("/database", methods=["GET"])
@login_required
def database():
    # TODO: add code here
    return flask.render_template("database.html")


"""
@app.route("/database", methods=["POST"])
@login_required
def database_post():
    print("/database POST request received.")
    instr_type = flask.request.form.get("instr_type")
    instr_name = flask.request.form.get("instr_name")
    compound_name = getCompoundName(instr_name, instr_type)
    user_id = current_user.id
    # TODO: Add in form validation
    new_instr = Instruments(
        compound_name=compound_name,
        user_id=user_id,
        instr_name=instr_name,
        instr_type=instr_type,
    )
    print(f"Adding {new_instr} to DB.")
    db.session.add(new_instr)
    db.session.commit()
    return flask.render_template("database.html")
"""


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


def getCompoundName(instr_name, instr_type):
    return f"{instr_name} - {instr_type}"


if __name__ == "__main__":
    app.run(
        # debug = True
        host=os.getenv("IP", "0.0.0.0"),
        port=int(os.getenv("PORT", "8233")),
        debug=True,
    )
# up til here username and routing works. time to implement password from here. HTML hasnt broken anything
# adding password to db.columns and seeing if they breakes anything
# added in db column for password and hardcoded filler password to test if db will accept new column
# basic password stuff working!!!!!!!! now polish and add flask.flask or jsonify :)
# appworks with email addition (works like how un ans password but with new 3rd field)
# TODO: implement hash for password --> implement flask flash --> implement password restrictions(min 8 characters, needs at least 1 number and 1 special character) --> implement email restrictions (needs an @ and ends with gmail.com/yahoo.com/aol.com/hotmail.com) --> spruce up html with instructions and bootstrap
