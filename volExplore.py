from flask import Flask, jsonify, request, render_template, flash, redirect, url_for, session
from flask_session import Session
from geojson import Point
from flask_pymongo import PyMongo
from bson.json_util import dumps
import json
from pymongo import MongoClient, GEOSPHERE
from constants import RADIANS_METERS_COEFFICIENT
import custom_query as cQ
import datetime
from ast import literal_eval
import utils as U
import bcrypt

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/volExploreDB"
mongo = PyMongo(app)

app.secret_key = ['SECRET_KEY']

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client.volExploreDB
# Collection connections
comment_collection = db.Comments
poi_collection = db.POI
SNW_edges = db.Street_Network_Edges
SNW_nodes = db.Street_Network_Nodes
users = db.Users

# Homepage
@app.route('/')
@app.route('/start_page', methods=['GET', 'POST'])
def start_page():
    if request.method == 'POST':
        name = request.form.get('name')
        details = request.form.get('details')
        flag = int(request.form.get('flag'))
        if flag:
            typePOI = request.form.get('poiType')
            coords = literal_eval(request.form.get('givenCoords'))
            # New POI is added to the database
            cQ.insertPOI(poi_collection, typePOI, name, details, coords)
        else:
            poid = request.form.get('poid')
            # POI is updated in the database
            cQ.updatePOI(poi_collection, poid, name, details)
        flash('Changes in Point of Interest successful', 'info')
    return render_template('home.html')

# Registration page
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']

        # Usernames must be unique
        if users.find_one({'username': username}):
            flash(username + ' already exists as a username', 'warning')
        else:
            encPass = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(14))
            users.insert_one({'username': username, 'password': encPass.decode('utf-8'), 'email': email, 'adminStatus': False})
            flash('You have been registered successfully. You can now log in', 'success')
            return redirect(url_for('login'))
        
    return render_template('register.html')

# Login page
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        login_user = users.find_one({'username': username})

        # Check if user info is valid
        if login_user:
            logpass = password.encode('utf-8')
            if bcrypt.checkpw(logpass, login_user['password'].encode('utf-8')):
                session['username'] = username
                if login_user['adminStatus']:
                    session['admin'] = True
                flash('Log in successful', 'success')
                return redirect(url_for('start_page'))
            
        flash('Username and Password combination is wrong', 'error')

    return render_template('login.html')

# Removes user info from session, logging them out and redirecting them to the homepage
@app.route('/logout')
def logout():
    session.pop('username', None)
    if 'admin' in session:
        session.pop('admin', None)
    flash('Log out completed', 'success')
    return redirect(url_for('start_page'))

# Searh POI in Radius page
@app.route('/point_search', methods=['GET'])
def point_search():
    return render_template('point_search.html')

# Search Route with POI page
@app.route('/route_search', methods=['GET'])
def route_search():
    return render_template('route_search.html')

# Page that displays the query results for POI search
@app.route('/point_result', methods=['GET', 'POST'])
def point_result():
    distance = float(request.args.get('distance')) * RADIANS_METERS_COEFFICIENT
    lat = float(request.args.get('lat'))
    lng = float(request.args.get('lng'))
    type_filter = []

    if request.args.get('all_chk'):
        type_filter.extend(["Archaeological_Site", "Arts_Centre", "Castle", "Fountain", "Garden", "Historic", "Memorial", "Museum", "Park", "Playground", "Recreational_Ground", "Tourist_Attraction", "Viewpoint"])
        # query mongoDB
    else:
        if request.args.get('arch_chk'):
            type_filter.append("Archaeological_Site")

        if request.args.get('art_chk'):
            type_filter.append("Arts_Centre")

        if request.args.get('castle_chk'):
            type_filter.append("Castle")

        if request.args.get('fountain_chk'):
            type_filter.append("Fountain")

        if request.args.get('gardn_chk'):
            type_filter.append("Garden")

        if request.args.get('hist_chk'):
            type_filter.append("Historic")

        if request.args.get('memo_chk'):
            type_filter.append("Memorial")

        if request.args.get('museum_chk'):
            type_filter.append("Museum")

        if request.args.get('prk_chk'):
            type_filter.append("Park")

        if request.args.get('playgrnd_chk'):
            type_filter.append("Playground")

        if request.args.get('rec_chk'):
            type_filter.append("Recreational_Ground")

        if request.args.get('trst_chk'):
            type_filter.append("Tourist_Attraction")

        if request.args.get('vp_check'):
            type_filter.append("Viewpoint")
        
    qResult = cQ.pointQ(poi_collection, type_filter, lat, lng, distance)

    return render_template('point_result.html', backend_data=qResult)

