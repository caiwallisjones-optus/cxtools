################################################################################
#
#   Author:         Cai Wallis-Jones
#   Description:    Simple CX one call flow builder
#   Version:        Unreleased
#   Date:           30/01/24
#   See Readme.txt for more details
#
################################################################################

import os
import shutil
import io
import functools
import traceback

import flask_login
from flask import (Flask, redirect, render_template, request,send_from_directory, url_for,send_file,Response, flash)

#from configparser import ConfigParser
from io import BytesIO

#Make sure that flask_login and bcrypt are installed


#Local files:
import local.db
import local.io
import local.tts
import local.cxone
import local.datamodel

newAppSetup = False

if (os.path.isfile(local.db.dbname) != True):
    print('New Setup detected')
    newAppSetup = True

#Init DB - create as needed
dbInit = local.db.init_db()

#Start our web service app
app = Flask(__name__)
app.secret_key = 'MySecretKey'

#https://pypi.org/project/Flask-Login/
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

#Our flask_login code
class User(flask_login.UserMixin):
    id = None
    email = None
    activeProjectId =  None
    projects = []
    securityMap = None
    pass

#Special debug for routes - returns errorlog
def safe_route(func):
    #"""Print the function signature and return value"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):
        try:
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            print(f"{func.__name__} >> ({signature})")
            value = func(*args, **kwargs)
            #print(f"{func.__name__}() << {repr(value)}")
            print(f"<< {func.__name__}() <<")
            return value
        except Exception as e:
            print("Exception: ", e)
            traceback.print_exc()
            return render_template('project-list.html', projects = local.db.GetProjectList(flask_login.current_user.id))
    return wrapper_debug

@login_manager.user_loader
def user_loader(id):
    print('User loader for %s' % id )
    if local.db.GetUserLoginIsValid(id) != 1 :
        print('Invalid user load for ID %s' % id )
        return
  
    result = local.db.GetUserStatus(id)
    user = User()
    user.id  = result[0]
    user.email = result[1]
    user.projects = dict()
    projectlist = local.db.GetProjectList(user.id)
    for project in projectlist:
        user.projects[project[0]] = project[4]

    #TODO we assume we have a project created
    if result[3] == "None":
        user.activeProjectId = list(user.projects.keys())[0]
    else:
        user.activeProjectId = result[3]

    return user

@login_manager.request_loader
def request_loader(request):
    email = request.form.get('email')

    print('Request loader for %s' % email )
    if local.db.GetUserLoginIsValid(email) != 1 :
        return
  
    result = local.db.GetUserStatus(email)
    user = User()
    user.id  = result[0]
    user.email = result[1]
    user.projects = dict()
    projectlist = local.db.GetProjectList(user.id)
    for project in projectlist:
        user.projects[project[0]] = project[4]

    #TODO we assume we have a project created
    if result[3] == "None":
        user.activeProjectId = list(user.projects.keys())[0]
    else:
        user.activeProjectId = result[3]

    return user

@login_manager.unauthorized_handler
def unauthorized_handler():
    return 'Unauthorized', 401

#Routing
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/')
def index():
   #print("/ as user %s " % flask_login.current_user.id)
   if flask_login.current_user.is_authenticated:
       print('User authenticated - check user has active projects')
       print("/ as user %s " % flask_login.current_user.email)

       if local.db.GetProjectCount(flask_login.current_user.id) > 0:
         return redirect('/projects')
       else:
         return render_template('project-item.html', item = None, errMsg = "You have no active projects - please create a new project" )
       
   else:
       #We may not have initiated config
       if newAppSetup == True:
           print('newAppSetup')
           return redirect ('/setup')
       else:
           print('User not authenticated - redirect to login')
           return redirect('/login')

@app.route('/setup', methods = ['GET', 'POST'])
def setup():
    print('Setup called')
    if request.method == 'GET':
        return render_template('setup.html')
    else:
        print('Creating user login')
        #Lets create our new user ID and set the azure TTS key
        email = request.form['email']
        password = request.form['password']
        tts_key = request.form['tts_key']

        local.db.AddSetting("tts_key",tts_key)
        local.db.AddUser(email, password)
        newAppSetup == False

        return redirect('/login')

@app.route('/login', methods = ['GET', 'POST'])
def login():
   if request.method == 'GET':
      #print("/login GET")
      return render_template('login.html')

   #Must be a post - lets log em in
   email = request.form['email']
   #print("/login POST for ")
   print('Checking access for user %s' % email)
   userId = local.db.GetUserAuth(email, request.form['password'])
   if userId is not None:
        print('Successful auth for ', email)
        
        user = User()
        result = local.db.GetUserStatus(userId)

        user.id  = result[0]
        user.email = result[1]
        user.projects = dict()
        projectlist = local.db.GetProjectList(user.id)
        for project in projectlist:
            user.projects[project[0]] = project[4]

        #TODO we assume we have a project created
        if result[3] == "None":
            user.activeProjectId = list(user.projects.keys())[0]
        else:
            user.activeProjectId = result[3]

        flask_login.login_user(user, remember=True  )

        return redirect('/')

   #login failed
   return render_template('login.html', errMsg = "Invalid username or password - please try again!!")

