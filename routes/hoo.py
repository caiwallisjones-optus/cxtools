"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Blueprint for hours of operation
#   Date:           17/01/24
################################################################################"""
import os
import json
import flask_login

from local import logger
from flask import request,flash,Blueprint, g, render_template
from markupsafe import Markup

import local.cxone
import local.datamodel
from routes.common import safe_route

bp = Blueprint('hoo', __name__)

@bp.route('/hoo', methods=['GET','POST'])
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
            local.db.delete("hoo",{ "id" : item_selected})
        if action =="synchronise":
            project_item = g.data_model.GetProject(flask_login.current_user.active_project)
            cx_connection = local.cxone.CxOne(project_item['user_key'],project_item['user_secret'])
            if cx_connection.is_connected():
                #We got a token so now let get the bu
                hoo_list = cx_connection.GetHooList()
                for item in hoo_list:
                    item_id = g.data_model.AddNewIfNoneEx("hoo","name",{ "external_id" : item['hoursOfOperationProfileId'],
                                                                         "name" : item['hoursOfOperationProfileName'], "description" : item['description'] })
                    if item_id < 0:
                        local.db.update("hoo", { "external_id" : item['hoursOfOperationProfileId'] }, { "id" : -item_id})
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
            local.db.update("hoo",values,{ "id" : item_id})

        if action == "item_linked_details":
            item_id = request.form['id']
            external_id = g.data_model.GetItem("hoo",item_id).get("external_id", None)
            if g.data_model.ValidateConnection():
                if external_id is not None:
                    __connection = local.cxone.CxOne(g.data_model._DataModel__key,g.data_model._DataModel__secret)
                    if __connection.is_connected():
                        result = __connection.GetHoo(external_id)
                        if result is not None:
                            flash(Markup(f"<pre>{json.dumps(result, indent=4,).replace(' ','&nbsp;')}</pre>"),"Information")
                        else:
                            flash("Error identifying HOO ID - please check your credentials","Error")
                    else:
                        flash("Error connecting to CXone - please check your credentials","Error")
                    g.item_selected = request.form['id']
                    return render_template('hoo-item.html')
                else:
                    flash("Please syncronise your HOO attempting this - no CXone ID detected","Error")
            else:
                flash("Please validate your connection in the deployment tab before attempting this","Error")
                g.item_selected = request.form['id']
                return render_template('hoo-item.html')

        if action == "item_apply_holiday":
            item_id = request.form['id']
            external_id = g.data_model.GetItem("hoo",item_id).get("external_id", None)
            holiday_suffix = g.data_model.GetItem("hoo",item_id).get("holiday_pattern", None)
            if g.data_model.ValidateConnection():
                if external_id is not None:
                    __connection = local.cxone.CxOne(g.data_model._DataModel__key,g.data_model._DataModel__secret)
                    if __connection.is_connected():
                        
                        holiday_file =  f'.//packages//default//templates//holidays_{holiday_suffix}.txt'
                        logger.info('Reading holiday file %s', holiday_file)
                        if os.path.isfile(holiday_file) is False:
                            flash("Error - holiday file does not exist","Error")
                            return render_template('hoo-item.html')
                        holidays = read_data_file(holiday_file)
                        original_hoo = __connection.GetHoo(external_id)
                        if original_hoo is not None:
                            __connection.Update_Hoo(external_id,original_hoo,"", "", [], holidays)
                            flash("Updated holidays","Information")
                        else:
                            flash("Error identifying HOO ID - please check your credentials and that the HOO has been pushed to the BU","Error")
                    else:
                        flash("Error connecting to CXone - please check your credentials","Error")
                    g.item_selected = request.form['id']
                    return render_template('hoo-item.html')
                else:
                    flash("Please syncronise your HOO attempting this - no CXone ID detected","Error")
            else:
                flash("Please validate your connection in the deployment tab before attempting this","Error")
                g.item_selected = request.form['id']
                return render_template('hoo-item.html')

    return render_template('hoo-list.html')


def read_data_file(file_name : str) -> dict:
    with open(file_name, encoding='utf-8') as f:
        headers = f.readline().strip().split('\t')
         # Read the remaining lines
        data_list = []
        for line in f:
            values = line.strip().split('\t')
            #Supported column names here:
            #https://developer.niceincontact.com/API/AdminAPI#/AddressBook/Create%20Address%20Book%20Entries
            data_dict = dict(zip(headers, values))
            data_list.append(data_dict)
    return data_list
