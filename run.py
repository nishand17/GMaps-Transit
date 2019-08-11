from app import app
from werkzeug.serving import make_ssl_devcert
import os

make_ssl_devcert('./ssl', host='localhost')
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

app.run(debug=True, ssl_context=('./ssl.crt', './ssl.key'))
