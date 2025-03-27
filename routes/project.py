"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Blueprint for HOO web comms
#   Date:           17/01/24
################################################################################"""
import traceback
import flask_login
from flask import request,flash,Blueprint, g, render_template #jsonify,

import local.datamodel
from routes.common import safe_route

bp = Blueprint('project', __name__)

@bp.route('/project', methods=['GET','POST'])
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
                values["user_id"] = g.data_model.user_id
                project_id = local.db.Insert("project",values)
                g.data_model.project_id =  project_id
                flask_login.current_user.active_project = project_id
                local.db.Update("user",{ "active_project" : project_id },{"id" : g.data_model.user_id})
                if  project_id is not None:
                    #Add default wav files to project ID
                    print('Generating standard WAV records for project')
                    sys_audio = local.io.GetSystemAudioFileList('default')
                    for key,value in sys_audio.items():
                        print(key)
                        local.db.Insert("audio",{"project_id" : project_id , "name" : key , "description" : value , "isSystem" : True})
                local.db.Insert("skill",{"project_id" : project_id , "name" : "System default - No Agents" ,
                                    "description" : "Removes agent from active queue (e.g when a call routes to voicemail)" , 
                                    "is_synced" : False})
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
