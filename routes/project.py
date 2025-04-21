"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Blueprint for HOO web comms
#   Date:           17/01/24
################################################################################"""
import traceback
import flask_login
from flask import request,flash,Blueprint, g, render_template #jsonify,

import local.io
import local.datamodel
from routes.common import safe_route
from . import logger

bp = Blueprint('project', __name__)

@bp.route('/project', methods=['GET','POST'])
@safe_route
def project():
    """Display project page"""
    dm : local.datamodel.DataModel = g.data_model

    if request.method =="POST":
        action = request.form['action'] # get the value of the clicked button
        if action =="create":
            return render_template('project-item.html')
        if action =="edit":
            g.item_selected = request.form['id']
            return render_template('project-item.html')
        if action =="delete":
            g.item_selected = request.form['id']
            project_count = len(dm.db_get_list("project"))
            logger.info("Number of projects %s", project_count)
            if project_count < 2:
                logger.info("Delete item request - not  enough projects")
                flash("Cannot delete past project - create a new project first","Information")
                return render_template('project-list.html')
            else:
                dm.db_delete("project",g.item_selected)
                if dm.project_id == g.item_selected:
                    dm.project_id = g.dm.db_get_list("project")[0]['id']
                flask_login.current_user.active_project = dm.project_id
                return render_template('project-list.html')

        #item actions
        if action =="item_create":
            try:
                #Create new project details
                values = dm.request_paramlist(request)
                logger.info("Creating project for %s", values.get('short_name'))
                logger.info("Created by user ID %s", dm.user_id)
                values["user_id"] = dm.user_id

                project_id = dm.db_insert_or_update("project","short_name",values)
                if project_id > 0:
                    flash("Project name already extists, please use a different name","Error")
                    return render_template('project-item.html')

                dm.project_id = -project_id
                flask_login.current_user.active_project = dm.project_id
                dm.db_update("user",dm.user_id,{ "active_project" : dm.project_id  })
                if  dm.project_id is not None:
                    #Add default wav files to project ID
                    print('Generating standard WAV records for project')
                    sys_audio = local.io.get_system_audio_file_list('default')
                    for key,value in sys_audio.items():
                        print(key)
                        dm.db_insert("audio",{"project_id" : dm.project_id , "name" : key , "description" : value , "isSystem" : True})
                    #Add single action items to project
                    dm.db_insert("skill",{"project_id" : dm.project_id , "name" : "System default - No Agents" ,
                                    "description" : "Removes agent from active queue (e.g when a call routes to voicemail)" , 
                                    "is_synced" : False})
            except Exception as e:
                flash("Something went wrong creating project","Error")
                logger.error("Exception: %s", repr(e))
                traceback.print_exc()
            return render_template('project-list.html')

        if action =="item_update":
            project_id = request.form['id']
            values = dm.request_paramlist(request)
            dm.db_update("project",project_id,values)
            return render_template('project-list.html')

    return render_template('project-list.html')