@app.route('/projects', methods=['GET','POST'])
@safe_route
def projects():
    
    print("/projects as user %s " % flask_login.current_user.email)
    if request.method =="GET":
        print("Getting projects from DB")
        return render_template('project-list.html', projects = local.db.GetProjectList(flask_login.current_user.id))
    
    #POST:
    action = request.form['action'] # get the value of the clicked button
    print("POST action % s " % action)
    if action =="new":
        return render_template('project-item.html', item = None )
    
    if action =="edit":
        id = request.form['id'] # get the value of the clicked button
        item = local.db.GetProject(id)
        return render_template('project-item.html', item = item )
    
    if action =="delete":
        id = request.form['id'] # get the value of the clicked button
        projectCount = local.db.GetProjectCount(flask_login.current_user.id)
        print("Project count %s" % projectCount)
        if projectCount < 2:
            print("Delete item request failed")
            return render_template('project-list.html', projects = local.db.GetProjectList(flask_login.current_user.id), errMsg = "You cannot delete your last project - create a new project first")
        else:
            local.db.DeleteProject(id)
            return render_template('project-list.html', projects = local.db.GetProjectList(flask_login.current_user.id) )
    
    if action =="create":
        err_msg = None
        try:
            #Create new project details
            shortname = request.form['shortname']
            instancename =  request.form['instancename']
            buid =  request.form['buid']
            description = request.form['description']
            ttsvoice = request.form['ttsvoice']
            deploymenttype = request.form['deploymenttype']
            userkey = request.form['userkey']
            usersecret = request.form['usersecret']

            print(f'Creating project for {shortname}')
            print(f'Created by user ID {flask_login.current_user.id}')
        
            project_id = local.db.AddProject(flask_login.current_user.id, flask_login.current_user.email, shortname, instancename,buid,description,ttsvoice,deploymenttype,userkey,usersecret)
            if  project_id is not None:
                #Add default wav files to project ID
                print(f'Generating standard WAV records for project')
                sysAudio = local.io.GetSystemAudioFileList(deploymenttype.lower())
                for key in sysAudio:
                    print(key)
                    local.db.AddAudioFile(project_id,key,sysAudio[key],True)
        except Exception as e:
            print ('Error exception %s' % e)
            err_msg = e
            print (e)
            err_msg = "Something went wrong creating project"
            return render_template('project-list.html', projects = local.db.GetProjectList(flask_login.current_user.id),errMsg = err_msg)

        print(f'Setting user active instance {project_id}')
        flask_login.current_user.activeProject = project_id
        local.db.SetUserProject(flask_login.current_user.id,project_id)
            
        return render_template('project-list.html', projects = local.db.GetProjectList(flask_login.current_user.id),errMsg = err_msg)
        
    if action =="update":
        id = request.form['id']
        shortname = request.form['shortname']
        instancename =  request.form['instancename']
        buid =  request.form['buid']
        description = request.form['description']
        ttsvoice = request.form['ttsvoice']
        deploymenttype = request.form['deploymenttype']
        userkey = request.form['userkey']
        usersecret = request.form['usersecret']

        print("Updating project details for %s " % shortname)
        print("Updating user ID is %s " % flask_login.current_user.id)
        #UpdateProject(project_id,shortname,instancename,buid,description,ttsvoice,deploymenttype,userkey,usersecret) 
        errMsg = local.db.UpdateProject(id, shortname, instancename,buid,description,ttsvoice,deploymenttype,userkey,usersecret)
        myProjects =  local.db.GetProjectList(flask_login.current_user.id)
        return render_template('project-list.html', projects = myProjects , errMsg = errMsg)
        
        #Set the users active to the requested project name
        flask_login.current_user.activeProject = project.ShortName

    if action =="connect":
        id = request.form['id'] # get the value of the clicked button
        item = local.db.GetProject(id)
        cx_conn = local.cxone.CxOne(item[10],item[11])
        if (cx_conn.get_token()):
            #We got a token so now let get the bu
            bu = cx_conn.GetBusinessUnit()
            buid = bu['businessUnitId']
            print ("BUID - " + str(buid) )
            if (item[6] ==  str(buid)):
                local.db.UpdateProjectConnection(item[0],True)
                return render_template('project-list.html', projects = local.db.GetProjectList(flask_login.current_user.id))
            else:
                return render_template('project-list.html', projects = local.db.GetProjectList(flask_login.current_user.id), errMsg = "Unable to validate BU settings for business unit " + item[6])
        else:
            list =  local.db.GetProjectList(flask_login.current_user.id)
            return render_template('project-list.html', projects = local.db.GetProjectList(flask_login.current_user.id), errMsg = "Unable to validate key settings")

    #Projects fallback
    list =  local.db.GetProjectList(flask_login.current_user.id)
    return render_template('project-list.html', projects = list)

