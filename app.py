"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Simple CX one call flow builder
#   Version:        Unreleased
#   Date:           30/01/24
#   See Readme.txt for more details
################################################################################"""

import os
import functools
import traceback
from io import BytesIO
import logging
from logging.handlers import TimedRotatingFileHandler

import flask_login
from flask import Flask, redirect, g, render_template, request,send_from_directory,Response, flash
from flask_socketio import SocketIO, join_room
#, url_for,send_file,session
#from configparser import ConfigParser
#Make sure that flask_login and bcrypt are installed

#Local files:
import local.db
import local.io
import local.tts
import local.cxone
import local.datamodel

from routes.audio import bp as audio_blueprint
from routes.callflow import bp as callflow_blueprint
from routes.deployment import bp as deployment_blueprint
from routes.hoo import bp as hoo_blueprint
from routes.poc import bp as poc_blueprint
from routes.project import bp as project_blueprint
from routes.queue import bp as queue_blueprint
from routes.skill import bp as skill_blueprint
from routes.admin import bp as admin_blueprint

#Start our web service app
app = Flask(__name__)
app.secret_key = 'MySecretKey'
socketio = SocketIO(app, async_mode='eventlet')

#Have to declare these after 'socketio' as this is used in the functions in the blueprints
from routes.services import bp as services_blueprint

@socketio.on('join')
def on_join(data):
    """User joins a room"""
    room = data['correlation_key']
    join_room(room)
    print(f"User joined room {room}")


#Register Blueprints (move to common?)
app.register_blueprint(audio_blueprint)
app.register_blueprint(callflow_blueprint)
app.register_blueprint(deployment_blueprint)
app.register_blueprint(hoo_blueprint)
app.register_blueprint(poc_blueprint)
app.register_blueprint(project_blueprint)
app.register_blueprint(queue_blueprint)
app.register_blueprint(skill_blueprint)
app.register_blueprint(services_blueprint)
app.register_blueprint(admin_blueprint)

NEW_APP_SETUP = False

def setup_logging():
    # Create a custom logger
    app_log = logging.getLogger('cxtools')
    app_log.setLevel(logging.DEBUG)

    # Create handlers

    file_handler = TimedRotatingFileHandler('cxtools.log', when='midnight', interval=1)
    file_handler.suffix = "%Y-%m-%d"
    file_handler.setLevel(logging.DEBUG)

    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)  # Set the logging level for the handler

    # Create formatters and add them to handlers
    file_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    console_formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    console_formatter.datefmt = "%H:%M:%S"
    file_handler.setFormatter(file_formatter)
    console_handler.setFormatter(console_formatter)

    # Add handlers to the logger
    app_log.addHandler(file_handler)
    app_log.addHandler(console_handler)

    return app_log

logger = setup_logging()
logger.info('Main application started - check deployment version 1.0.0.1')

local.db.init_db()

#https://pypi.org/project/Flask-Login/
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

@app.teardown_appcontext
def close_db(e=None):
    """Clear app contect/close DB connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()
    if e is not None:
        logger.critical("Exception in teardown %s", e)
        traceback.print_exc()

class User(flask_login.UserMixin):
    """Extend flask login class with id/email/active_project and security map"""
    id = None
    email = None
    active_project =  None

def safe_route(func):
    """Load data model and initialise with current active project - if user is authenticated"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):

        try:
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            logger.info("%s >> %s", func.__name__, signature)
            if flask_login.current_user.is_authenticated:
                g.active_section = request.endpoint
                g.data_model = local.datamodel.DataModel(flask_login.current_user.id,flask_login.current_user.active_project )
                g.item_selected = None
            else:
                g.data_model = None

            value = func(*args, **kwargs)
            #logger.info(f"{func.__name__}() << {repr(value)}")

            logger.info("<< %s << ", func.__name__)
            return value
        except Exception as e:
            logger.error("<< exception at %s: \n %s", __name__, e)
            traceback.print_exc()
            return render_template('project-list.html')
    return wrapper_debug

@login_manager.user_loader
def user_loader(item_id):
    """Flask userloader - updates and builds the g.data_model """
    logger.info(">> user loader for %s", item_id)
    user = User()
    try:
        result = local.db.select_first("user",["*"],{ "id" : item_id})
        if len(result) == 0 :
            logger.info("Invalid user load for ID %s", id)
            return
        user.id  = result.get('id',None)
        user.email = result.get('username',None)
        user.active_project = result.get('active_project',None)
        if result.get('active_project',None) is None:
            user.active_project = local.db.select_first("project", ["id"],{"user_id" : user.id }).get('id')
    except Exception as e:
        logger.error("<< exception at %s: \n %s", __name__, e)
    return user

@login_manager.request_loader
def request_loader(sys_request):
    """NFI"""
    email = sys_request.form.get('email',None)
    if email is None :
        return
    result = local.db.select_first("user",["*"],{ "username" : email})

    if len(result) == 0 :
        return

    user = User()
    user.id  = result['id']
    user.email = result['username']
    user.active_project = result['active_project']

    if result['active_project'] is None:
        user.active_project = (local.db.select_first("project",["id"],{"user_id" : user.id})).get('id')

    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    """Do we ever use this?"""
    return 'Unauthorized', 401

