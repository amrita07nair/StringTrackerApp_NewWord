"""
Flask app logic for P1M3
"""
# pylint: disable=no-member
# pylint: disable=too-few-public-methods
import os
from flask_login.utils import _get_user
import requests
import time
import flask

from dotenv import load_dotenv, find_dotenv
from flask import Markup
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
from sqlalchemy import update

load_dotenv(find_dotenv())


app = flask.Flask(__name__, static_folder="./build/static")
# Point SQLAlchemy to your Heroku database
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL1")
# Gets rid of a warning
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.secret_key = os.getenv("SECRET_KEY")
uri = os.getenv("DATABASE_URL1")

# rest of connection code using the connection string `uri`
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


"""
Sessions:
- session_id (primary key)
- user_id (relationship with user table) - many:one (session:user)
- instrument_id (relationship with instrument table) -  many:one (session:instr)
- string_id (relationship with string table) - many:one (session:str) 
- playtime_mins (integer) 
- date (string)
"""


class Sessions(db.Model):
    session_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    user = db.relationship("User")
    instr_id = db.Column(db.Integer, db.ForeignKey("instruments.instr_id"))
    instrument = db.relationship("Instruments")
    string_id = db.Column(db.Integer, db.ForeignKey("strings.str_id"))
    string = db.relationship("Strings")
    playtime_mins = db.Column(db.Integer, nullable=False)
    date = db.Column(db.Integer, nullable=False)


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
    if email == "" or username == "" or password == "":  # if the form fields are empty
        signup_flash = Markup("Please fill in all account information.")
        return flask.render_template("signup.html", signup_flash=signup_flash)

    password_safe = password_meet_requirements(
        password
    )  # does password meet requrements? T or F?
    # email_ending_valid = check_email(email)
    email_validator_status = email_validator(email)
    print("PASSWORD TRIALS!!!")
    print(password_safe)
    print(email_validator_status)
    print(password)

    if password_safe and email_validator_status == "valid":
        user_byusername = get_user_by_username(username)
        user_byemail = get_user_by_email(email)
        if user_byusername:
            signup_flash = Markup(
                "Username taken. Please pick another username, or login with your existing account."
            )
            return flask.render_template("signup.html", signup_flash=signup_flash)

        elif user_byemail:
            signup_flash = Markup(
                "Email taken with account. Login with your existing account."
            )
            return flask.render_template("signup.html", signup_flash=signup_flash)

        else:
            user = User(email=email, username=username, password=password)
            db.session.add(user)
            db.session.commit()
            return flask.redirect(flask.url_for("login"))
    else:
        if password_safe == False:
            signup_flash = Markup(
                "Password not secure enough.<br>Password must meet the following requirements:<br>1. At least 1 special character:  ~`! @#$%^&*()_-+={[}]|\:;\"'<,>.?/ <br>2. Must contain both uppercase and lowercase letters.<br>3. Must be 8 characters or longer.<br>4. Must contain at least one number 0-9."
            )
            return flask.render_template("signup.html", signup_flash=signup_flash)
        elif email_validator_status == "invalid":
            signup_flash = Markup(
                "Your email could not be verified. Please enter a valid email address."
            )
            return flask.render_template("signup.html", signup_flash=signup_flash)


@app.route("/login")
def login():
    return flask.render_template("login.html")


@app.route("/login", methods=["POST"])
def login_post():
    email = flask.request.form.get("email")
    password = flask.request.form.get("password")
    user = get_user_by_email(email)
    user_exists = user_login_success(user, password)
    if user_exists:
        print(user_exists)
        print(user)
        login_user(user)
        print("DO WE GET HERE")
        # return flask.render_template("home.html") #manual patch to get to home, but anywhere @login_required is, it wont work
        return flask.redirect(flask.url_for("home"))
    else:
        flask.flash("Invalid email/password. Retry or Sigin Up.")
        return flask.redirect(flask.url_for("login"))


"""
NEW STUFF
"""


def get_user_by_username(username):
    user = User.query.filter_by(username=username).first()
    return user


def get_user_by_email(email):
    user = User.query.filter_by(email=email).first()
    return user


def user_login_success(user, password):
    if user and user.verify_password(password):
        print("USER IS VERIFIED")
        return True
    else:
        print("USER UNABLE TO BE VERIFIED")
        return False


