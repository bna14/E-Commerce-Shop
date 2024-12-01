# config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Database configuration (using SQLite for simplicity)
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'sales.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'your_secret_key'  # Replace with an actual secret key in production