@app.route('/queues', methods=['GET','POST'])
def queues():
    if request.method == 'GET':
        #print("Getting queue from DB")
        hooList = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        queues = local.db.GetQueueList(flask_login.current_user.activeProjectId)
        return render_template('queue-list.html', queues = queues, hooList = hooList, skillList =skillList)
    
    #POST:
    action = request.form['action'] # get the value of the clicked button
    print("POST action % s " % action)
    if action =="new":
        hoolist = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('queue-item.html', item = None, hooList = hoolist, skillList = skillList )
   
    if action =="edit":
        id = request.form['id'] # get the value of the clicked button
        item = local.db.GetQueue(id)
        hoolist = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        actions = local.db.GetQueueActionsList(id)
        return render_template('queue-item.html', item = item, actions= actions, hooList = hoolist, skillList = skillList )

    if action == "delete":
        id = request.form['id'] # get the value of the clicked button
        local.db.DeleteQueue(id)
        return render_template('queue-list.html', queues = local.db.GetQueueList(flask_login.current_user.activeProjectId))
    
    ######
    ##          Queue-Item Actions
    ######
    if action == "queue_new":
        #Create new queue details
        queue_name = request.form['name']
        #queue_skills =  request.form['attachedskills']
        #queue_hoo =  request.form['hoo']
        
        print("Creating queue details for %s " % queue_name)
        print("Creating user ID is %s " % flask_login.current_user.id)
        print("Creating project ID is %s " % flask_login.current_user.activeProjectId)
        
        queueId = local.db.AddQueue(flask_login.current_user.activeProjectId,queue_name,"","")

        item = local.db.GetQueue(queueId)
        hoolist = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('queue-item.html', item = item, hooList = hoolist, skillList = skillList )
    
    if action =="queue_update":
        queue_id = request.form['id']
        queue_name = request.form['name']
        queue_skills =  request.form['attachedskills']
        queue_hoo =  request.form['hoo']

        print("Updating queue details for %s " % queue_name)
        print("QueueHoo %s" % queue_hoo)
        errMsg = local.db.UpdateQueue(queue_id,queue_name,queue_skills,queue_hoo)
        
        queues = local.db.GetQueueList(flask_login.current_user.activeProjectId)
        hooList = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        queues = local.db.GetQueueList(flask_login.current_user.activeProjectId)
        return render_template('queue-list.html', queues = queues, hooList = hooList, skillList =skillList, errMsg = errMsg)
      
    if action =="queue_cancel":
        return redirect('/queues' )    
    
    #Action updates from Queue-Item:
    if action =="queue_item_skill_new":
        #Append queueskill to list (table id!)
        id = request.form['id'] # get the value of the clicked button
        item = local.db.GetQueue(id)

        queue_name = item[2]
        queue_skills =  item[3]
        queue_hoo = item[4]
        queue_newskill = request.form['new_skill']
        skill_array = queue_skills.split(",")
        if (queue_newskill not in skill_array):
            skill_array.append(queue_newskill)
            while '' in skill_array:
                skill_array.remove('')
            queue_skills = (",").join(skill_array)


        print("Updating queue details for %s " % queue_name)
        
        errMsg = local.db.UpdateQueue(id,queue_name,queue_skills,queue_hoo)
        
        #item = local.db.GetQueue(id)
        hoolist = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        actions = local.db.GetQueueActionsList(str(id))
        item = local.db.GetQueue(id)
        return render_template('queue-item.html', item = item, actions= actions, hooList = hoolist, skillList = skillList )
    
    if action =="queue_item_skill_remove":

        id = request.form['id']
        queue_name = request.form['name']
        queue_skills =  request.form['attachedskills']
        queue_hoo = request.form['hoo']
        queue_skillremove = request.form['skill_remove']
        print("Removing: %s" % queue_skillremove)
        skill_array = queue_skills.split(",")
        if (queue_skillremove in skill_array):
           skill_array.remove(queue_skillremove)
           queueskills = (",").join(skill_array)

        print("**Updating queue details for %s " % queue_name)
        print("**QueueHoo %s" % queue_name)
        errMsg = local.db.UpdateQueue(id,queue_name,queueskills,queue_hoo)

        item = local.db.GetQueue(id)
        hoolist = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        actions = local.db.GetQueueActionsList(id)
        return render_template('queue-item.html', item = item, actions= actions, hooList = hoolist, skillList = skillList )
    
    
    if action == "queue_action_new":
        #Create new queue action - this is called from the queue-item html
        queue_id = request.form['id']    
        return render_template('queueaction-item.html', item = None, queue_id = queue_id)
    
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
        hoolist = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('queue-item.html', item = None, actions = local.db.GetQueueActionsList(queue_id), hooList = hoolist, skillList = skillList )

    if action =="queue_action_up":
        return ("Not Built yet TODO - 00003 " + action)
    if action =="queue_action_down":
        return ("Not Built yet TODO - 00004 " +  action)
    
    #Action updates from QueueAction-Item:
    if action =="queueaction_create":
        #Create new queue action(blank)
        queue_id = request.form['queue_id']     
        #errMsg = local.db.AddQueueAction(id)
        queue_action = request.form['queueaction']   
        param1 =  request.form['param1']
        param2 =  request.form['param2']
        print('Param 1 % s ' % param1)
        print('Param 2 % s' % param2)
        local.db.AddQueueAction(queue_id,queue_action,param1,param2)
        item = local.db.GetQueue(queue_id)
        hoolist = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id), hoolist=hoolist, skillList = skillList)
    
    if action =="queueaction_update":
        action_id = request.form['id'] 
        queue_action = request.form['queueaction']   
        param1 =  request.form['param1']
        param2 =  request.form['param2']
        local.db.UpdateQueueAction(action_id,queue_action,param1,param2)

        queue_id = request.form['queue_id'] 
        item = local.db.GetQueue(queue_id)
        hoolist = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id), hooList=hoolist, skillList = skillList)

    if action =="queueaction_cancel":
        queue_id = request.form['queue_id'] 
        item = local.db.GetQueue(queue_id)    
        hoolist = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id), hooList=hoolist, skillList = skillList)

    #Queue Hoo Operations
    if action =="queue_item_inqueueaction_new":
        queue_id = request.form['id'] 
        state = request.form['inqueueState'] 
        action_type = request.form['inqueueStateAction'] 
        params = request.form['inqueueStateParams'] 

        local.db.UpdateQueueHooActions(queue_id,'QUEUE',state,action_type,params)
        item = local.db.GetQueue(queue_id)    
        hooList = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id), hooList=hooList, skillList = skillList)
        
    if action =="queue_item_prequeueaction_new":
        queue_id = request.form['id'] 
        state = request.form['prequeueState'] 
        action_type = request.form['prequeueStateAction'] 
        params = request.form['prequeueStateParams'] 

        local.db.UpdateQueueHooActions(queue_id,'PREQUEUE',state,action_type,params)
        item = local.db.GetQueue(queue_id)    
        hooList = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id), hooList=hooList, skillList = skillList)
    
    if action == "queue_item_prequeueaction_remove":
        queue_id = request.form['id'] 
        actionToRemove = request.form['queue_item_prequeueaction_remove'] 
        local.db.DeleteQueueHooAction(queue_id,'QUEUE',actionToRemove)

        item = local.db.GetQueue(queue_id)    
        hooList = local.db.GetHooList(flask_login.current_user.activeProjectId)
        skillList = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('queue-item.html', item = item, actions = local.db.GetQueueActionsList(queue_id), hooList=hooList, skillList = skillList)

