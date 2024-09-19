"""################################################################################
#
#   Author:         Cai Wallis-Jones
#   Description:    Simple CX one call flow builder
#   Version:        Unreleased
#   Date:           30/01/24
#   See Readme.txt for more details
#
################################################################################"""

import os
import io
import functools
import traceback
from io import BytesIO

import flask_login
from flask import (Flask, redirect, g, render_template, request,send_from_directory,Response, flash)
#, url_for,send_file,session
#from configparser import ConfigParser
#Make sure that flask_login and bcrypt are installed

#Local files:
import local.db
import local.io
import local.tts
import local.cxone
import local.datamodel

newAppSetup = False

#We dont need this?!
#Init DB - create as needed
#dbInit =
local.db.init_db()

#Start our web service app
app = Flask(__name__)
app.secret_key = 'MySecretKey'

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
        print("Exception: ", e)
        traceback.print_exc()


class User(flask_login.UserMixin):
    """Extend flask login class with id/email/activeProjectId and security map"""
    id = None
    email = None
    activeProjectId =  None
    securityMap = None

def safe_route(func):
    """Load data model and initialise with current active project - if user is authenticated"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):

        try:
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            print(f"{func.__name__} >> ({signature})")

            if flask_login.current_user.is_authenticated:
                g.active_section = request.endpoint
                g.data_model = local.datamodel.DataModel(flask_login.current_user.id,flask_login.current_user.activeProjectId )
                g.item_selected = None

            value = func(*args, **kwargs)
            #print(f"{func.__name__}() << {repr(value)}")

            print(f"<< {func.__name__}() <<")
            return value
        except Exception as e:
            print("Exception: ", e)
            traceback.print_exc()
            return render_template('project-list.html')
    return wrapper_debug

@login_manager.user_loader
def user_loader(item_id):
    """Flask userloader - updates and builds the g.data_model """
    print(f'User loader for {item_id}' )
    result = local.db.SelectFirst("user",["*"],{ "id" : item_id})
    if len(result) == 0 :
        print(f'Invalid user load for ID {id}')
        return
    user = User()
    user.id  = result.get('id',None)
    user.email = result.get('username',None)
    user.activeProjectId = result.get('active_project',None)
    try:
        if result.get('active_project',None) is None:
            user.activeProjectId = local.db.SelectFirst("project", ["id"],{"user_id" : user.id }).get('id')
    finally:
        pass
    return user

@login_manager.request_loader
def request_loader(sys_request):
    """NFI"""
    email = sys_request.form.get('email',None)
    if email is None :
        return
    result = local.db.SelectFirst("user",["*"],{ "username" : email})

    if len(result) == 0 :
        return

    user = User()
    user.id  = result['id']
    user.email = result['username']
    user.activeProjectId = result['active_project']

    if result['active_project'] is None:
        user.activeProjectId = (local.db.SelectFirst("project",["id"],{"user_id" : user.id})).get('id')

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
        print('User authenticated - check user has active projects')
        print(f"/ as user {flask_login.current_user.email}")

        if len(g.data_model.GetProjectList()) > 0:
            return redirect('/project')
        else:
            flash("You have no active projects - please create a new project","Information")
            return render_template('project-item.html')
    else:
        #We may not have initiated config
        if newAppSetup == True:
            print(f'We are unauthenticated and detected new app "{newAppSetup}"')
            return redirect ('/setup')
        else:
            print('User not authenticated - redirect to login')
            return redirect('/login')

@app.route('/setup', methods = ['GET', 'POST'])
@safe_route
def setup():
    """Setup Called"""
    if request.method == 'GET':
        return render_template('setup.html')

    print('Creating user login')
    #Lets create our new user ID and set the azure TTS key
    email = request.form['email']
    password = request.form['password']
    tts_key = request.form['tts_key']

    local.db.AddSetting("tts_key",tts_key)
    local.db.AddUser(email, password)

    return redirect('/login')

@app.route('/login', methods = ['GET', 'POST'])
@safe_route
def login():
    """Display login page and collect login for user"""
    if request.method == 'POST':
        result = local.db.SelectFirst("user",["*"], {"username" : request.form.get('email'), "password" : request.form.get('password')})
        if len(result) > 0 :
            print(f'Successfully located user with correct credentials - {result['username']}')

            user = User()
            user.id  = result['id']
            user.email = result['username']
            user.activeProjectId = result['active_project']
            flask_login.login_user(user, remember=False  )
            return redirect('/')
        else:
            flash("Invalid username or password","Information")

    return render_template('login.html')

@app.route('/project', methods=['GET','POST'])
@safe_route
def project():
    """Display porject page"""
    if request.method =="POST":
        action = request.form['action'] # get the value of the clicked button
        if action =="create":
            return render_template('project-item.html')
        if action =="edit":
            g.item_selected = request.form['id']
            return render_template('project-item.html')
        if action =="delete":
            g.item_selected = request.form['id']
            project_count = len(g.data_model.GetProjectList())
            print(f"Number of projects  {project_count}")
            if project_count < 2:
                print("Delete item request - not  enough projects")
                flash("Cannot delete past project - create a new project first","Information")
                return render_template('project-list.html')
            else:
                local.db.Delete("project",{ "id" : g.item_selected} )
                #TODO- select first active project
                return render_template('project-list.html')

        #item actions
        if action =="item_create":
            try:
                #Create new project details
                values = g.data_model.BuildItemParamList(request)
                print(f'Creating project for {values.get('short_name')}')
                print(f'Created by user ID {g.data_model.user_id}')

                project_id = local.db.Insert("project",values)
                g.data_model.project_id =  project_id
                flask_login.current_user.activeProjectId = project_id
                local.db.Update("user",{ "active_project" : project_id },{"id" : g.data_model.user_id})
                if  project_id is not None:
                    #Add default wav files to project ID
                    print('Generating standard WAV records for project')
                    sys_audio = local.io.GetSystemAudioFileList('default')
                    for key in sys_audio.items():
                        print(key)
                        local.db.Insert("audio",{"project_id" : project_id , "name" : key , "description" : sys_audio[key] , "isSystem" : True})
            except Exception as e:
                flash("Something went wrong creating project","Error")
                print("Exception: ", e)
                traceback.print_exc()
            return render_template('project-list.html')

        if action =="item_update":
            project_id = request.form['id']
            values = g.data_model.BuildItemParamList(request)
            local.db.Update("project",values,{ "id" : project_id})
            return render_template('project-list.html')

    return render_template('project-list.html')

@app.route('/queues', methods=['GET','POST'])
@safe_route
def queues():
    """Display queues page"""
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button

        if action =="create":
            return render_template('queue-item.html')

        if action =="edit":
            item_id = request.form['id'] # get the value of the clicked button
            item = local.db.GetQueue(item_id)
            actions = local.db.GetQueueActionsList(item_id)
            return render_template('queue-item.html', item = item, actions= actions)

        if action == "delete":
            item_id = request.form['id'] # get the value of the clicked button
            local.db.DeleteQueue(item_id)
            return render_template('queue-list.html')

        ##          Queue-Item Actions
        if action == "queue_new":
            #Create new queue details
            queue_name = request.form['name']
            print(f"Creating queue details for {queue_name}")
            print(f"Creating user ID is {flask_login.current_user.id}")
            print(f"Creating project ID is {flask_login.current_user.activeProjectId}")

            new_queue_id = local.db.AddQueue(flask_login.current_user.activeProjectId,queue_name,"","")

            item = local.db.GetQueue(new_queue_id)
            return render_template('queue-item.html', item = item )

        if action =="queue_update":
            queue_id = request.form['id']
            queue_name = request.form['name']
            queue_skills =  request.form['attachedskills']
            queue_hoo =  request.form['hoo']

            print(f"Updating queue details for {queue_name}")
            print(f"QueueHoo {queue_hoo}")
            err_msg  = local.db.UpdateQueue(queue_id,queue_name,queue_skills,queue_hoo)
            flash(err_msg,"Error")
            return render_template('queue-list.html')

        if action =="queue_cancel":
            return redirect('/queues')

    #Action updates from Queue-Item:
        if action =="queue_item_skill_new":
            #Append queueskill to list (table id!)
            item_id = request.form['id'] # get the value of the clicked button
            item = local.db.GetQueue(item_id)

            queue_name = item[2]
            queue_skills =  item[3]
            queue_hoo = item[4]
            queue_newskill = request.form['new_skill']
            skill_array = queue_skills.split(",")
            if queue_newskill not in skill_array:
                skill_array.append(queue_newskill)
                while '' in skill_array:
                    skill_array.remove('')
                    queue_skills = (",").join(skill_array)

            print(f"Updating queue details for {queue_name}")

            local.db.UpdateQueue(item_id,queue_name,queue_skills,queue_hoo)

            #item = local.db.GetQueue(id)
            actions = local.db.GetQueueActionsList(str(item_id))
            item = local.db.GetQueue(item_id)
            return render_template('queue-item.html', item = item, actions= actions)

        if action =="queue_item_skill_remove":

            item_id = request.form['id']
            queue_name = request.form['name']
            queue_skills =  request.form['attachedskills']
            queue_hoo = request.form['hoo']
            queue_skillremove = request.form['skill_remove']
            print(f"Removing: {queue_skillremove}")
            skill_array = queue_skills.split(",")
            if queue_skillremove in skill_array:
                skill_array.remove(queue_skillremove)
                queueskills = (",").join(skill_array)

            print(f"**Updating queue details for {queue_name}")
            print(f"**QueueHoo {queue_name}")
            local.db.UpdateQueue(item_id,queue_name,queueskills,queue_hoo)

            item = local.db.GetQueue(item_id)
            actions = local.db.GetQueueActionsList(item_id)
            return render_template('queue-item.html', item = item, actions= actions )

        if action == "queue_action_new":
            #Create new queue action - this is called from the queue-item html
            item_id = request.form['id']
            return render_template('queueaction-item.html', item = None, item_id = queue_id)

        if action =="queue_action_edit":
            #Edit the queue action
            action_id = request.form['action_id']
            queue_id = request.form['queue_id']
            item = local.db.GetQueueAction(action_id)
            print('We are editing our action - ' + action_id)
            print(item)
            return render_template('queueaction-item.html', item = item, queue_id = queue_id)

        if action =="queue_action_delete":
            #Delete the queue action
            action_id = request.form['action_id']
            queue_id = request.form['queue_id']
            local.db.DeleteQueueAction(action_id)
            item = local.db.GetQueue(queue_id)
            return render_template('queue-item.html', item = None, actions = local.db.GetQueueActionsList(queue_id) )

        if action =="queue_action_up":
            return "Not Built yet TODO - 00003 " + action
        if action =="queue_action_down":
            return "Not Built yet TODO - 00004 " +  action

        #Action updates from QueueAction-Item:
        if action =="queueaction_create":
            #Create new queue action(blank)
            queue_id = request.form['queue_id']
            #errMsg = local.db.AddQueueAction(id)
            queue_action = request.form['queueaction']
            param1 =  request.form['param1']
            param2 =  request.form['param2']
            print(f'Param 1 {param1}')
            print(f'Param 2 {param2}')
            local.db.AddQueueAction(queue_id,queue_action,param1,param2)
            item = local.db.GetQueue(queue_id)
            return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id))

        if action =="queueaction_update":
            action_id = request.form['id']
            queue_action = request.form['queueaction']
            param1 =  request.form['param1']
            param2 =  request.form['param2']
            local.db.UpdateQueueAction(action_id,queue_action,param1,param2)

            queue_id = request.form['queue_id']
            item = local.db.GetQueue(queue_id)
            return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id))

        if action =="queueaction_cancel":
            queue_id = request.form['queue_id']
            item = local.db.GetQueue(queue_id)
            return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id))

        #Queue Hoo Operations
        if action =="queue_item_inqueueaction_new":
            queue_id = request.form['id']
            state = request.form['inqueueState']
            action_type = request.form['inqueueStateAction']
            params = request.form['inqueueStateParams']

            local.db.UpdateQueueHooActions(queue_id,'QUEUE',state,action_type,params)
            item = local.db.GetQueue(queue_id)
            return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id))
        if action =="queue_item_prequeueaction_new":
            queue_id = request.form['id']
            state = request.form['prequeueState']
            action_type = request.form['prequeueStateAction']
            params = request.form['prequeueStateParams']

            local.db.UpdateQueueHooActions(queue_id,'PREQUEUE',state,action_type,params)
            item = local.db.GetQueue(queue_id)
            return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id))
        if action == "queue_item_prequeueaction_remove":
            queue_id = request.form['id']
            actionToRemove = request.form['queue_item_prequeueaction_remove']
            local.db.DeleteQueueHooAction(queue_id,'QUEUE',actionToRemove)

            item = local.db.GetQueue(queue_id)
            return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id))

    return render_template('queue-list.html')

@app.route('/callflow', methods=['GET','POST'])
@safe_route
def callflow():
    """Display callflow page"""
    if request.method == 'GET':
        return render_template('callflow-list.html')

    #POST:
    action = request.form['action'] # get the value of the clicked button
    g.item_selected = request.form['id']

    if action =="create":
        return render_template('callflow-item.html',  item = None, action_item = None, action_responses = None)

    if action =="edit":
        item = local.db.GetCallFlow(g.item_selected)
        if item[5] is not None:
            action_item = local.db.GetCallFlowAction(item[5])
            action_responses = local.db.GetCallFlowActionResponses(action_item[0])
            return render_template('callflow-item.html',  item = item, action_item = action_item, action_responses = action_responses)

        return render_template('callflow-item.html',  item = item, action_item = None, action_responses = None)

    if action == "delete":
        item_id = request.form['id'] # get the value of the clicked button
        local.db.DeleteCallFlow(item_id)
        return render_template('callflow-list.html')

    if action =="callflow_item_poc_new":
        callflow_id = request.form['id']
        callflow_name = request.form['name']
        callflow_description =  request.form['description']
        new_poc_id =  request.form['new_poc']

        item = local.db.GetCallFlow(callflow_id)
        ##Get poc by ID
        if item[4] is None:
            poc_list = new_poc_id
        else:
            poc_list = (item[4] + "," + new_poc_id).lstrip(',')
        ##Update callflow.
        local.db.UpdateCallFlow({ 'poc_list' :poc_list }, {'id': item[0]})
        item = local.db.GetCallFlow(callflow_id)
        return render_template('callflow-item.html',  item = item, action_item = None, action_responses = None)

    ######
    ##          CallFlow-Item Actions
    ######
    if action == "item_new":
        #Create new queue details
        callflow_name = request.form['name']
        callflow_description =  request.form['description']

        callflow_id = local.db.AddCallFlow(flask_login.current_user.activeProjectId,callflow_name,callflow_description)
        if callflow_id.isnumeric():
            item = local.db.GetCallFlow(callflow_id)
            return render_template('callflow-item.html',  item = item, action_item = None, action_responses = None)
        else:
            flash(callflow_id,"Error")
            return render_template('callflow-item.html',  item = None, action_item = None, action_responses = None)

    if action =="item_update":
        #Update Name and description as needed
        call_flow_id = request.form['id']
        call_flow_name = request.form['name']
        call_flow_description =  request.form['description']
        local.db.UpdateCallFlow({'name': call_flow_name,'description': call_flow_description },{'id' : call_flow_id })
        #Update the current action as needed
        call_flow_action_id = request.form.get('action_id',None)
        if not(call_flow_action_id is None or call_flow_action_id == ''):
            call_flow_action_name = request.form['action_name']
            call_flow_action_type = request.form['action_type']
            call_flow_action_params = []
            call_flow_action_params.append(request.form.get('action_param_0',None))
            call_flow_action_params.append(request.form.get('action_param_1',None))
            call_flow_action_params.append(request.form.get('action_param_2',None))
            call_flow_action_params.append(request.form.get('action_param_3',None))
            call_flow_action_params.append(request.form.get('action_param_4',None))
            #Generate call params based on internal ID
            i = 0
            for action_element in g.data_model.GetActionParams(call_flow_action_type):
                #Add element names to appropriate list IF they do not exist
                if (len(call_flow_action_params[i]) > 0) and action_element.endswith("_LOOKUP"):
                    item_type  = action_element.split('|')[1][:-7]
                    item_exists = g.data_model.AddNewIfNoneEx(item_type,"name",{ "name" : call_flow_action_params[i], "description" : "<Added when creating call flow - update details before publishing>"})
                    #Now update the lookup so that we have the ID not the name in our lists
                    call_flow_action_params[i] = str(abs(item_exists))
                i += 1
            #build param list
            action_params = g.data_model.BuildParamList(call_flow_action_type, (call_flow_action_params) )
            params = {'name' : call_flow_action_name,'action': call_flow_action_type, 'params' : action_params}
            query_filter = {'id' : call_flow_action_id}
            local.db.UpdateCallFlowAction(params,query_filter)

        item = local.db.GetCallFlow(call_flow_id)
        action_item = local.db.GetCallFlowAction(call_flow_action_id)
        action_responses = local.db.GetCallFlowActionResponses(action_item[0])

        return render_template('callflow-item.html',  item = item, action_item = action_item, action_responses = action_responses)

    if action =="item_cancel":
        return redirect('/callflow')

    if action =="action_new":
        item_id = request.form['id']
        item = local.db.GetCallFlow(item_id)
        #Now build the param list for the actions
        action_id = request.form['action_id']
        action_type = request.form['action_type']
        action_parent = 0
        if action_id == '':
            action_name = "BEGIN"
        else:
            action_name = "Action"
        if not(action_id is None or action_id == ''):
            # We need to update the action with the action_type - and for this we only set the action_type
            params = {'action': action_type}
            query_filter = {'id' : action_id}
            local.db.UpdateCallFlowAction(params,query_filter)

            #Add default action as needed
            item = local.db.GetCallFlow(id)
            action_item = local.db.GetCallFlowAction(action_id)
            if g.data_model.GetActionHasDefaultResponse(action_type):
                local.db.AddActionResponse(item[0],action_item[0],"DEFAULT",None)

            action_responses = local.db.GetCallFlowActionResponses(action_item[0])

            return render_template('callflow-item.html',  item = item, action_item = action_item, action_responses = action_responses)

        else:

            #Moving the config to when we have created the action
            action_added = local.db.AddCallFlowAction(id,action_parent,action_name,action_type,"")
            #And set the child id as its our first:
            local.db.UpdateCallFlow({'name': item[2],'description': item[3] , 'callFlowAction_id' : action_added },{'id' : id })

            item = local.db.GetCallFlow(id)
            action_item = local.db.GetCallFlowAction(action_added)
            if g.data_model.GetActionHasDefaultResponse(action_type):
                local.db.AddActionResponse(item[0],action_item[0],"DEFAULT",None)
                action_responses = local.db.GetCallFlowActionResponses(action_item[0])

        return render_template('callflow-item.html',  item = item, action_item = action_item, action_responses = action_responses)

    if action == "action_response_new":
        callflow_id = request.form['id']
        action_id = request.form['action_id']
        action_response = request.form['action_response_new']

        #Add response for action_id
        local.db.AddActionResponse(callflow_id,action_id,action_response,None)

        item = local.db.GetCallFlow(callflow_id)
        action_item = local.db.GetCallFlowAction(action_id)
        action_responses = local.db.GetCallFlowActionResponses(action_item[0])
        return render_template('callflow-item.html',  item = item, action_item = action_item, action_responses = action_responses)

    if action.startswith("action_response_create_"):
        #Create a new response and update the existing response
        callflow_id = request.form['id']
        action_id = request.form['action_id']
        parent_response_id = action.removeprefix("action_response_create_")
        parent_response = local.db.GetCallFlowActionResponse(parent_response_id)
        action_name = request.form.get('action_name',"Action_") +"_" + parent_response[3]
        new_action = local.db.AddCallFlowAction(callflow_id,action_id,action_name ,"","")
        #Update our parent response to point to the new action
        local.db.UpdateCallFlowActionResponse(parent_response_id,new_action)

        item = local.db.GetCallFlow(callflow_id)
        action_item = local.db.GetCallFlowAction(new_action)
        action_responses = local.db.GetCallFlowActionResponses(new_action[0])
        return render_template('callflow-item.html',  item = item, action_item = action_item, action_responses = action_responses)

    if action.startswith("action_response_select_"):
        callflow_id = g.item_selected
        action_response_id = action.removeprefix("action_response_select_")
        #Get action response Id to get next action Id
        item = local.db.GetCallFlow(g.item_selected)
        action_item = local.db.GetCallFlowAction(action_response_id)
        action_responses = local.db.GetCallFlowActionResponses(action_response_id)
        return render_template('callflow-item.html',  item = item, action_item = action_item, action_responses = action_responses)

    return f"Not Built yet TODO - /callflow POST {action}"

@app.route('/audio', methods=['GET','POST'])
@safe_route
def audio():
    """Route all audio requests"""
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        #Audio-List
        if action == 'create':
            return render_template('audio-item.html')

        if action.startswith("download"):
            file_id = request.form['id'] # get the value of the item associated with the button
            file = local.db.SelectFirst("audio","*",{ "id" : file_id})

            print(f"Request for text to speech with a filename={file['name']}")
            try:
                sub_key = local.db.GetSetting("tts_key")
                voice_font = "en-AU-NatashaNeural"

                tts = local.tts.Speech(sub_key)
                audio_response = tts.save_audio(file['description'], voice_font)
                print(f"TTS file length {len(audio_response)}")

                with BytesIO(audio_response) as output:
                    output.seek(0)
                    headers = {"Content-disposition": f"attachment; filename={file['name']}.wav" }
                    return Response(output.read(), mimetype='audio/wav', headers=headers)
            except Exception as e:
                print(f"Exception {e}")
                flash("Unable to connect API", "Error")

        if action == 'import_list':
            flash("Import feature is not implemented yet","Information")

        if action == 'edit':
            g.item_selected = request.form['id'] # get the value of the item associated with the button
            return render_template('audio-item.html')

        if action == 'delete':
            item_selected = request.form['id']
            local.db.Delete("audio",{ "id" : item_selected})

        #Audio-Item
        if action == 'item_update':
            file_id = request.form['id']
            file_name = request.form['name']
            wording = request.form['description']
            if local.db.Update("audio",{ "name" : file_name, "description" : wording },{ "id" : file_id }):
                return render_template('audio-list.html')
            else:
                flash("Error updating audio","Error")
                g.item_selected = file_id
                return render_template('audio-item.html')

        if action == 'item_create':
            file_name = request.form['name']
            description = request.form['description']
            if not g.data_model.AddNewIfNone("audio",file_name,description):
                flash("File name already exists - please use a unique filename","Error")
                return render_template('audio-item.html')

            return render_template('audio-list.html')

    #Default response
    return render_template('audio-list.html')

@app.route('/poc', methods=['GET','POST'])
@safe_route
def poc():
    """Route all entry point updates"""
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        if action =="create":
            return render_template('poc-item.html')
        if action =="edit":
            g.item_selected = request.form['id']
            return render_template('poc-item.html')
        if action == "delete":
            item_selected = request.form['id']
            local.db.Delete("poc",{ "id" : item_selected})
        if action =="synchronise":
            project_item = g.data_model.GetProject(flask_login.current_user.activeProjectId)
            cx_connection = local.cxone.CxOne(project_item['user_key'],project_item['user_secret'])
            if cx_connection.get_token() is not None:
                #We got a token so now let get the bu
                poc_list = cx_connection.GetPocList()
                for key,value in poc_list.items():
                    item_id = g.data_model.AddNewIfNoneEx("poc","name",{ "external_id" : value[0],
                                                                         "name" : key , "description" :  value[2] })
                    if item_id < 0 :
                        local.db.Update("poc", { "external_id" : value[0] , "description" : value[2]}, { "id" : key})
                        flash(f"Linked Existing POC to BU POC - as name already exists - {key}","Information")
            else:
                flash("Unable to connect to CX one - check your credentials","Error")
        #Poc-Item
        if action == "item_create":
            name = request.form['name']
            description = request.form['description']
            if not g.data_model.AddNewIfNone("poc",name,description):
                flash("Entry point name already exists - please use a unique number/name","Error")
                return render_template('poc-item.html')
        if action =="item_update":
            item_id = request.form['id']
            values = g.data_model.BuildItemParamList(request)
            local.db.Update("poc",values,{ "id" : item_id})

    #action =="item_cancel" - just drop through to the poc-list
    return render_template('poc-list.html')

@app.route('/hoo', methods=['GET','POST'])
@safe_route
def hoo():
    """Route all hoo updates"""
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        if action =="create":
            return render_template('hoo-item.html')
        if action =="edit":
            g.item_selected = request.form['id']
            return render_template('hoo-item.html')
        if action == "delete":
            item_selected = request.form['id']
            local.db.Delete("hoo",{ "id" : item_selected})
        if action =="synchronise":
            project_item = g.data_model.GetProject(flask_login.current_user.activeProjectId)
            cx_connection = local.cxone.CxOne(project_item['user_key'],project_item['user_secret'])
            if cx_connection.get_token() is not None:
                #We got a token so now let get the bu
                hoo_list = cx_connection.GetHooList()
                for item in hoo_list:
                    item_id = g.data_model.AddNewIfNoneEx("hoo","name",{ "external_id" : item['hoursOfOperationProfileId'],
                                                                         "name" : item['hoursOfOperationProfileName'], "description" : item['description'] })
                    if item_id < 0:
                        local.db.Update("hoo", { "external_id" : item['hoursOfOperationProfileId'] }, { "id" : item_id})
                        flash(f"Linked Existing HOO to BU Hoo - as name already exists - {item['hoursOfOperationProfileName']}","Information")
            else:
                flash("Unable to connect to CX one - check your credentials","Error")

        #Actions in Hoo-Item
        if action == "item_create":
            name = request.form['name']
            description = request.form['description']
            if not g.data_model.AddNewIfNone("hoo",name,description):
                flash("Hours of operation name already exists - please use a unique name","Error")
                return render_template('hoo-item.html')

        if action =="item_update":
            item_id = request.form['id']
            values = g.data_model.BuildItemParamList(request)
            local.db.Update("poc",values,{ "id" : item_id})

    return render_template('hoo-list.html')

@app.route('/skill', methods=['GET','POST'])
@safe_route
def skill():
    """Route all hoo updates"""
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        if action =="create":
            return render_template('skill-item.html')
        if action =="edit":
            g.item_selected = request.form['id']
            return render_template('skill-item.html')
        if action == "delete":
            item_selected = request.form['id']
            local.db.Delete("skill",{ "id" : item_selected})
        if action =="synchronise":
            project_item = g.data_model.GetProject(flask_login.current_user.activeProjectId)
            cx_connection = local.cxone.CxOne(project_item['user_key'],project_item['user_secret'])
            if cx_connection.get_token() is not None:
                #We got a token so now let get the bu
                skill_list = cx_connection.GetSkillList()
                for item in skill_list:
                    item_id = g.data_model.AddNewIfNoneEx("skill","name",
                                                          { "external_id" : item['skillId'],
                                                            "name" : item['skillName'], 
                                                            "description" : item['campaignName'] })
                    if item_id < 0:
                        local.db.Update("skill", { "external_id" : item['skillId'] },
                                                 { "id" : item_id})
                        flash(f"Linked Existing Skill to BU Skill - as name already exists - {item['skillName']}",
                                "Information")
            else:
                flash("Unable to connect to CX one - check your credentials","Error")
        #Actions in Skill-Item
        if action == "item_create":
            name = request.form['name']
            description = request.form['description']
            if not g.data_model.AddNewIfNone("skill",name,description):
                flash("Skill name already exists - please use a unique name","Error")
                return render_template('skill-item.html')

        if action =="item_update":
            item_id = request.form['id']
            values = g.data_model.BuildItemParamList(request)
            local.db.Update("skill",values,{ "id" : item_id})
    return render_template('skill-list.html')

@app.route('/tools', methods=['GET','POST'])
@safe_route
def tools():
    """Tools page"""
    if request.method == 'GET':
        return render_template('tools-wav.html')
    #POST
    #Check if we are setting connection info:
    action = request.form.get('action')
    action_type = request.form.get('action_type')
    user_name = request.form.get('action_username')
    user_password = request.form.get('action_password')
    if action == "login_connect":
        client = local.cxone.CxOne(user_name,user_password)
        if (user_name == '' or user_password == '') or (client.get_token() is None):
            flash("Invalid credentials to connect to BU - you can still download speech files, without connecting","Information")
            return render_template('tools-wav.html')
        #We have a token so return to client and let them know
        return render_template('tools-wav.html', action_type = action_type, token = client.get_token(), connection_name = client.bu['businessUnitName'])
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
        tts_subscription_key = local.db.GetSetting('tts_key')
        tts = local.tts.Speech(tts_subscription_key)
        tts.get_token()
        audio_response = tts.save_audio(tts_utterance, voice_font)

        print(f'Length={len(audio_response)}')
        #And provide download to user
        with BytesIO(audio_response) as output:
            output.seek(0)
            headers = {"Content-disposition": f"attachment; filename={tts_filename}" }
            return Response(output.read(), mimetype='audio/wav', headers=headers)
    if action == "login_clear":
        return render_template('tools-wav.html')

    flash("Unknown Action","Error")
    return render_template('tools-wav.html')

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
        print(f"Setting active instance {project_instance}")
        #Don't select a project if we are not allowed to!
        local.db.Update("user",{"active_project": project_instance},{ "id" : flask_login.current_user.id})
        flask_login.current_user.activeProject = project_instance
        return redirect('/project')
    else:
        return redirect('/login')

@app.route('/deployment', methods=['GET','POST'])
@safe_route
def deployment():
    """General deployment process"""
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        client = None
        #project = local.db.Select("project","*",{ "id" : g.data_model.project_id})
        match action:
            case "bu_check":
                try:
                    g.data_model.ValidateConnection()
                    if g.data_model.connected_bu_name is not None:
                        flash(f"Successful connection to {g.data_model.connected_bu_name} - this validation will expire in 24 hrs","Information")
                    else:
                        flash("Error connecting to business unit - please check you project key/secret","Error")
                except Exception as e:
                    print (f"Exception {e}")
                    result = "Unknown connection error - please try again later"
                    flash(result,"Error")
            case "package_validate":
                if g.data_model.ValidatePackage():
                    flash("No duplicate scripts identified - package can be deployed","Information")
                else:
                    flash("Duplicate files located on remote server - these scripts be overwritten if you deploy:<br>" + "<br>".join(g.data_model.errors),"Warning")
            case "package_upload":
                if g.data_model.UploadPackage():
                    flash("Package base scripts uploaded","Information")
                else: flash("Something went wrong:<br>" + "<br>".join(g.data_model.errors),"Error")
            case "audio_validate":
                if g.data_model.ValidateAudio():
                    flash("No duplicate audio files located","Information")
                else:
                    flash("Audio files already exist in in destination - upload to overwrite them" + "<br>".join(g.data_model.errors),"Warning")
            case "audio_upload":
                if g.data_model.UploadAudioPackage():
                    flash("Audio has been created and uploaded","Information")
                else:
                    flash("Something went wrong : " + "<br>".join(g.data_model.errors),"Error")
            case "hoo_validate":
                #Sync hoo and then update
                project_item = g.data_model.GetProject(flask_login.current_user.activeProjectId)
                cx_connection = local.cxone.CxOne(project_item['user_key'],project_item['user_secret'])
                if cx_connection.get_token() is not None:
                    #We got a token so now let get the bu
                    hoo_list = cx_connection.GetHooList()
                    for item in hoo_list:
                        item_id = g.data_model.AddNewIfNoneEx("hoo","name",{ "external_id" : item['hoursOfOperationProfileId'],
                                                                         "name" : item['hoursOfOperationProfileName'], "description" : item['description'] })
                        if item_id < 0:
                            local.db.Update("hoo", { "external_id" : item['hoursOfOperationProfileId'] }, { "id" : item_id})
                            flash(f"Linked Existing HOO to BU Hoo - as name already exists - {item['hoursOfOperationProfileName']}","Information")
                else:
                    flash("Unable to connect to CX one - check your credentials","Error")
                #We have synced the HOO now check how many BU do not have external ID
                g.data_model.UploadHoo()
                flash(g.data_model.errors,"info")
            case "sync_skills_validate":
                pass
                #g.data_model.ValidateSkills()
            case "sync_skills_upload":
                pass
            case "addressbook_upload":
                file = request.files['addressbook_file']
                address_name = request.form.get('addressbook_name')
                file.stream.seek(0)
                wrapper = io.TextIOWrapper(file.stream,  encoding="utf-8", )
                data_list = ReadDataList(wrapper)

                client = None
                if (client is not None and client.get_token() is not None):
                    client.CreateAddressBook(address_name,{ "addressBookEntries" : data_list})
                    flash("Address book uploaded","Information")
                else:
                    flash("Error Uploading Address book","Error")
            case "dnis":
                switch_statement = g.data_model.ExportDnisSwitch()
                return switch_statement.replace('\n', '<br>')
            case "queue":
                queue_statement = g.data_model.ExportQueueSwitch()
                return queue_statement
            case _:
                flash("We haven't got that working yet","Information")

        return render_template('deployment.html')

    #Must be a standard GET request
    if not g.data_model.IsValidated("connection"):
        flash("You have not verified your project connection to the business unit recently - please validate before continuing")
    return render_template('deployment.html')

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
@safe_route
def download(filename):
    """Used to get files from local directory as needed in TTS - defaults to default directory"""
    download_path = os.path.join(app.root_path, 'packages//default')
    return send_from_directory(download_path, filename, mimetype='text/plain',as_attachment = True)

def ReadDataList(file_stream):
    """Helper function to read tsv and build a list of dict for eack line"""
    headers = str(file_stream.readline()).strip().split('\t')
    # Read the remaining lines
    data_list = []
    for line in file_stream.readlines():
        values = line.strip().split('\t')
        #Supported column names here:
        #https://developer.niceincontact.com/API/AdminAPI#/AddressBook/Create%20Address%20Book%20Entries
        data_dict = dict(zip(headers, values))
        data_list.append(data_dict)
    return data_list

if __name__ == '__main__':
    app.run()
