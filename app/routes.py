from app import app, db, captcha_secret, client, transit_agencies
from flask import render_template, session, request, jsonify, abort, redirect, url_for, flash
from config import Auth
from authlib.client import OAuth2Session
from flask_login import login_required, current_user, login_user, logout_user
from .models import User
import requests
from functools import wraps
import json
from google.cloud import datastore

def get_google_auth(state=None, token=None):
    if token:
        return OAuth2Session(Auth.CLIENT_ID, token=token)
    if state:
        return OAuth2Session(
            Auth.CLIENT_ID,
            redirect_uri=Auth.REDIRECT_URI)
    oauth = OAuth2Session(
        Auth.CLIENT_ID,
        redirect_uri=Auth.REDIRECT_URI,
        scope=Auth.SCOPE)
    return oauth

def check_recaptcha(f):
    """
    Checks Google reCAPTCHA.

    :param f: view function
    :return: Function
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request.recaptcha_is_valid = None

        if request.method == 'POST':
            data = {
                'secret': captcha_secret,
                'response': request.form.get('g-recaptcha-response'),
                'remoteip': request.access_route[0]
            }
            r = requests.post(
                "https://www.google.com/recaptcha/api/siteverify",
                data=data
            )
            result = r.json()

            if result['success']:
                request.recaptcha_is_valid = True
            else:
                request.recaptcha_is_valid = False
                flash('Invalid reCAPTCHA. Please try again.', 'error')

        return f(*args, **kwargs)

    return decorated_function


@app.route('/address', methods=['POST'])
@login_required
def address():
    if not request.form or not request.form['originAddress']:
        abort(404)

    originAddress = request.form['originAddress']
    destinationAddress = request.form['destAddress']

    origin_url = '+'.join(originAddress.split(' '))
    dest_url = '+'.join(destinationAddress.split(' '))
    google_url = "https://maps.googleapis.com/maps/api/directions/json?origin={0}&destination={1}&mode=transit&transit_mode=bus&transit_routing_preference=fewer_transfers&key=AIzaSyB_2x6LiC8Omy_NJrV06uO5zjwBSwfIZvQ".format(origin_url, dest_url)

    google_response = requests.post(google_url).json()
    google_route_steps = google_response['routes'][0]['legs'][0]['steps']

    bus_step = [step for step in google_route_steps if step['travel_mode'] == 'TRANSIT']

    if len(bus_step) < 1:
        print('No bus needed')
        # No bus - Use route_steps first location for lat/lon
        no_bus_lat = google_route_steps[0]['start_location']['lat']
        no_bus_lon = google_route_steps[0]['start_location']['lng']
        return render_template('directions.html', map_lat=no_bus_lat, map_lon=no_bus_lon, origin=originAddress, dest=destinationAddress, dest_lat=no_bus_lat, dest_lon=no_bus_lon)

    bus_step = bus_step[0]

    map_lat, map_lon = bus_step['start_location']['lat'], bus_step['start_location']['lng']
    dest_lat = google_route_steps[-1]['end_location']['lat']
    dest_lon = google_route_steps[-1]['end_location']['lng']
    transit_details = bus_step['transit_details']
    arrival_stop, departure_stop = transit_details['arrival_stop']['name'], transit_details['departure_stop']['name']

    line = transit_details['line']
    agency_name, bus_name, agency_site = line['agencies'][0]['name'], line['short_name'], line['agencies'][0]['url']

    name_511 = transit_agencies.get(agency_name, None) or transit_agencies.get(agency_site, None)

    bus_lat, bus_lon = bus_step['start_location']['lat'], bus_step['start_location']['lng']

    if name_511:
        print('found bus')
        url_511 = "http://api.511.org/transit/VehicleMonitoring?format=json&api_key=0cffec6e-a59c-46ec-b804-c697b87e4c92&agency={0}".format(name_511)
        response_511 = requests.get(url_511)
        json_511 = json.loads(response_511.text.encode().decode("utf-8-sig"))
        json_511 = json_511['Siri']['ServiceDelivery']['VehicleMonitoringDelivery']['VehicleActivity']
        bus_lines = []
        for activity in json_511:
            bus_lines.append(str(activity['MonitoredVehicleJourney']['LineRef']))
        if str(bus_name) in bus_lines:
            print('bus line available')
            possible_buses = [x['MonitoredVehicleJourney'] for x in json_511 if str(x['MonitoredVehicleJourney']['LineRef']) == bus_name]
            bus_lat, bus_lon = possible_buses[0]['VehicleLocation']['Latitude'], possible_buses[0]['VehicleLocation']['Longitude']

        # get bus coords

    return render_template('directions.html', dest_lat=dest_lat, dest_lon=dest_lon, bus_lat = bus_lat, bus_lon= bus_lon, map_lat=map_lat, map_lon=map_lon, origin=originAddress, dest=destinationAddress)

@app.route('/', methods=['POST', 'GET'])
@app.route('/index', methods=['POST', 'GET'])
@login_required
@check_recaptcha
def index():
    if request.method == 'POST' and request.recaptcha_is_valid:
        current_user.username = request.form['captcha']
        entity = datastore.Entity(key=client.key('User', current_user.username))
        entity.update({
            'username': current_user.username,
            'Name': current_user.name,
            'email': current_user.email,
        })
        client.put(entity)
    return render_template('index.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/login')
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    google = get_google_auth()
    auth_url, state = google.authorization_url(
        Auth.AUTH_URI, access_type='offline')
    session['oauth_state'] = state
    session.modified=True
    return render_template('login.html', auth_url=auth_url)

@app.route('/username')
@login_required
def username():
    return render_template('username.html', default=extract_username(current_user.email))

def extract_username(email):
    if '@' not in email:
        return ''
    return email[:email.index('@')]

@app.route('/gCallback')
def callback():
    # Redirect user to home page if already logged in.
    if current_user is not None and current_user.is_authenticated:
        return redirect(url_for('index'))
    if 'error' in request.args:
        if request.args.get('error') == 'access_denied':
            return 'You denied access.'
        return 'Error encountered.'
    if 'code' not in request.args and 'state' not in request.args:
        return redirect(url_for('login'))
    else:
        # Execution reaches here when user has
        # successfully authenticated our app.
        print('session', session.values())
        google = get_google_auth(state=True)
        try:
            token = google.fetch_token(
                Auth.TOKEN_URI,
                client_secret=Auth.CLIENT_SECRET,
                authorization_response=request.url)
        except HTTPError:
            return 'HTTPError occurred.'
        google = get_google_auth(token=token)
        resp = google.get(Auth.USER_INFO)
        if resp.status_code == 200:
            user_data = resp.json()
            print(resp.json())
            email = user_data['email']
            user = User.query.filter_by(email=email).first()

            new_user = False

            if user is None:
                user = User()
                user.email = email
                new_user = True
            user.name = user_data['name']
            user.tokens = json.dumps(token)
            user.avatar = user_data['picture']
            user.username = extract_username(email)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            if new_user:
                return redirect(url_for('username'))
            return redirect(url_for('index'))
        return 'Could not fetch your information.'