def password_meet_requirements(password):
    contains_special_char = does_contains_special_char(password)
    contains_number = does_contains_number(password)
    mixed_case = is_mixed_case(password)
    if len(password) >= 8 and contains_special_char and contains_number and mixed_case:
        return True
    else:
        return False


def does_contains_special_char(password):
    if (
        ("!" in password)
        or ("@" in password)
        or ("~" in password)
        or ("#" in password)
        or ("$" in password)
        or ("%" in password)
        or ("^" in password)
        or ("^" in password)
        or ("&" in password)
        or ("*" in password)
        or ("(" in password)
        or (")" in password)
        or ("_" in password)
        or ("-" in password)
        or ("+" in password)
        or ("=" in password)
        or ("{" in password)
        or ("}" in password)
        or ("[" in password)
        or ("]" in password)
        or (":" in password)
        or (";" in password)
        or ("'" in password)
        or ('"' in password)
        or ("<" in password)
        or (">" in password)
        or ("," in password)
        or ("." in password)
        or ("?" in password)
        or ("/" in password)
    ):
        return True
    else:
        return False


def does_contains_number(password):
    if (
        ("0" in password)
        or ("1" in password)
        or ("2" in password)
        or ("3" in password)
        or ("4" in password)
        or ("5" in password)
        or ("6" in password)
        or ("7" in password)
        or ("8" in password)
        or ("9" in password)
    ):
        return True
    else:
        return False


def is_mixed_case(
    password,
):  # are there upper and lowercase letters? https://www.kite.com/python/answers/how-to-check-if-a-string-is-upper,-lower,-or-mixed-case-in-python
    if password.islower() or password.isupper():
        return False
    elif not password.islower() and not password.isupper():
        return True
    else:
        return False


def check_email(email):
    if (
        email.endswith("@gmail.com")
        or email.endswith("@yahoo.com")
        or email.endswith("@aol.com")
        or email.endswith("@hotmail.com")
    ):
        return True
    else:
        return False


def email_validator(email):
    email_valid_status = ""
    response = requests.get(
        "https://isitarealemail.com/api/email/validate", params={"email": email}
    )
    status = response.json()["status"]
    if status == "valid":
        email_valid_status = "valid"
    elif status == "invalid":
        email_valid_status = "invalid"
    else:
        email_valid_status = "invalid"
    return email_valid_status


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
    try:
        curr_instr_name = (
            Instruments.query.filter_by(instr_id=current_user.current_instr_id)
            .first()
            .instr_name
        )
    except AttributeError:
        curr_instr_name = ""

    try:
        curr_str_name = (
            Strings.query.filter_by(instr_id=current_user.current_instr_id)
            .first()
            .str_name
        )
    except AttributeError:
        curr_str_name = ""

    return flask.render_template(
        "home.html", curr_instr_name=curr_instr_name, curr_str_name=curr_str_name
    )


@app.route("/database", methods=["GET"])
@login_required
def database():
    print("Proc'ing database GET:")
    instr_names = getUserInstrumentNames()
    instr_names_len = int(len(instr_names))

    print("O_O")
    print(type(instr_names_len))

    str_names = getUserStringNames()
    str_names_len = int(len(str_names))

    try:
        curr_instr_name = (
            Instruments.query.filter_by(instr_id=current_user.current_instr_id)
            .first()
            .instr_name
        )
    except AttributeError:
        curr_instr_name = ""

    # get current string name
    try:
        curr_str_name = (
            Strings.query.filter_by(instr_id=current_user.current_instr_id)
            .first()
            .str_name
        )
    except AttributeError:
        curr_str_name = ""

    return flask.render_template(
        "database.html",
        curr_instr_name=curr_instr_name,
        instr_names=instr_names,
        instr_names_len=instr_names_len,
        str_names=str_names,
        str_names_len=str_names_len,
        curr_str_name=curr_str_name,
    )


def validate_new_instr_form(instr_name, instr_type):
    if instr_name != "" and instr_type != "":
        return True
    return False


