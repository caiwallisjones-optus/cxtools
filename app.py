"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Simple CX one call flow builder
#   Version:        Unreleased
#   Date:           30/01/24
#   See Readme.txt for more details
################################################################################"""

import os
import traceback
from io import BytesIO
import json
from markupsafe import Markup

import flask_login
from flask import Flask, redirect, g, render_template, request,send_from_directory,Response, flash
from flask_socketio import SocketIO, join_room
#, url_for,send_file,session
#from configparser import ConfigParser
#Make sure that flask_login and bcrypt are installed

from logging_config import logger
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
from routes.common import safe_route , unsafe_route

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

@login_manager.user_loader
def user_loader(item_id):
    """Flask userloader - updates and builds the g.data_model """
    logger.info(">> user loader for %s", item_id)
    user = User()
    try:
        user_record = local.db.select_first("user",["*"],{ "id" : item_id})
        if user_record is None:
            logger.info("Invalid user load for ID %s", id)
            return
        user.id  = user_record.get('id',None)
        user.email = user_record.get('username',None)
        user.active_project = user_record.get('active_project',None)
        if user_record.get('active_project',None) is None:
            user.active_project = local.db.select_first("project", ["id"],{"user_id" : user.id }).get('id')
    except Exception as e:
        logger.error("<< exception at %s: \n %s", __name__, e)

    return user

@login_manager.request_loader
def request_loader(sys_request):
    """NFI"""
    email = sys_request.form.get('email',None)
    if email is None :
        logger.info("no email in request loader")
        return
    result = local.db.select_first("user",["*"],{ "username" : email})

    if result is None:
        logger.info("no user located from request loader")
        return

    user = User()
    user.id  = result['id']
    user.email = result['username']
    user.active_project = result['active_project']

    if result['active_project'] is None:
        user.active_project = (local.db.select_first("project",["id"],{"user_id" : user.id})).get('id')
    #logger.info("user identified as %s", user.email)
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

        if g.data_model.db_get_list("project") is not None:
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
    local.db.insert("config", { "key": "tts_key", "value" : tts_key})

    return redirect('/login')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    """Display login page and collect login for user"""
    if request.method == 'POST':
        result = local.db.select_first("user",["*"], {"username" : request.form.get('email'), "password" : request.form.get('password')})
        if result is not None:
            logger.info("Successfully located user with correct credentials - %s", result['username'])

            user = User()
            user.id  = result['id']
            user.email = result['username']
            user.active_project = result['active_project']
            flask_login.login_user(user, remember=False  )
            return redirect('/')
        else:
            flash("Invalid username or password","Information")
            return redirect('/login')

    return render_template('login.html')

@app.route('/tools', methods=['GET','POST'])
@unsafe_route
def tools_main():
    return render_template('tools-wav.html')

@app.route('/tools/<sub>', methods=['GET','POST'])
@unsafe_route
def tools(sub = None):
    """Tools page"""
    if request.method == 'GET':
        if sub == 'bulk':
            return render_template('tools-misc.html')
        if sub == "debug":
            return render_template('tools-debug.html')
        if sub =="review":
            return render_template('tools-review.html')
        return redirect('/tools')
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
    if action == "review":
        snippet_name = request.form.get('query')
        dm : local.datamodel.DataModel = g.data_model
        if dm is None:
            logger.info("No data model - cannot review")
            flash("Unable to locate configuration data","Error")
            return redirect('/tools')
        project = dm.db_get_item("project",flask_login.current_user.active_project)
        key  = project['user_key']
        secret = project['user_secret']
        client = local.cxone.CxOne(key,secret)
        if client.is_connected():
            if project['instance_name'] == "":
                path = ""
            else:
                path = project['instance_name'] + "\\"
            script = client.get_script(f"{path}CustomEvents_PROD")
        else:
            logger.info("Unable to connect to CxOne - cannot review")
            flash("Unable to connect to CxOne - cannot review","Error")
            return redirect('/tools')
        data = json.loads(script)

        snippet_id = None
        for script_action in data['actions']:
            if data['actions'][script_action]['label'] == snippet_name:
                snippet_id = script_action
                break

        #Now get the text
        if snippet_id is not None:
            result = data['properties'][snippet_id]['0']['value']
            result = Markup(f"<pre>{result}</pre>")
            return render_template('tools-review.html', item_text = result)

        logger.info("Unable to locate snippet %s", snippet_name)
        flash("Unable to locate snippet %s" , snippet_name)
        return render_template('tools-review.html')

    flash("Unknown Action","Error")
    return render_template('tools-wav.html')

@app.route('/logout')
@unsafe_route
def logout():
    """Log out user"""
    flask_login.logout_user()
    flash("You have been logged out","Information")
    return redirect('/login')

@app.route('/instance')
@safe_route
def instance():
    """Select the project instance if we are logged in"""
    dm : local.datamodel.DataModel = g.data_model
    if flask_login.current_user.is_authenticated:
        project_instance = request.args.get('instance')
        logger.info("Setting active instance %s", project_instance)
        dm.db_update("user", flask_login.current_user.id, {"active_project": project_instance})
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

@app.route('/help/<path:subpath>', methods=['GET'])
@unsafe_route
def help_redirect(subpath):
    """Redirect requests to /help/<somepath> to static/help/<somepath>.html"""
    try:
        return send_from_directory(os.path.join(app.root_path, 'static', 'help'), f"{subpath}.html")
    except Exception as e:
        logger.error("Error serving help file for path %s: %s", subpath, e)
        return "Help file not found", 404

if __name__ == '__main__':
    socketio.run(app , debug=False)