@app.route('/callflow', methods=['GET','POST'])
@safe_route
def CallFlow():
    data_model = local.datamodel.DataModel(flask_login.current_user.id,flask_login.current_user.activeProjectId)
    
    #Get All call flow for current project
    if request.method == 'GET':
        list = local.db.GetCallFlowList(data_model.project_id)
        return render_template('callflow-list.html',  items = list)
    
    #POST:
    action = request.form['action'] # get the value of the clicked button
    print("CallFlow POST action % s " % action)
    
    if action =="new":
        return render_template('callflow-item.html',  item = None, action_item = None, action_responses = None)
   
    if action =="edit":
        id = request.form['id'] # get the value of the clicked button
        item = local.db.GetCallFlow(id)
        if (item[5] is not None):
            action_item = local.db.GetCallFlowAction(item[5])
            action_responses = local.db.GetCallFlowActionResponses(action_item[0])
            return render_template('CallFlow-item.html',  item = item, action_item = action_item, action_responses = action_responses, data_model = data_model)
        
        return render_template('CallFlow-item.html',  item = item, action_item = None, action_responses = None)
    
    if action == "delete":
        id = request.form['id'] # get the value of the clicked button
        local.db.DeleteCallFlow(id)
        list = local.db.GetCallFlowList(flask_login.current_user.activeProjectId)
        return render_template('CallFlow-list.html',  items = list)
    
    ######
    ##          CallFlow-Item Actions
    ######
    if action == "item_new":
        #Create new queue details
        callflow_name = request.form['name']
        callflow_description =  request.form['description']
        
        errMsg = local.db.AddCallFlow(flask_login.current_user.activeProjectId,callflow_name,callflow_description)
        if errMsg.isnumeric():
            item = local.db.GetCallFlow(errMsg)
            return render_template('CallFlow-item.html',  item = item, action_item = None, action_responses = None,data_model = data_model)
        else:
            return render_template('CallFlow-item.html',  item = None, action_item = None, action_responses = None, errMsg = errMsg, data_model = data_model)
       
    if action =="item_update":
        #Update Name and description as needed
        call_flow_id = request.form['id']
        call_flow_name = request.form['name']
        call_flow_description =  request.form['description']
        errMsg = local.db.UpdateCallFlow({'name': call_flow_name,'description': call_flow_description },{'id' : call_flow_id })
        
        #Update the current action as needed
        call_flow_action_id = request.form.get('action_id',None)
        if not(call_flow_action_id is None or call_flow_action_id == ''):
            call_flow_action_name = request.form['action_name']
            call_flow_action_type = request.form['action_type']
            ##TODO: work on multiple params
            call_flow_action_param1 = request.form.get('action_param_0',None)
            call_flow_action_param2 = request.form.get('action_param_1',None)
            call_flow_action_param3 = request.form.get('action_param_2',None)
            call_flow_action_param3 = request.form.get('action_param_3',None)
            call_flow_action_param3 = request.form.get('action_param_4',None)
            #build param list
            action_params = data_model.BuildParamList(call_flow_action_type, (call_flow_action_param1,call_flow_action_param2,call_flow_action_param3) )
            params = {'name' : call_flow_action_name,'action': call_flow_action_type, 'params' : action_params}
            filter = {'id' : call_flow_action_id}
            local.db.UpdateCallFlowAction(params,filter)
        
        item = local.db.GetCallFlow(call_flow_id)
        action_item = local.db.GetCallFlowAction(call_flow_action_id)
        action_responses = local.db.GetCallFlowActionResponses(action_item[0])
            
        return render_template('CallFlow-item.html',  item = item, action_item = action_item, action_responses = action_responses, data_model = data_model)
    
        
    
    if action =="item_cancel":
        return redirect('/callflow' )    
    
    if action =="action_new":
        id = request.form['id']
        item = local.db.GetCallFlow(id)
        #Now build the param list for the actions
        action_id = request.form['action_id']
        action_type = request.form['action_type']
        action_parent = 0
        if action_id == '':
            action_name = "BEGIN"
        else:
            action_name = "Action"
        if not(action_id is None or action_id == ''):
            # We need to update the action with the actiontype - and for this we only set the action_type
            params = {'action': action_type}
            filter = {'id' : action_id}
            local.db.UpdateCallFlowAction(params,filter)

            #Add default action as needed
            item = local.db.GetCallFlow(id)
            action_item = local.db.GetCallFlowAction(action_id)
            if data_model.GetActionHasDefaultResponse(action_type):
                local.db.AddActionResponse(item[0],action_item[0],"DEFAULT",None)

            action_responses = local.db.GetCallFlowActionResponses(action_item[0])
            
            return render_template('CallFlow-item.html',  item = item, action_item = action_item, action_responses = action_responses, data_model = data_model)
    
        else:

            #Moving the config to when we have created the action
            action_added = local.db.AddCallFlowAction(id,action_parent,action_name,action_type,"")
            #And set the child id as its our first:
            local.db.UpdateCallFlow({'name': item[2],'description': item[3] , 'callFlowAction_id' : action_added },{'id' : id })

            item = local.db.GetCallFlow(id)
            action_item = local.db.GetCallFlowAction(action_added)
            if data_model.GetActionHasDefaultResponse(action_type):
                local.db.AddActionResponse(item[0],action_item[0],"DEFAULT",None)
                action_responses = local.db.GetCallFlowActionResponses(action_item[0])
            
        return render_template('CallFlow-item.html',  item = item, action_item = action_item, action_responses = action_responses, data_model = data_model)
    
    if action == "action_response_new":
        callflow_id = request.form['id']
        action_id = request.form['action_id']
        action_response = request.form['action_response_new']
        
        #Add response for action_id
        local.db.AddActionResponse(callflow_id,action_id,action_response,None)

        item = local.db.GetCallFlow(callflow_id)
        action_item = local.db.GetCallFlowAction(action_id)
        action_responses = local.db.GetCallFlowActionResponses(action_item[0])
        return render_template('CallFlow-item.html',  item = item, action_item = action_item, action_responses = action_responses, data_model = data_model)

    if action.startswith("action_response_create_"):
        #Create a new response and update the existing response
        callflow_id = request.form['id']
        action_id = request.form['action_id']
        action_response_id = action.removeprefix("action_response_create_")
        new_action = local.db.AddCallFlowAction(callflow_id,action_id,"Action"+action_id ,"","")
        ##Set the response to our new action
        local.db.UpdateCallFlowActionResponse(action_response_id,new_action)

        item = local.db.GetCallFlow(callflow_id)
        action_item = local.db.GetCallFlowAction(new_action)
        action_responses = local.db.GetCallFlowActionResponses(new_action[0])
        return render_template('CallFlow-item.html',  item = item, action_item = action_item, action_responses = action_responses, data_model = data_model)
    
    if action.startswith("action_response_select_"):
        callflow_id = request.form['id']
        #action_id = request.form['action_id']
        
        action_response_id = action.removeprefix("action_response_select_")
        #Get action response Id to get next action Id
        response = local.db.GetCallFlowActionResponse(action_response_id)
        
        item = local.db.GetCallFlow(callflow_id)
        action_item = local.db.GetCallFlowAction(response[4])
        action_responses = local.db.GetCallFlowActionResponses(action_item[0])
        return render_template('CallFlow-item.html',  item = item, action_item = action_item, action_responses = action_responses, data_model = data_model)
        pass
       
    return ("Not Built yet TODO - /callflow POST % s " % action)

