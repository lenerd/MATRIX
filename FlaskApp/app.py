import datetime
from functools import wraps

import bson

from pymongo import MongoClient
from flask import Flask, render_template, request, flash, redirect, url_for, session
from flask_login import LoginManager
from apscheduler.schedulers.background import BackgroundScheduler

from FlaskApp.competition_forms import CompetitionForm, CompetitionRegistrationForm
from FlaskApp.validate_submission import Submission


def validate_submission():
    client = MongoClient()
    db = client['BIU']
    collection = db['submissions']

    # TODO: download the configuration file from MATRIX folder at the repo.
    for submission in collection.find({'hasValidated': 'false'}):
        try:
            address = submission['gitAddress']
            # config_file = submission['sanityFile']
            config_file = 'https://raw.githubusercontent.com/cryptobiu/MATRIX/master/ProtocolsConfigurations/Config_HyperMPC.json'
            protocol_name = address.split('/')[-1]
            address += '.git'
            validation = Submission(config_file)
            validation.validate()
        except KeyError as e:
            print('Key %s not found ' % e)
            continue


sched = BackgroundScheduler(daemon=True)
sched.add_job(validate_submission, trigger='interval', seconds=10)
sched.start()

login_manager = LoginManager()
app = Flask(__name__)
login_manager.init_app(app)


def is_logged_in(f):
    @wraps(f)
    def wrap(*args, **kwargs):
        if 'logged_in' in session:
            return f(*args, **kwargs)
        else:
            flash('Unauthorized, Please login', 'danger')
            return redirect(url_for('login'))
    return wrap


@app.route('/home')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html', title='-About')


@app.route('/', methods=['GET'])
def login():
    return render_template('login.html', title='-Login')


@app.route('/<string:user>')
def login_user(user):
    session['user'] = user
    session['logged_in'] = True
    return redirect(url_for('index'))


@app.route('/circuits')
def circuits():

    client = MongoClient()
    db = client['BIU']
    collection = db['circuits']
    circuits_list = []

    for circuit in collection.find({}):
        circuits_list.append(circuit)
    return render_template('circuits.html', title='-Circuits', circuit_files=circuits_list)


@app.route('/competitions')
# @is_logged_in
def competitions():
    client = MongoClient()
    db = client['BIU']
    collection = db['Competitions']
    competitions_list = []

    for competition in collection.find({}):
        competitions_list.append(competition)

    return render_template('competitions.html', title='-Competitions', competitions=competitions_list)


@app.route('/competitions_manage', methods=['GET', 'POST'])
def competitions_management():
    form = CompetitionForm(request.form)
    if request.method == 'POST':
        name = form.name.data
        description = form.description.data
        start_date = form.start_date.data
        end_date = form.end_date.data
        status = form.status.data
        start_date = datetime.datetime.combine(start_date, datetime.datetime.min.time())
        end_date = datetime.datetime.combine(end_date, datetime.datetime.min.time())

        client = MongoClient()
        db = client['BIU']
        collection = db['Competitions']
        competition = {
            'competitionName': name,
            'description': description,
            'startDate': start_date,
            'endDate': end_date,
            'status': status
        }

        try:
            competition_id = collection.insert_one(competition)
            if competition_id.acknowledged:
                flash('Competition added', 'success')
        except bson.errors.InvalidDocument:
            flash('Failed to create new competition', 'danger')

        return redirect(url_for('competitions'))

    return render_template('competitions_manage.html', title='-CompetitionsAdminPanel', form=form)


@app.route('/register_competition/<string:competition_name>', methods=['GET', 'POST'])
def register_competition(competition_name):
    form = CompetitionRegistrationForm(request.form)
    if request.method == 'POST':
        client = MongoClient()
        db = client['BIU']
        collection = db['submissions']
        git_address = form.address.data
        sanity_file = form.sanity_file.data
        submission = {
            'competitionName': competition_name,
            'gitAddress': git_address,
            'sanityFile': sanity_file,
            'hasValidated': 'false',
            'user': session['user']
        }
        try:
            submission_id = collection.insert_one(submission)
            if submission_id.acknowledged:
                flash('Submission added', 'success')
        except bson.errors.InvalidDocument:
            flash('Failed to create new submission', 'danger')
        return redirect(url_for('competitions'))

    return render_template('register_competition.html', title='-%s Registration' % competition_name, form=form,
                           competition_name=competition_name)


if __name__ == '__main__':
    app.secret_key = 'secret'
    app.run(debug=True)
