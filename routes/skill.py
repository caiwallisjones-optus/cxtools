"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Blueprint for SKILL
#   Date:           17/01/24
################################################################################"""
import flask_login
from flask import request,flash,Blueprint, g, render_template #jsonify,

import local.datamodel
from routes.common import safe_route

bp = Blueprint('skill', __name__)

@bp.route('/skill', methods=['GET','POST'])
@safe_route
def skill():
    """Route all hoo updates"""
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button

        if action =="create":
            return render_template('skill-item.html')
        if action.startswith('edit_'):
            g.item_selected = action.removeprefix("edit_")
            return render_template('skill-item.html')
        if action.startswith('delete_'):
            g.item_selected = action.removeprefix("delete_")
            local.db.Delete("skill",{ "id" : g.item_selected})
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
