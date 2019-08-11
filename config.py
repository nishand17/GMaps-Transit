import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config(object):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True

class Auth:
    CLIENT_ID = ('641429306273-sod4okj7q65fjpr46re812aj2n4fh3tk.apps.googleusercontent.com')
    CLIENT_SECRET = 'U2I9qJnqUCWGnMpELwdJua1A'
    REDIRECT_URI = 'https://localhost:5000/gCallback'
    AUTH_URI = 'https://accounts.google.com/o/oauth2/auth'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'
    USER_INFO = 'https://www.googleapis.com/userinfo/v2/me'
    SCOPE = ['profile', 'email']
    CAPTCHA_ENABLE = True
    CAPTCHA_NUMERIC_DIGITS = 5
    SESSION_TYPE = 'sqlalchemy'
