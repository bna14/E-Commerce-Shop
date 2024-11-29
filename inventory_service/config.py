# config.py

import os

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Database configuration
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'inventory.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Secret key for security purposes
    SECRET_KEY = 'your_secret_key'  # Replace with an actual secret key in production