#Routing
@app.route('/favicon.ico')
def favicon():
    """Return a nice picture for the fav icon on the browser"""
    return send_from_directory(os.path.join(app.root_path, 'static'),'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
@safe_route
def index():
    """Web page root - dtermine if user is logged in"""
    if flask_login.current_user.is_authenticated:
        logger.info('User authenticated - check user has active projects')
        logger.info("/ as user %s" , flask_login.current_user.email)

        if len(g.data_model.GetProjectList()) > 0:
            return redirect('/project')
        else:
            flash("You have no active projects - please create a new project","Information")
            return render_template('project-item.html')
    else:
        #We may not have initiated config
        if NEW_APP_SETUP is True:
            logger.info("We are unauthenticated and detected new app %s", NEW_APP_SETUP)
            return redirect ('/setup')
        else:
            logger.info('User not authenticated - redirect to login')
            return redirect('/login')

@app.route('/setup', methods = ['GET', 'POST'])
@safe_route
def setup():
    """Setup Called"""
    if request.method == 'GET':
        return render_template('setup.html')

    logger.info('Creating user login')
    #Lets create our new user ID and set the azure TTS key

    tts_key = request.form['tts_key']
    #nice_key = request.form['nice_key']
    #nice_secret = request.form['nice_secret']
    #verify = request.form['verify']

    #if nice_secret != verify:
    #    flash("Secrets do not match - please validate and re-enter","Error")
    #    return render_template('setup.html')

    #TODO - if existing was found - update
    #dm.AddNewIfNone("config","tts_key", { "key": "tts_key", "value" : tts_key})
    local.db.insert("config", { "key": "tts_key", "value" : tts_key})
    #dm.AddNewIfNone("config","nice_key", { "key": "nice_key", "value" : nice_key})
    #dm.AddNewIfNone("config","nice_secret", { "key": "tts_key", "value" : nice_secret})


    return redirect('/login')

@app.route('/login', methods = ['GET', 'POST'])
@safe_route
def login():
    """Display login page and collect login for user"""
    if request.method == 'POST':
        result = local.db.select_first("user",["*"], {"username" : request.form.get('email'), "password" : request.form.get('password')})
        if len(result) > 0 :
            logger.info("Successfully located user with correct credentials - %s", result['username'])

            user = User()
            user.id  = result['id']
            user.email = result['username']
            user.active_project = result['active_project']
            flask_login.login_user(user, remember=False  )
            return redirect('/')
        else:
            flash("Invalid username or password","Information")

    return render_template('login.html')

@app.route('/tools', methods=['GET','POST'])
@safe_route
def tools_main():
    return render_template('tools-wav.html')

@app.route('/tools/<sub>', methods=['GET','POST'])
@safe_route
def tools(sub = None):
    """Tools page"""
    if request.method == 'GET':
        if sub == 'bulk':
            return render_template('tools-misc.html')
        return render_template('tools-wav.html')
    #POST
    #Check if we are setting connection info:
    action = request.form.get('action')
    action_type = request.form.get('action_type')
    user_name = request.form.get('action_username')
    user_password = request.form.get('action_password')
    if action == "login_connect":
        client = local.cxone.CxOne(user_name,user_password)
        if (user_name == '' or user_password == '') or (client.is_connected() is False):
            flash("Invalid credentials to connect to BU - you can still download speech files, without connecting","Information")
            return render_template('tools-wav.html')
        #We have a token so return to client and let them know
        return render_template('tools-wav.html', action_type = action_type, token = None , connection_name = client.business_unit['businessUnitName'])
    if action == "files_download":
        token = request.form.get('token')
        connection_name = request.form.get("connection_name")
        #create_type =  request.form.get('file_type')
        tts_filename =  request.form.get('file_name')
        tts_utterance = request.form.get('word_input')
        if (tts_filename == '' or tts_utterance == ''):
            flash("You have not entered a file name ","Information")
            return render_template('tools-wav.html', token = token, connection_name = connection_name)

        if not tts_filename.lower().endswith('.wav') :
            tts_filename = tts_filename +".wav"
        voice_font = "en-AU-NatashaNeural"
        tts_subscription_key = local.db.get_setting('tts_key')
        tts = local.tts.Speech(tts_subscription_key)
        tts.get_token()
        audio_response = tts.get_audio(tts_utterance, voice_font)

        logger.info("Length=%s", len(audio_response))
        #And provide download to user
        with BytesIO(audio_response) as output:
            output.seek(0)
            headers = {"Content-disposition": f"attachment; filename={tts_filename}" }
            return Response(output.read(), mimetype='audio/wav', headers=headers)
    if action == "login_clear":
        return render_template('tools-wav.html')

    flash("Unknown Action","Error")
    return render_template('tools-wav.html')

@app.route('/debug')
@safe_route
def debug():
    """Debug page"""
    return render_template('tools-debug.html')


@app.route('/logout')
@safe_route
def logout():
    """Log out user"""
    flask_login.logout_user()
    flash("You have been logged out","Information")
    return redirect('/login')

@app.route('/instance')
@safe_route
def instance():
    """Select the project instance if we are logged in"""
    if flask_login.current_user.is_authenticated:
        project_instance = request.args.get('instance')
        logger.info("Setting active instance %s", project_instance)
        #Don't select a project if we are not allowed to!
        local.db.update("user",{"active_project": project_instance},{ "id" : flask_login.current_user.id})
        flask_login.current_user.activeProject = project_instance
        return redirect('/project')
    else:
        return redirect('/login')

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
@safe_route
def download(filename):
    """Used to get files from local directory as needed in TTS - defaults to default directory"""
    download_path = os.path.join(app.root_path, 'packages//default')
    return send_from_directory(download_path, filename, mimetype='text/plain',as_attachment = True)

if __name__ == '__main__':
    socketio.run(app , debug=False)