@app.route('/audio', methods=['GET','POST'])
def audio():
    if request.method == 'GET':
        filelist = local.db.GetAudioList(flask_login.current_user.activeProjectId)
        return render_template('audiofile-list.html', audiofiles = filelist)

    else:
        action = request.form['action'] # get the value of the clicked button
        #Common actions, no ID
        if action == 'new':
            return render_template('audiofile-item.html', item = None )
        
        if action == 'download':
            file_id = request.form['id'] # get the value of the item associated with the button
            file = local.db.GetAudio(file_id)

            print('Request for text to speech with a filename=%s' % file[2])
            sub_key = local.db.GetSetting("tts_key")
            voice_font = "en-AU-NatashaNeural"
       
            tts = local.tts.Speech(sub_key)
            if (tts.get_token()==False):
                return render_template('audiofile-list.html',audiofiles = filelist, errMsg = "Error connecting to Azure for TTS key - please try again later")
            
            audio_response = tts.save_audio(file[3], voice_font)
            print('Length=%s' % len(audio_response))
            #https://stackoverflow.com/questions/69076959/send-a-file-to-the-user-then-delete-file-from-server/69080438#69080438
            #A better way??

            with BytesIO(audio_response) as output:
                output.seek(0)
                headers = {"Content-disposition": "attachment; filename=%s.wav" % file[2] }
                return Response(output.read(), mimetype='audio/wav', headers=headers)
        
        if action == 'import':
            filelist = local.db.GetAudioList(flask_login.current_user.activeProjectId)
            return render_template('audiofile-list.html',audiofiles = filelist, errMsg = "Import feature is not implemented yet")
        

        if action == 'edit':
            file_id = request.form['id'] # get the value of the item associated with the button
            file = local.db.GetAudio(file_id)
            return render_template('audiofile-item.html', item = file)

        if action == 'update':
            file_id = request.form['id']
            file_name = request.form['name']
            wording = request.form['wording']
            if local.db.UpdateAudio(file_id, file_name, wording):
                filelist = local.db.GetAudioList(flask_login.current_user.activeProjectId)
                return render_template('audiofile-list.html', audiofiles = filelist)  
            else:
                errMsg ="Error updating file please use a proper file name"
                file = local.db.GetAudio(file_id)
                return render_template('audiofile-item.html', item = file)
            
                

        if action == 'create':
            file_name = request.form['name']
            wording = request.form['wording']
            local.db.AddAudioFile(flask_login.current_user.activeProjectId, file_name, wording,False)
            filelist = local.db.GetAudioList(flask_login.current_user.activeProjectId)
            return render_template('audiofile-list.html', audiofiles = filelist)  

        filelist = local.db.GetAudioList(flask_login.current_user.activeProjectId)
        return render_template('audiofile-list.html', audiofiles = filelist)

