"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Blueprint for SKILL
#   Date:           17/01/24
################################################################################"""
import json
import flask_login
from flask import request,flash,Blueprint, g, render_template #jsonify,
from markupsafe import Markup
import local.datamodel
from routes.common import safe_route


bp = Blueprint('skill', __name__)

@bp.route('/skill', methods=['GET','POST'])
@safe_route
def skill():
    """Route all hoo updates"""
    dm : local.datamodel.DataModel = g.data_model
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button

        if action =="create":
            return render_template('skill-item.html')
        if action.startswith('edit_'):
            g.item_selected = action.removeprefix("edit_")
            return render_template('skill-item.html')
        if action.startswith('delete_'):
            g.item_selected = action.removeprefix("delete_")
            dm.db_delete("skill",g.item_selected)

        if action =="synchronise":
            project_item = dm.db_get_item("project", flask_login.current_user.active_project)
            cx_connection = local.cxone.CxOne(project_item['user_key'],project_item['user_secret'])
            if cx_connection.is_connected():
                #We got a token so now let get the bu
                skill_list = cx_connection.get_skill_list()
                for item in skill_list:
                    skill_type = "Unknown"
                    if item['media_typeId']== 4:
                        skill_type = "Voice"
                    if item['media_typeId']== 4 and item['isOutbound'] is True:
                        skill_type = "Outbound"
                    if item['media_typeId']== 9:
                        skill_type = "Digital"
                    if item['media_typeId']== 5:
                        skill_type = "Voicemail"
                    item_id = dm.db_insert_or_update("skill","name",
                                                          { "external_id" : item['skillId'],
                                                            "name" : item['skill_name'], 
                                                            "skill_type" : skill_type,
                                                            "description" : item['campaign_name'] })
                    if item_id > 0:
                        dm.db_update("skill",item_id, { "external_id" : item['skillId'] })
                        flash(f"Linked Existing Skill to BU Skill - as name already exists - {item['skill_name']}",
                                "Information")
            else:
                flash("Unable to connect to CX one - check your credentials","Error")
        #Actions in Skill-Item
        if action == "item_create":
            name = request.form['name']
            description = request.form['description']
            if not dm.db_insert_or_update("skill","name",{ "name" : name, "description" : description, "skill_type" : request.form['skill_type']}):
                flash("Skill name already exists - please use a unique name","Error")
                return render_template('skill-item.html')

        if action =="item_update":
            item_id = request.form['id']
            values = dm.request_paramlist(request)
            values.pop("external_id")
            dm.db_update("skill",item_id,values)

        if action == "item_linked_details":
            item_id = request.form['id']
            external_id = dm.db_get_item("skill",item_id).get("external_id", None)
            if dm.validate_connection():
                if external_id is not None:
                    project = dm.db_get_item("project", flask_login.current_user.active_project)
                    __connection = local.cxone.CxOne(project['user_key'],project['user_secret'])
                    if __connection.is_connected():
                        result = __connection.get_skill(external_id)
                        if result is not None:
                            flash(Markup(f"<pre>{json.dumps(result, indent=4,).replace(' ','&nbsp;')}</pre>"),"Information")
                        else:
                            flash("Error identifying Skill ID - please check your credentials","Error")
                    else:
                        flash("Error connecting to CXone - please check your credentials","Error")
                    g.item_selected = request.form['id']
                    return render_template('hoo-item.html')
            else:
                flash("Please validate your connection in the deployment tab before attempting this","Error")
                g.item_selected = request.form['id']
                return render_template('skill-item.html')



    return render_template('skill-list.html')
