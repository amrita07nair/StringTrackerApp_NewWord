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
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
# Gets rid of a warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = "I am a secret key"
uri = os.getenv("DATABASE_URL")
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
    instruments = db.relationship("Instruments", backref="user", lazy=True)
    current_instr_id = db.Column(db.Integer, nullable=True)
    str_lifespans = db.relationship("Stringlifespans", backref="user", lazy=True)

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
    """
    string_lifespans = db.Column(db.String(65535), nullable=False)


db.create_all()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_name):
    """
    Required by flask_login
    """
    return get_user_by_username(user_name)


@app.route("/logout")
@login_required
def logout():
    print("Logging out user")
    logout_user()
    return flask.redirect(flask.url_for("login"))


@app.route("/signup")
def signup():
    print("proc'ing signup()")
    """
    Signup endpoint for GET requests
    """
    return flask.render_template("signup.html")


@app.route("/signup", methods=["POST"])
def signup_post():
    print("proc'ing signup_post()")
    """
    Handler for signup form data
    """
    email = flask.request.form.get("email")
    username = flask.request.form.get("username")
    password = flask.request.form.get("password")
    user = get_user_by_username(username)
    if user:
        return flask.redirect(flask.url_for("login"))
    else:
        user = User(email=email, username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return flask.redirect(flask.url_for("login"))


def get_user_by_username(username):
    user = User.query.filter_by(username=username).first()
    return user


@app.route("/login")
def login():
    """
    Login endpoint for GET requests
    """
    print("proc'ing login()")
    return flask.render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    """
    Handler for login form data
    """
    print("proc'ing login_post()")
    email = flask.request.form.get("email")
    password = flask.request.form.get("password")
    user = get_user_by_email(email)
    if user_login_success(user, password):
        print("user_login_success")
        login_user(user)
        print(f"current user username = {current_user.username}")
        return flask.render_template("home.html")
    return flask.render_template("login.html")


def get_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    return user


def user_login_success(user, password):
    if user and user.verify_password(password):
        return True
    return False


@app.route("/")
def main():
    """
    Main page just reroutes to index or login depending on whether the
    user is authenticated
    """
    print("proc'ing main()")
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
    print("proc'ing home()")
    return flask.render_template("home.html")


@app.route("/database", methods=["GET"])
@login_required
def database():
    print("Proc'ing database GET:")
    instr_names = getUserInstrumentNames()
    instr_names_len = int(len(instr_names))

    curr_instr_name = get_current_instr_name()

    return flask.render_template(
        "database.html",
        curr_instr_name=curr_instr_name,
        instr_names=instr_names,
        instr_names_len=instr_names_len,
    )


@app.route("/database", methods=["POST"])
@login_required
def database_post():
    print("/database POST request received.")
    instr_type = flask.request.form.get("instr_type")
    instr_name = flask.request.form.get("instr_name")
    compound_name = get_compound_name(instr_name, instr_type)
    user_id = current_user.id
    is_valid = validate_new_instr_form(instr_name, instr_type)

    if not is_valid:
        # TODO: Return to database.HTML and don't add to DB
        print("Implement this")

    new_instr = Instruments(
        compound_name=compound_name,
        user_id=user_id,
        instr_name=instr_name,
        instr_type=instr_type,
    )
    print(f"Adding {new_instr} to DB.")
    db.session.add(new_instr)
    db.session.commit()

    # we assume that the newly added instrument is the user's new current instrument, so we attach it to user's profile
    set_of_instr = current_user.instruments

    added_instr_id = 0
    for instr in set_of_instr:
        if instr.instr_name == instr_name:
            added_instr_id = instr.instr_id

    current_user.current_instr_id = added_instr_id

    instr_names = getUserInstrumentNames()
    instr_names_len = int(len(instr_names))

    curr_instr_name = get_current_instr_name()

    return flask.render_template(
        "database.html",
        curr_instr_name=curr_instr_name,
        instr_names=instr_names,
        instr_names_len=instr_names_len,
    )


def validate_new_instr_form(instr_name, instr_type):
    if instr_name != "" and instr_type != "":
        return True
    return False


def get_current_instr_name():
    try:
        curr_instr_name = (
            Instruments.query.filter_by(instr_id=current_user.current_instr_id)
            .first()
            .instr_name
        )
    except AttributeError:
        curr_instr_name = ""
    return curr_instr_name


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


def get_compound_name(instr_name, instr_type):
    return f"{instr_name} - {instr_type}"


def getUserInstrumentNames():
    set_of_instr = current_user.instruments
    instr_names = []
    for instr in set_of_instr:
        instr_names.append(instr.instr_name)
    return instr_names


# Get instrument ID using user ID and instrument name
def getCurrentInstrument(curr_instr_name):
    curr_instr_db_obj = (
        Instruments.query.filter_by(user_id=current_user.id)
        .filter_by(instr_name=curr_instr_name)
        .first()
    )
    return curr_instr_db_obj


@app.route("/changeinstr", methods=["POST"])
@login_required
def change_instr():
    print("/changeinstr received POST request.")
    curr_instr_name = flask.request.form.get("instruments")

    # get the current instrument's ID
    curr_instr_db_obj = getCurrentInstrument(curr_instr_name)
    curr_instr_id = curr_instr_db_obj.instr_id

    # attach this instr_id to the user's current_instr_id
    current_user.current_instr_id = curr_instr_id
    instr_names = getUserInstrumentNames()
    instr_names_len = int(len(instr_names))

    print(f"Current user instrument changed to {current_user.current_instr_id}")
    return flask.render_template(
        "database.html",
        curr_instr_name=curr_instr_name,
        instr_names=instr_names,
        instr_names_len=instr_names_len,
    )


if __name__ == "__main__":
    app.run(
        # debug = True
        host=os.getenv("IP", "0.0.0.0"),
        port=int(os.getenv("PORT", "8230")),
        debug=True,
    )
# up til here username and routing works. time to implement password from here. HTML hasnt broken anything
# adding password to db.columns and seeing if they breakes anything
# added in db column for password and hardcoded filler password to test if db will accept new column
# basic password stuff working!!!!!!!! now polish and add flask.flask or jsonify :)
