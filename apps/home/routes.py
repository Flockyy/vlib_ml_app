from apps.authentication.models import Predictions
from apps.home import blueprint
from decouple import config
from flask import render_template, request, redirect, url_for
from flask_login import login_required, current_user
from jinja2 import TemplateNotFound
import pickle
import pandas as pd
from datetime import datetime, date
import requests
import json
# import locale

# locale.getlocale()
# ('fr_FR', 'UTF-8')
# locale.setlocale(locale.LC_TIME, 'fr_FR')
# 'fr_FR'

model=pickle.load(open('model_charly/BestModel.pkl', 'rb'))

@blueprint.route('/index')
@login_required
def index():
    return render_template('home/index.html', segment='index')

@blueprint.route('/<template>')
@login_required
def route_template(template):

    try:

        if not template.endswith('.html'):
            pass

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500
    
# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None

#setting up weather api_key
def get_api_key():
    api_key = config('API')
    return api_key

def get_weather_results(city, api_key):
    lang = 'fr'
    url =f'https://api.openweathermap.org/data/2.5/weather?q={city}&lang={lang}&appid={api_key}&units=metric'
    response = requests.get(url)
    return response.json()

#Prediction history route
@blueprint.route('/pred-history', methods=['POST', 'GET'])
@login_required
def preds_history_page():

    #Retrieving predictions data for the current user
    user_id = current_user.get_id()
    pred = Predictions()
    prediction_list = pred.find_by_user_id(user_id)

    return render_template('home/page-pred-history.html', prediction_list = prediction_list, segment = 'pred-history')
    
#Adding routes
@blueprint.route('/preds', methods=['POST', 'GET'])
@login_required
def preds_page():

    date = pd.to_datetime(request.form['Date'])
    time = date.date()
    difference = (pd.to_datetime(time) - pd.to_datetime(2012-12-19)).days
    season = request.form['Season']
    weather = request.form['weather']
    if request.form['day'] == 'Work day':
        workingday = 1
        holiday = 0
    else:
        workingday = 0
        holiday = 1
    
    year = date.year
    month = date.month
    month_name = date.month_name()
    day = date.day_name()
    hour = date.hour
    minutes = date.minute
    day_number = date.day
    temp = request.form['tempre']
    windspeed = request.form['vent']
    humidity = request.form['humid']
    atemp = request.form['atemp']

    if hour >= 20 or hour <= 8:
        is_night = 1
    else:
        is_night = 0
    
    dictionary = {'season': int(season), 'holiday': holiday, 'workingday':workingday, 'weather':float(weather) , 'temp':float(temp), 'atemp':float(atemp), 'humidity':float(humidity), 'windspeed':float(windspeed), 'month':float(month), 'day':day, 'hour':int(hour), 'year':int(year), 'date':difference, 'is_night':is_night}
    variables = list(dictionary.values())
    
    df = pd.DataFrame([variables], columns=dictionary.keys())
    prediction = model.predict(df)
    
    # DB storing
    pred = Predictions(
        user_id = current_user.get_id(), 
        datetime= str(date), 
        season= int(season), 
        weather= int(weather), 
        workday = request.form['day'], 
        temperature = temp, 
        atemperature = atemp, 
        humidity = humidity, 
        windspeed = windspeed, 
        count = int(prediction[0])
    )
    pred.save_to_db()
    
    return render_template('home/page-preds.html', date = date, prediction = int(prediction[0]), hour = hour, day=day, year=year, minutes = minutes, month=month_name, day_number = day_number)

@blueprint.route('/results', methods=['GET', 'POST'])
@login_required
def results():
    pred = Predictions()
    all_pred_list = pred.get_all_in_list_with_user_name()
    prediction_list = []
    date_list = []

    for i in  all_pred_list:
        prediction_list.append(i.count)
        date_list.append(i.datetime)

    return render_template('home/results.html', preds = json.dumps(prediction_list), dates = json.dumps(date_list), segment = 'results')
    

@blueprint.route('/weather', methods=['POST', 'GET'])
@login_required
def weather():

    city = 'Lille' #fill in the city logic
    api_key = get_api_key()
    data = get_weather_results(city, api_key)
    today = date.today()
    day = today.strftime('%B %d, %Y')
    time = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    time = datetime.strptime(time,"%Y-%m-%d %H:%M:%S")
    day_name = today.strftime('%A')
    temp = '{0:.1f}'.format(data['main']['temp'])
    feels_like = '{0:.2f}'.format(data['main']['feels_like'])
    weather = data['weather'][0]['main']
    desc = data['weather'][0]['description'].title()
    humidity = data['main']['humidity']
    wind = data['wind']['speed']
    hr, mi = (time.hour, time.minute)

    if hr>=7 and hr<18: 
        time = 'day'
    else:
        time = 'night'

    return render_template('home/home_weather.html', weather=weather, feels_like=feels_like, temp=temp, city = city, date=day, day =day_name, desc=desc, humidity=humidity, wind=wind, time=time, segment = 'page-weather')


@blueprint.route('/delete_record')
def delete_record():
    """Delete prediction records in BDD"""
    record_id = request.args.get('id')
    Predictions.query.filter_by(id=record_id).first().delete_from_db()
    return redirect(url_for('preds_history_page'))