# Page that displays the results for route search
@app.route('/route_result')
def route_result():
    sp_lat = float(request.args.get('sp_lat'))
    sp_lng = float(request.args.get('sp_lng'))
    ep_lat = float(request.args.get('ep_lat'))
    ep_lng = float(request.args.get('ep_lng'))

    centreLat, centreLng, radius = U.centreQ(sp_lat, sp_lng, ep_lat, ep_lng)

    if radius*2 >= 2000:
        flash('Please select a destination that is closer to the starting point', 'warning')
        return redirect(url_for('route_search'))
    
    type_filter = []

    if request.args.get('all_chk'):
        type_filter.extend(["Archaeological_Site", "Arts_Centre", "Castle", "Fountain", "Garden", "Historic", "Memorial", "Museum", "Park", "Playground", "Recreational_Ground", "Tourist_Attraction", "Viewpoint"])
        # query mongoDB
    else:
        if request.args.get('arch_chk'):
            type_filter.append("Archaeological_Site")

        if request.args.get('art_chk'):
            type_filter.append("Arts_Centre")

        if request.args.get('castle_chk'):
            type_filter.append("Castle")

        if request.args.get('fountain_chk'):
            type_filter.append("Fountain")

        if request.args.get('gardn_chk'):
            type_filter.append("Garden")

        if request.args.get('hist_chk'):
            type_filter.append("Historic")

        if request.args.get('memo_chk'):
            type_filter.append("Memorial")

        if request.args.get('museum_chk'):
            type_filter.append("Museum")

        if request.args.get('prk_chk'):
            type_filter.append("Park")

        if request.args.get('playgrnd_chk'):
            type_filter.append("Playground")

        if request.args.get('rec_chk'):
            type_filter.append("Recreational_Ground")

        if request.args.get('trst_chk'):
            type_filter.append("Tourist_Attraction")

        if request.args.get('vp_check'):
            type_filter.append("Viewpoint")

    qResult = cQ.pointQ(poi_collection, type_filter, centreLat, centreLng, radius * RADIANS_METERS_COEFFICIENT)

    distance, route_res = cQ.NEWcalc_path(SNW_edges, SNW_nodes, sp_lat, sp_lng, ep_lat, ep_lng, centreLat, centreLng, radius, qResult)
    time_sec = distance/1.5
    time_min = time_sec//60
    return render_template('route_result.html', POI = qResult, route_dist = round(distance), time = time_min, route = route_res, lat = centreLat, lng = centreLng, radius = radius)

# when the "show comments" button is pressed, fetch all the appropraite comments from database and display them
@app.route('/showComments', methods=['GET', 'POST'])
def showComments():
    data = request.get_json()
    print(data)
    if 'Comment' in data:
        cQ.addComment(comment_collection, data['POID'], data['Comment'], session['username'])
    #make query to fetch all comments
    comments = cQ.selectComments(comment_collection, data['POID'])
    if not comments:
        comments = {"empty": 0}
    return jsonify(comments)

# Admin only visible page, when "is there something missing?" button is pressed
@app.route('/addinfo')
def addinfo():
    return render_template('addinfo.html')

# Page only visible to admin, to check whether POI already exists or not
@app.route('/checkPOI', methods=['GET', 'POST'])
def checkPOI():
    coordinatesLatStr = request.form.get('coordsLat').split(',')
    coordinatesLngStr = request.form.get('coordsLng').split(',')
    POIfilter = request.form.get('poiType')
    
    coords = []
    for i, coordSet in enumerate(coordinatesLatStr):
        coords.insert(i, [float(coordinatesLngStr[i]), float(coordinatesLatStr[i])])
    if len(coords) != 1:
        coords.insert(len(coords), coords[0])
    qResult = cQ.fetchPOI(poi_collection, [POIfilter], coords, 100 * RADIANS_METERS_COEFFICIENT)

    return render_template('checkPOI.html', poi = qResult, inputCoord = coords, POIfilter = POIfilter)

if __name__ == '__main__':
    app.run(debug=True)