@app.route("/database", methods=["POST"])
@login_required
def database_post():
    print("/database POST request received.")
    instr_type = flask.request.form.get("instr_type")
    instr_name = flask.request.form.get("instr_name")
    compound_name = getCompoundName(instr_name, instr_type)
    user_id = current_user.id

    # TODO: Add in form validation
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

    set_of_instr = current_user.instruments

    added_instr_id = 0
    for instr in set_of_instr:
        if instr.instr_name == instr_name:
            added_instr_id = instr.instr_id

    current_user.current_instr_id = added_instr_id

    db.session.add(current_user)
    db.session.commit()

    print(f"user1 is {current_user.id}")
    print(f"attached instrument id {current_user.current_instr_id}")

    instr_names = getUserInstrumentNames()
    instr_names_len = int(len(instr_names))

    str_names = getUserStringNames()
    str_names_len = int(len(str_names))

    try:
        curr_instr_name = (
            Instruments.query.filter_by(instr_id=current_user.current_instr_id)
            .first()
            .instr_name
        )
    except AttributeError:
        curr_instr_name = ""

    return flask.render_template(
        "database.html",
        instr_names=instr_names,
        instr_names_len=instr_names_len,
        curr_instr_name=curr_instr_name,
        str_names=str_names,
        str_names_len=str_names_len,
    )


@app.route("/addsession", methods=["POST"])
@login_required
def addsession_post():
    print("/addsession POST request received.")
    playtime_mins = flask.request.form.get("playmins")

    user_id = current_user.id

    # get current string id
    curr_instr_id = current_user.current_instr_id
    try:
        curr_string_id = Strings.query.filter_by(instr_id=curr_instr_id).first().str_id
    except AttributeError:
        curr_string_id = ""

    # TODO: add in form validation
    new_session = Sessions(
        user_id=user_id,
        instr_id=curr_instr_id,
        string_id=curr_string_id,
        playtime_mins=playtime_mins,
        date="12022021",  # TODO: get actual date
    )
    print(f"adding new session: {new_session} to DB")
    db.session.add(new_session)
    db.session.commit()

    try:
        curr_instr_name = (
            Instruments.query.filter_by(instr_id=current_user.current_instr_id)
            .first()
            .instr_name
        )
    except AttributeError:
        curr_instr_name = ""

    try:
        curr_str_name = (
            Strings.query.filter_by(instr_id=current_user.current_instr_id)
            .first()
            .str_name
        )
    except AttributeError:
        curr_str_name = ""

    return flask.render_template(
        "home.html", curr_instr_name=curr_instr_name, curr_str_name=curr_str_name
    )


@app.route("/analytics")
@login_required
def analytics():
    try:
        curr_instr_name = (
            Instruments.query.filter_by(instr_id=current_user.current_instr_id)
            .first()
            .instr_name
        )
    except AttributeError:
        curr_instr_name = ""

    # get current string
    curr_instr_id = current_user.current_instr_id
    try:
        curr_str = Strings.query.filter_by(instr_id=curr_instr_id).first()
    except AttributeError:
        curr_str = ""

    # get the id, name, cost of the current string
    try:
        curr_str_id = curr_str.str_id
        curr_str_name = curr_str.str_name
        curr_str_cost = curr_str.str_cost
    except AttributeError:
        curr_str_id = ""
        curr_str_name = ""
        curr_str_cost = 0

    # get all the sessions associated with our string

    print("do we get a string?????")
    print(curr_str)

    if curr_str == None:
        string_health = (3,)
        current_instr_name = ""
        current_str_name = ""
        total_playtime_hrs = 0
        avg_cost_hr = 0
    else:
        print("entering else")
        my_string_sessions = Sessions.query.filter_by(string_id=curr_str_id).all()
        # TODO:  get total_playtime
        total_playtime_mins = 0
        for session in my_string_sessions:
            total_playtime_mins = total_playtime_mins + session.playtime_mins

        total_playtime_hrs = total_playtime_mins / 60

        # TODO: Add this in for the color coding (string_health)
        avg_lifespan = 100
        string_life = 1 - (total_playtime_hrs / avg_lifespan)
        string_health = 100
        # when you have played more than 30% of the string's anticipated lifespan
        if string_life > 0.3:
            string_health = 3
        elif string_life > 0.10:
            string_health = 2
        else:
            string_health = 1

        # get cost per hour
        if total_playtime_hrs == 0:
            avg_cost_hr = 0
        else:
            avg_cost_hr = curr_str_cost / total_playtime_hrs

        total_playtime_hrs = round(total_playtime_hrs, 2)
        avg_cost_hr = round(avg_cost_hr, 2)

    return flask.render_template(
        "analytics.html",
        string_health=string_health,
        current_instr_name=curr_instr_name,
        current_str_name=curr_str_name,
        total_playtime_hrs=total_playtime_hrs,
        avg_cost_hr=avg_cost_hr,
    )