@app.route('/poc', methods=['GET','POST'])
def poc():
    if request.method == 'GET':
        list = local.db.GetPocList(flask_login.current_user.activeProjectId)
        buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12])
        return render_template('poc-list.html',  items = local.db.GetPocList(flask_login.current_user.activeProjectId), buConnected = buConnected)
    
    #POST:
    action = request.form['action'] # get the value of the clicked button
    print("POST action % s " % action)
    
    if action =="new":
        return render_template('poc-item.html', item = None)
    
    if action =="edit":
        id = request.form['id'] # get the value of the clicked button
        item = local.db.GetPoc(id)
        return render_template('poc-item.html', item = item)

    if action == "delete":
        id = request.form['id'] # get the value of the clicked button
        local.db.DeletePoc(id)
        list = local.db.GetPocList(flask_login.current_user.activeProjectId)
        return render_template('poc-list.html', items = list)
    
    if action =="import":
        item = local.db.GetProject(flask_login.current_user.activeProjectId)
        cx_conn = local.cxone.CxOne(item[10],item[11])
        if (cx_conn.get_token()):
            #We got a token so now let get the bu
            poc = cx_conn.GetPocInfo()
            print(poc)
            poc = dict(sorted(poc.items()))
            for key,values in poc.items():
                #consolidated_list[poc['contactAddress']] = (poc['contactCode'], poc['isActive'], poc['scriptName'])
                e164_address = key
                cxone_id = values[0]
                scriptName = values[2]
                #TODO Check if this already exists and update instead of add
                #if local.db.GetHooByExternalId():
                    #local.db.UpdateHoo(hoo,profileId,True,profileName,description)
                #else:
                local.db.AddPoc(flask_login.current_user.activeProjectId,cxone_id,True,e164_address,scriptName)
            list = local.db.GetPocList(flask_login.current_user.activeProjectId)
            buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12])
            return render_template('poc-list.html',  items = local.db.GetPocList(flask_login.current_user.activeProjectId), buConnected = buConnected)
        else:
            list = local.db.GetHooList(flask_login.current_user.activeProjectId)
            buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12])
            return render_template('poc-list.html',  items = list, buConnected = buConnected, errMsg ="Error connecting to CX One please verify connection")

    #Actions in POC-Item
    if action == "item_new":
        #Create new queue details
        name = request.form['name']
        notes =  request.form['notes']
        
        errMsg = local.db.AddPoc(flask_login.current_user.activeProjectId,"",False,name,notes)
        return render_template('poc-list.html', items = local.db.GetPocList(flask_login.current_user.activeProjectId))
    
    
    if action =="item_update":
        return ("Not Built yet TODO - /poc POST ")
    
    if action =="item_cancel":
        return redirect('/poc' ) 
      
    return ("Not Built yet TODO - /poc POST ")

