"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Blueprint for POC web comms
#   Date:           17/01/24
################################################################################"""
import flask_login
from flask import request,flash,Blueprint, g, render_template #jsonify,

#from local import logger

import local.cxone
from local.datamodel import DataModel
from routes.common import safe_route

bp = Blueprint('poc', __name__)

@bp.route('/poc', methods=['GET','POST'])
@safe_route
def poc():
    """Route all entry point updates"""
    dm : DataModel = g.data_model
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        if action =="create":
            return render_template('poc-item.html')
        if action =="edit":
            g.item_selected = request.form['id']
            return render_template('poc-item.html')
        if action == "delete":
            item_selected = request.form['id']
            dm.db_delete("poc",item_selected)
        if action =="synchronise":
            project_item = dm.db_get_item("project", flask_login.current_user.active_project)
            cx_connection = local.cxone.CxOne(project_item['user_key'],project_item['user_secret'])
            if cx_connection.is_connected():
                #We got a token so now let get the bu
                poc_list = cx_connection.get_poc_list()
                for key,value in poc_list.items():
                    item_id = dm.db_insert_or_update("poc","name",{ "external_id" : value[0],
                                                                         "name" : key , "description" :  value[2] })
                    if item_id > 0 :
                        dm.db_update("poc", item_id,{ "external_id" : value[0] , "description" : value[2]})

                        flash(f"Linked Existing POC to BU POC - as name already exists - {key}","Information")
            else:
                flash("Unable to connect to CX one - check your credentials","Error")
        #Poc-Item
        if action == "item_create":
            name = request.form['name']
            description = request.form['description']
            if dm.db_insert_or_update("poc",name,{ "name" : name, "description" : description}) > 0:
                flash("Entry point name already exists - please use a unique number/name","Error")
                return render_template('poc-item.html')
        if action =="item_update":
            item_id = request.form['id']
            values = dm.request_paramlist(request)
            dm.db_update("poc",item_id, values)

    #action =="item_cancel" - just drop through to the poc-list
    return render_template('poc-list.html')
