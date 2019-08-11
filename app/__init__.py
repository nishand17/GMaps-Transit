from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
import os
from flask_admin.contrib.sqla import ModelView
from flask_admin import Admin
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_session import Session
from google.cloud import datastore

transit_agencies = {
'AC Transit': 'AC',
'AC': 'AC',
"http://www.actransit.org": 'AC',
"Bay Area Rapid Transit": 'BA',
"BART": 'BA',
"http://www.bart.gov": 'BA',
'Caltrain': 'CT',
"http://www.caltrain.com": "CT",
"County Connection": "CC",
"http://www.countyconnection.com/": "CC",
"Dumbarton Express Consortium": "DE",
"Dumbarton": "DE",
"Dumbarton Express": "DE",
"https://dumbartonexpress.com": "DE",
"Fairfield and Suisun Transit": "FS",
"FAST": "FS",
"http://www.fasttransit.org/": "FC",
"Golden Gate Transit": "GG",
"GG Transit": "GG",
"http://www.goldengate.org": "GG",
"Marin Transit": "MA",
"http://marintransit.org": "MA",
"Napa": "VN",
"Napa VINE": "VN",
"http://www.ridethevine.com/vine": "VN",
"San Francisco Municipal Transportation Agency": 'SF',
"SF Muni": "SF",
"Tri Delta Transit": "3D",
"http://trideltatransit.com": "3D",
"https://SFMTA.com": "SF",
"VTA": "SC",
"http://www.vta.org": "SC",
"WestCat (Western Contra Costa)": "WC",
"WestCAT": "WC",
"http://www.westcat.org/": "WC",
"Santa Rosa CityBus": "SR",
"SR CityBus": "SR",
"https://srcity.org/1036/Transit-and-CityBus": "SR"
}

app = Flask(__name__)

app.secret_key = 'A0Zr98j/3yX A~XHH!jmN]LWX/,?RT'
app.config['FLASK_ADMIN_SWATCH'] = 'cerulean'
app.config['CAPTCHA_ENABLE'] = True
app.config['CAPTCHA_NUMERIC_DIGITS'] = 5
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.config.from_object(Config)

captcha_key = '6LeMHJgUAAAAAFWg7lLpDhdnYLj-F4JE9jaR5BMv'
captcha_secret = '6LeMHJgUAAAAAEi5Sze6ieoUW14c4crEM-tHefcJ'

maps_key = "AIzaSyB_2x6LiC8Omy_NJrV06uO5zjwBSwfIZvQ"

key_511 = "0cffec6e-a59c-46ec-b804-c697b87e4c92"

db = SQLAlchemy(app)
migrate = Migrate(app, db)

login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.session_protection = "strong"

Session(app)

client = datastore.Client(project="lookingbus-transit-portal")

from app import routes, models

admin = Admin(app, name='lookingbus', template_mode='bootstrap3')
admin.add_view(ModelView(models.User, db.session))