@app.route('/hoo', methods=['GET','POST'])
def hoo():
    if request.method == 'GET':
        list = local.db.GetHooList(flask_login.current_user.activeProjectId)
        result = local.db.GetProject(flask_login.current_user.activeProjectId)[12]
        print("TESTING" + str(result))
        return render_template('hoo-list.html',  items = list, buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12]))
    
    #POST:
    action = request.form['action'] # get the value of the clicked button
    print("HOO POST action % s " % action)
    
    if action =="new":
        
        return render_template('hoo-item.html', item = None)
    
    if action =="edit":
        id = request.form['id'] # get the value of the clicked button
        item = local.db.GetHoo(id)
        return render_template('hoo-item.html', item = item)

    if action == "delete":
        id = request.form['id'] # get the value of the clicked button
        local.db.DeleteHoo(id)
        list = local.db.GetHooList(flask_login.current_user.activeProjectId)
        return render_template('hoo-list.html', items = list)
    
    if action =="import":
        item = local.db.GetProject(flask_login.current_user.activeProjectId)
        cx_conn = local.cxone.CxOne(item[10],item[11])
        if (cx_conn.get_token()):
            #We got a token so now let get the bu
            hoo = cx_conn.GetHooInfo()
            for item in hoo:
                profileId = item['hoursOfOperationProfileId']
                profileName = item['hoursOfOperationProfileName']
                description = item['description']
                #TODO Check if this already exists and update instead of add
                #if local.db.GetHooByExternalId():
                    #local.db.UpdateHoo(hoo,profileId,True,profileName,description)
                #else:
                local.db.AddHoo(flask_login.current_user.activeProjectId,profileId,True,profileName,description)
            list = local.db.GetHooList(flask_login.current_user.activeProjectId)
            result = local.db.GetProject(flask_login.current_user.activeProjectId)[12]
            return render_template('hoo-list.html',  items = list, buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12]))
        else:
            list = local.db.GetHooList(flask_login.current_user.activeProjectId)
            result = local.db.GetProject(flask_login.current_user.activeProjectId)[12]
            return render_template('hoo-list.html',  items = list, buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12]), errMsg ="Error connecting to CX One please verify connection")

            
            return render_template('hoo-list.html', items = list)

    #Actions in Hoo-Item
    if action == "item_new":
        #Create new queue details
        name = request.form['name']
        notes =  request.form['notes']
        
        errMsg = local.db.AddHoo(flask_login.current_user.activeProjectId,"",False,name,notes)
        return render_template('hoo-list.html', items = local.db.GetHooList(flask_login.current_user.activeProjectId))
        
    if action =="item_update":
        item_id = request.form['id']
        hoo_name = request.form['name']
        hoo_description = request.form['notes']
        if local.db.UpdateHoo(item_id,"","",hoo_name,hoo_description):
            items = local.db.GetHooList(flask_login.current_user.activeProjectId)
            return render_template('hoo-list.html', items = items)  
        else:
            errMsg ="Error updating file please use a proper file name"
            item = local.db.GetHoo(item_id)
            return render_template('hoo-item.html', item = item)
    
    if action =="item_cancel":
        return redirect('/hoo' ) 
      
    return ("Not Built yet TODO - /hoo POST ")
    
@app.route('/skill', methods=['GET','POST'])
def skill():
    if request.method == 'GET':
        list = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('skill-list.html',  items = list, buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12]))
    
    #POST:
    action = request.form['action'] # get the value of the clicked button
    print("HOO POST action % s " % action)
    
    if action =="new":
        return render_template('skill-item.html', item = None)
    
    if action =="edit":
        id = request.form['id'] # get the value of the clicked button
        item = local.db.GetSkill(id)
        return render_template('skill-item.html', item = item)

    if action == "delete":
        id = request.form['id'] # get the value of the clicked button
        local.db.DeleteSkill(id)
        list = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('skill-list.html',  items = list, buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12]))
    

    if action == "import":
        item = local.db.GetProject(flask_login.current_user.activeProjectId)
        cx_conn = local.cxone.CxOne(item[10],item[11])
        if (cx_conn.get_token()):
            #We got a token so now let get the bu
            skill = cx_conn.GetSkillInfo()
            for item in skill:
                skillId = item['skillId']
                skillName = item['skillName']
                skillNotes = item['campaignName']
                #TODO Check if this already exists and update instead of add
                #if local.db.GetHooByExternalId():
                    #local.db.UpdateHoo(hoo,profileId,True,profileName,description)
                #else:
                if ((item['isOutbound'] == False) and  (item['isActive']==True )):
                    local.db.AddSkill(flask_login.current_user.activeProjectId,skillId,True,skillName,skillNotes)
            
            list = local.db.GetSkillList(flask_login.current_user.activeProjectId)
            return render_template('skill-list.html',  items = list, buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12]))
        else:
            list = local.db.GetSkillList(flask_login.current_user.activeProjectId)
            return render_template('skill-list.html',  items = list, buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12]), errMsg ="Error connecting to CX One please verify connection")

    #Actions in Skill-Item
    if action == "item_new":
        #Create new queue details
        name = request.form['name']
        notes =  request.form['notes']
        
        errMsg = local.db.AddSkill(flask_login.current_user.activeProjectId,"",False,name,notes)
        list = local.db.GetSkillList(flask_login.current_user.activeProjectId)
        return render_template('skill-list.html',  items = list, buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12]))
    
    if action =="item_update":
        item_id = request.form['id']
        name = request.form['name']
        notes = request.form['notes']
        if local.db.UpdateSkill(item_id,None,None,name,notes):
            list = local.db.GetSkillList(flask_login.current_user.activeProjectId)
            return render_template('skill-list.html',  items = list, buConnected = bool(local.db.GetProject(flask_login.current_user.activeProjectId)[12]))
        else:
            errMsg ="Error updating file please use a proper file name"
            item = local.db.GetHoo(item_id)
            return render_template('hoo-item.html', item = item)
    
    if action =="item_cancel":
        return redirect('/skill' ) 
      
    return ("X-Not Built yet TODO - /skill POST % s" % action)