@app.route("/settings")
@login_required
def settings():
    # TODO: add code here
    return flask.render_template("settings.html")


def getCompoundName(instr_name, instr_type):
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


# Get string names using current user's instrument id
def getUserStringNames():
    set_of_str = Strings.query.filter_by(instr_id=current_user.current_instr_id)
    str_names = []
    for str in set_of_str:
        str_names.append(str.str_name)
    return str_names


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

    db.session.add(current_user)
    db.session.commit()

    str_names = getUserStringNames()
    str_names_len = int(len(str_names))

    print(f"Current user instrument changed to {current_user.current_instr_id}")
    return flask.render_template(
        "database.html",
        curr_instr_name=curr_instr_name,
        instr_names=instr_names,
        instr_names_len=instr_names_len,
        str_names=str_names,
        str_names_len=str_names_len,
    )


@app.route("/add_strings", methods=["POST"])
@login_required
def add_strings():
    print(f"add_strings post received")
    str_name = flask.request.form.get("str_name")
    str_cost = flask.request.form.get("str_cost")
    print(f"user is {current_user.id}")
    print(f"current instrument id {current_user.current_instr_id}")
    instr_id = current_user.current_instr_id
    new_strings = Strings(str_name=str_name, str_cost=str_cost, instr_id=instr_id)
    db.session.add(new_strings)
    db.session.commit()

    print(f"current strings for instr is {str_name}")
    return flask.redirect(flask.url_for("database"))


@app.route("/change_strings", methods=["POST"])
@login_required
def change_strings():
    print(f"change_strings post received")
    curr_str_name = flask.request.form.get("strings")

    str_names = getUserStringNames()
    str_names_len = int(len(str_names))
    instr_names = getUserInstrumentNames()
    instr_names_len = int(len(instr_names))

    try:
        curr_instr_name = (
            Instruments.query.filter_by(instr_id=current_user.current_instr_id)
            .first()
            .instr_name
        )
    except AttributeError:
        curr_instr_name = ""

    print(f"curr strings is {curr_str_name}")
    return flask.render_template(
        "database.html",
        curr_instr_name=curr_instr_name,
        curr_str_name=curr_str_name,
        str_names=str_names,
        str_names_len=str_names_len,
        instr_names=instr_names,
        instr_names_len=instr_names_len,
    )

@app.route("/profile")
@login_required
def profile():
    
    curr_username = User.get_username(current_user)
    curr_password = User.get_password(current_user)
    curr_email = User.get_email(current_user)

    return flask.render_template("profile.html", curr_username = curr_username, curr_email = curr_email, curr_password = curr_password)

@app.route("/changePassword", methods = ["POST"])
@login_required
def changePassword():
    curr_username = User.get_username(current_user)
    curr_password = User.get_password(current_user)
    curr_email = User.get_email(current_user)

    curr_pass = flask.request.form.get("curr_pass")
    new_pass = flask.request.form.get("new_pass")
    new_pass_confirm = flask.request.form.get("new_pass_confirm")
    print(curr_pass)
    print(new_pass)
    print(new_pass_confirm)
    print('HERE')

    new_pass_confirm_safe = password_meet_requirements(
        new_pass_confirm
    )
    new_pass_safe = password_meet_requirements(
        new_pass
    )

    update_statement = User.update()\
                       .where(User.c.username == curr_username)\
                       .values(password = new_pass)
    print(update_statement)

    #if (new_pass_safe and new_pass_confirm_safe) and new_pass == new_pass_confirm:
       
    
    return flask.render_template("profile.html", curr_username = curr_username, curr_email = curr_email, curr_password = curr_password)




if __name__ == "__main__":
    app.run(
        # debug = True
        host=os.getenv("IP", "0.0.0.0"),
        port=int(os.getenv("PORT", "8230")),
        debug=True,
    )
