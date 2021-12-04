

# Purpose
    The purpose of our app is to help string musicians know when to change their strings on their instrument. The last thing a musiician wants is to be playing and a string breaks because it is very worn out. We designed an app that allows users to sign up/ login to a personal account and save their instruments and what strings are attached to that instrument. Once they have instruments and strings saved they are able to record how much time they play that instrument. This will then save your total playtime on that set of strings to our databes. You will then be able to see how much longer you will be able to use this set of strings before you are in risk of a string breaking.

## Requirements

1. Flask
2. requests
3. python-dotenv
4. Flask-Login
5. psycopg2-binary
6. Flask-SQLAlchemy
7. Werkzeng==2.0.2

## Run Application

1. Install all of the requirements above.
2. Create a heroku account if you don't already have one.
3. Create a heroku database in the terminal:
    -heroku create 
    -heroku addons:create heroku-postgresql:hobby-dev -a "Name of heroku app"
    -heroku config -a "Name of heroku app"
4. Create a .env file and copy the database URL and put it in the .env in this format
    - export DATABASE_URL1 = "Paste URL here"
5. Finally run the app
    - python3 app.py

## Issues
CI and unit tests are working however they are failing due to linting