@app.route('/tools', methods=['GET','POST'])
def tools():
    print('Request for tools page received')
    if request.method == 'GET':
       return render_template('tools.html')
   
    Filename = request.form.get('filename')
    TtsData = request.form.get('ttsdata')
              
    print('Filename=%s' % Filename)
    print('TtsData=%s' % TtsData)

    if Filename:
       print('Request for text to speech with a filename=%s' % Filename)
       text_input = TtsData
       sub_key = local.db.GetSetting('tts_key')
       voice_font = "en-AU-NatashaNeural"
       
       tts = local.tts.Speech(sub_key)
       tts.get_token()
       audio_response = tts.save_audio(text_input, voice_font)
       
       print('Length=%s' % len(audio_response))
       #https://stackoverflow.com/questions/69076959/send-a-file-to-the-user-then-delete-file-from-server/69080438#69080438
       #A better way??

       with BytesIO(audio_response) as output:
          output.seek(0)
          headers = {"Content-disposition": "attachment; filename=%s" % Filename }
          return Response(output.read(), mimetype='audio/wav', headers=headers)
    else:
       print('Invalid filename -- requesting again')
       return render_template('tools.html', errMsg = 'Invalid filename - please use a valid filename')
@app.route('/phone', methods=['GET','POST'])
def phone():
   return render_template('chat.html') 

@app.route('/logout')
def logout():
    flask_login.logout_user()
    return 'Logged out'
   
@app.route('/instance')
def instance():
    instance = request.args.get('instance')
    print('Setting active instance %s ' % instance)
    
    local.db.SetUserProject(flask_login.current_user.id, instance)
    print('Setting active instance completed')
    flask_login.current_user.activeProject = instance

    return redirect('/projects')

@app.route('/deployment', methods=['GET','POST'])
def deployment():
    pass
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        client = None
        project = local.db.GetProject(flask_login.current_user.activeProjectId)

        match action:
            case "bu_check":
                try:
                    client = local.cxone.CxOne(project[10],project[11])   
                except:
                    return render_template('deployment.html', errMsg = "Invalid Key/Secret - add details to project")
                if (client is not None and client.get_token()):        
                    businessUnit = client.GetBusinessUnit()
                    result = f"You are connecting to Business Unit: {businessUnit['businessUnitName']}"
                    return render_template('deployment.html', errMsg = result)
            case "addressbook_upload":
                file = request.files['addressbook_file']
                address_name = request.form.get('addressbook_name')
                
                file.stream.seek(0)
                wrapper = io.TextIOWrapper(file.stream,  encoding="utf-8", )
                data_list = ReadDataList(wrapper)
                
                client = local.cxone.CxOne(project[10],project[11])  
                if (client is not None and client.get_token()):
                    client.CreateAddressBook(address_name,{ "addressBookEntries" : data_list})
                    return render_template('deployment.html', errMsg = 'Address book uploaded')   
                else:
                    return render_template('deployment.html', errMsg = 'Error Uploading Address book')   
            case _:
                return render_template('deployment.html', errMsg = 'Unknown action')        
            
        return render_template('deployment.html', errMsg = 'Still in debug')
   
    #Must be a standard GET request
    return render_template('deployment.html', errMsg = 'Still in debug')

@app.route('/download/<path:filename>', methods=['GET', 'POST'])
def download(filename):
    download_path = os.path.join(app.root_path, 'packages//default')
    return send_from_directory(download_path, filename, mimetype='text/plain',as_attachment = True)

def ReadDataList(fileStream):
    #headers = str(fileStream.readline())
    headers = str(fileStream.readline()).strip().split('\t')
    # Read the remaining lines
    data_list = []
    for line in fileStream.readlines():
        values = line.strip().split('\t')
        #Supported column names here:
        #https://developer.niceincontact.com/API/AdminAPI#/AddressBook/Create%20Address%20Book%20Entries
        data_dict = dict(zip(headers, values))
        data_list.append(data_dict)
        
    return data_list

if __name__ == '__main__':
   app.run()
