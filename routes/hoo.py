"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Blueprint for hours of operation
#   Date:           17/01/24
################################################################################"""
import os
import json
import flask_login
from flask import request,flash,Blueprint, g, render_template
from markupsafe import Markup

from local import logger

import local.cxone
from local.datamodel import DataModel
from routes.common import safe_route

bp = Blueprint('hoo', __name__)

@bp.route('/hoo', methods=['GET','POST'])
@safe_route
def hoo():
    """Route all hoo updates"""
    dm : DataModel = g.data_model
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        if action =="create":
            return render_template('hoo-item.html')
        if action =="edit":
            g.item_selected = request.form['id']
            return render_template('hoo-item.html')
        if action == "delete":
            item_selected = request.form['id']
            dm.db_delete("hoo",item_selected)
        if action =="synchronise":
            project_item = dm.db_get_item("project",flask_login.current_user.active_project)
            cx_connection = local.cxone.CxOne(project_item['user_key'],project_item['user_secret'])
            if cx_connection.is_connected():
                #We got a token so now let get the bu
                hoo_list = cx_connection.get_hoo_list()
                for item in hoo_list:
                    item_id = dm.db_insert_or_update("hoo","name",{ "external_id" : item['hoursOfOperationProfileId'],
                                                                         "name" : item['hoursOfOperationProfileName'], "description" : item['description'] })
                    if item_id > 0:
                        dm.db_update("hoo", { "external_id" : item['hoursOfOperationProfileId'] }, { "id" : item_id})
                        flash(f"Linked Existing HOO to BU Hoo - as name already exists - {item['hoursOfOperationProfileName']}","Information")
            else:
                flash("Unable to connect to CX one - check your credentials","Error")

        #Actions in Hoo-Item
        if action == "item_create":
            values = dm.request_paramlist(request)
            values = collapse_daily_pattern(values)
            if dm.db_insert_or_update("hoo","name",values) > 0:
                flash("Hours of operation name already exists - please use a unique name","Error")
                return render_template('hoo-item.html')

        if action =="item_update":
            item_id = request.form['id']
            values = dm.request_paramlist(request)
            values = collapse_daily_pattern(values)
            dm.db_update("hoo", item_id, values)

        if action == "item_linked_details":
            item_id = request.form['id']
            external_id = dm.db_get_item("hoo",item_id).get("external_id", None)
            if dm.validate_connection():
                if external_id is not None:
                    project = dm.db_get_item("project", flask_login.current_user.active_project)
                    __connection = local.cxone.CxOne(project['user_key'],project['user_secret'])
                    if __connection.is_connected():
                        result = __connection.get_hoo(external_id)
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
            external_id = dm.db_get_item("hoo",item_id).get("external_id", None)
            holiday_suffix = dm.db_get_item("hoo",item_id).get("holiday_pattern", None)
            days = dm.db_get_item("hoo",item_id).get("daily_pattern", "").split(",")
            if len(days) == 7:
                days = [
                    {
                        "day" : "Monday" if i == 0 else "Tuesday" if i == 1 else "Wednesday" if i == 2 
                            else "Thursday" if i == 3 else "Friday" if i == 4 else "Saturday" if i == 5 else "Sunday",
                        "openTime": day.split('-')[0] + ":00" if day != "Closed" else "00:00:00",
                        "closeTime": day.split('-')[1] + ":00" if day != "Closed" else "00:00:00",
                        "isClosedAllDay": False if day != "Closed" else True
                    }
                    for i, day in enumerate(days)
                ]
            else:
                days = []
            if dm.validate_connection():
                if external_id is not None:
                    project = dm.db_get_item("project", flask_login.current_user.active_project)
                    __connection = local.cxone.CxOne(project['user_key'],project['user_secret'])
                    if __connection.is_connected():
                        holiday_file = os.path.join('packages', 'default', 'templates', f'holidays_{holiday_suffix}.txt')
                        logger.info('Reading holiday file %s', holiday_file)
                        if os.path.isfile(holiday_file) is False:
                            flash("Error - holiday file does not exist","Error")
                            return render_template('hoo-item.html')
                        holidays = read_data_file(holiday_file)
                        original_hoo = __connection.get_hoo(external_id)
                        if original_hoo is not None:
                            __connection.update_hoo(external_id,original_hoo,"", "", days, holidays)
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

def collapse_daily_pattern(values: dict) -> dict:
    """Get the daily patterns from the form obiects and return updated list"""
    #Collapse Hoo items in values
    daily_pattern = ["Closed" for i in range(7)]
    days = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    for day in days:
        if request.form.get(f'{day}_closed') != 'on':
            daily_pattern[days.index(day)] = values[f'{day}_start'] + '-' + values[f'{day}_end']
            values.pop(day + '_start',None)
            values.pop(day + '_end',None)
            values['daily_pattern'] = ",".join(daily_pattern)
        values.pop(day + '_closed',None)
    #Remove the daily pattern from the values dict
    return values
