"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Blueprint for POC web comms
#   Date:           17/01/24
################################################################################"""
import flask_login
from flask import request,flash,Blueprint, g, render_template #jsonify,

import local.datamodel
from routes.common import safe_route

bp = Blueprint('poc', __name__)

@bp.route('/poc', methods=['GET','POST'])
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
            local.db.delete("poc",{ "id" : item_selected})
        if action =="synchronise":
            project_item = g.data_model.GetProject(flask_login.current_user.active_project)
            cx_connection = local.cxone.CxOne(project_item['user_key'],project_item['user_secret'])
            if cx_connection.is_connected():
                #We got a token so now let get the bu
                poc_list = cx_connection.GetPocList()
                for key,value in poc_list.items():
                    item_id = g.data_model.AddNewIfNoneEx("poc","name",{ "external_id" : value[0],
                                                                         "name" : key , "description" :  value[2] })
                    if item_id > 0 :
                        local.db.update("poc", { "external_id" : value[0] , "description" : value[2]}, { "id" : item_id})
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
            local.db.update("poc",values,{ "id" : item_id})

    #action =="item_cancel" - just drop through to the poc-list
    return render_template('poc-list.html')
