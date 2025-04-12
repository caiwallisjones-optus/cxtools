"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    This is our callflow pages
#   Date:           17/01/24
################################################################################"""
from flask import request,flash,Blueprint, g, render_template,redirect #jsonify,
import flask_login

from local import logger
import local.datamodel
from routes.common import safe_route


bp = Blueprint('callflow', __name__)

@bp.route('/callflow', methods=['GET','POST'])
@safe_route
def callflow():
    """Display callflow page"""
    dm : local.datamodel.DataModel = g.data_model

    if request.method == 'GET':
        return render_template('callflow-list.html')

    #POST:
    action = request.form['action'] # get the value of the clicked button
    g.item_selected = request.form.get('id',None)
    if action =="create":
        g.item_selected = None
        return render_template('callflow-item.html')

    if action =="edit":
        item = dm.db_get_item("callflow",g.item_selected)
        if item['callFlowAction_id'] is not None:
            action_item = dm.db_get_item("callFlowAction", item['callFlowAction_id'])
            action_responses = dm.db_get_list_filtered("callFlowResponse", {"callFlowAction_id" : action_item['id']})
            return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

        return render_template('callflow-item.html', action_responses = None)

    if action == "delete":
        item_id = request.form['id'] # get the value of the clicked button
        dm.db_delete("callFlow",item_id)
        return render_template('callflow-list.html')

    ######
    ##          CallFlow-Item Actions
    ######
    if action == "item_create":
        #Create new queue details
        callflow_name = request.form['name']
        callflow_description =  request.form['description']

        callflow_id = dm.db_insert_or_update("callFlow","name",{ 'project_id' : flask_login.current_user.active_project,
                                                           'name' : callflow_name , 'description' : callflow_description})
        if callflow_id < 0:
            g.item_selected = -callflow_id
            return render_template('callflow-item.html', action_item = None, action_responses = None)

        flash("Name exists - please use a unique callflow name","Error")
        g.item_selected = None
        return render_template('callflow-item.html')

    if action =="item_update":
        #Update Name and description as needed
        call_flow_id = request.form['id']
        call_flow_name = request.form['name']
        call_flow_description =  request.form['description']
        dm.db_insert_or_update("callFlow","id",{ "id" : call_flow_id, 'project_id' : flask_login.current_user.active_project, 'name' : call_flow_name ,
                                'description' : call_flow_description})

        #local.db.UpdateCallFlow({'name': call_flow_name,'description': call_flow_description },{'id' : call_flow_id })
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
            for action_element in dm.get_script_action_params(call_flow_action_type):
                #Add element names to appropriate list IF they do not exist
                if (len(call_flow_action_params[i]) > 0) and action_element.endswith("_LOOKUP"):
                    item_type  = action_element.split('|')[1][:-7]
                    item_exists = dm.db_insert_or_update(item_type,"name",{ "name" : call_flow_action_params[i],
                                                                "description" : "<Added when creating call flow - update details before publishing>"})
                    #Now update the lookup so that we have the ID not the name in our lists
                    call_flow_action_params[i] = str(abs(item_exists))
                i += 1
            #build param list
            action_params = dm.build_param_list(call_flow_action_type, (call_flow_action_params) )
            dm.db_update("callflowaction",call_flow_action_id, {'name' : call_flow_action_name,'action': call_flow_action_type, 'params' : action_params})


        action_item = dm.db_get_item("callFlowAction",call_flow_action_id)
        if action_item is not None:
            action_responses = dm.db_get_list_filtered("callFlowResponse", {"callFlowAction_id" : action_item['id']})
        else:
            action_responses = None
        return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

    if action =="item_cancel":
        g.item_selected = None
        return redirect('/callflow')

    if action =="item_poc_add":
        callflow_id = request.form['id']
        callflow_name = request.form['name']
        callflow_description =  request.form['description']
        new_poc_id =  request.form['new_poc']

        item = dm.db_get_item("callFlow",callflow_id)
        ##Get poc by ID
        if item['poc_list'] is None:
            poc_list = new_poc_id
        else:
            #Remove items in poclist that no longer exist
            conf_list = item['poc_list'].split(",")
            for poc in conf_list:
                if poc == '' or dm.db_get_item("poc", poc) is None:
                    #Remove item from list
                    conf_list.remove(poc)

            conf_list.append(new_poc_id)
            #And add back new POC
            poc_list = ",".join(set([element for element in conf_list if element]))
        ##Update callflow.
        dm.db_update("callflow",  item['id'],{ 'poc_list' :poc_list } )


        call_flow_action_id = request.form.get('action_id',None)
        action_item =  dm.db_get_item("callFlowAction", call_flow_action_id)
        if action_item is not None:
            action_responses = dm.db_get_list_filtered("callFlowResponse", {"callFlowAction_id" : action_item['id']})
        else:
            action_responses = None

        return render_template('callflow-item.html',  action_item = action_item, action_responses = action_responses)

    if action.startswith("item_poc_remove_"):
        item_id = action.removeprefix("item_poc_remove_")

        callflow_id = request.form['id']
        item = dm.db_get_item("callflow",callflow_id)
        item_poc = item['poc_list']
        if item_poc:
            item_poc = item_poc.split(",")
            item_poc.remove(item_id)
            new_poc_id = ','.join(item_poc)
        else:
            logger.debug("Error - trying to remove a POC that does not exist")

        dm.db_update("callflow", callflow_id , { 'poc_list' : new_poc_id })

        call_flow_action_id = request.form.get('action_id',None)
        action_item =  dm.db_get_item("callFlowAction", call_flow_action_id)
        if action_item is not None:
            action_responses = dm.db_get_list_filtered("callFlowResponse", {"callFlowAction_id" : action_item['id']})
        else:
            action_responses = None

        return render_template('callflow-item.html',  action_item = action_item, action_responses = action_responses)

    if action =="action_new":
        item_id = request.form['id']
        item = dm.db_get_item("callflow",item_id)
        #Now build the param list for the actions
        action_id = request.form['action_id']
        action_type = request.form['action_type']
        action_parent = 0
        if not(action_id is None or action_id == ''):
            # We need to update the action with the action_type - and for this we only set the action_type
            dm.db_update("callflowaction", action_id, {'action': action_type})
            #Add default action as needed
            action_item =  dm.db_get_item("callFlowAction", action_id)
            if dm.get_script_action_has_default(action_type):
                dm.db_insert("callFlowResponse",{"callFlow_id" : g.item_selected , "callFlowAction_id" : action_item['id'],
                                                       "response" : "Default", "callFlowNextAction_id" : None } )
            action_responses =  dm.db_get_item("callflowresponse", action_item['id'])

            return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

        else:
            #Create the first action (action_id is None or action_id == '')
            logger.info("Creating first action for new callflow")
            action_added = dm.db_insert("callFlowAction", {"callFlow_id" : item_id , "parent_id" :action_parent,
                                                            "name" : "BEGIN", "action" : action_type})
            logger.info("Updating callflow % s ", item_id)
            dm.db_update("callflow", item_id, {'name': item['name'],'description': item['description'] , 'callFlowAction_id' : action_added })

            action_item = dm.db_get_item("callFlowAction",action_added)
            if dm.get_script_action_has_default(action_type):
                logger.info("Requires a default path adding now")
                dm.db_insert("callFlowResponse", { "callFlow_id" : g.item_selected,
                                "callFlowAction_id" : action_item['id'] ,"response" : "Default","callFlowNextAction_id" : None})
                action_responses =  dm.db_get_item("callflowresponse", action_added)

        return render_template('callflow-item.html',action_item = action_item, action_responses = action_responses)

    if action == "action_response_new":
        callflow_id = request.form['id']
        action_id = request.form['action_id']
        action_response = request.form['action_response_new']

        #Add response for action_id
        dm.db_insert("callFlowResponse",{"callFlow_id" : callflow_id , "callFlowAction_id" : action_id,
                                                       "response" :action_response , "callFlowNextAction_id" : None } )
        action_item = dm.db_get_item("callFlowAction",action_id)
        action_responses = dm.db_get_list_filtered("callFlowResponse", {"callFlowAction_id" : action_item['id']})

        return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

    if action.startswith("action_response_create_"):
        #Create a new response and update the existing response
        callflow_id = request.form['id']
        action_id = request.form['action_id']
        parent_response_id = action.removeprefix("action_response_create_")
        parent_response = dm.db_get_item("callFlowResponse",parent_response_id)

        action_name = request.form.get('action_name',"ERROR") +"_" + parent_response['response']
        new_action = dm.db_insert( "callFlowAction",{"callFlow_id" : callflow_id,
                                        "parent_id" : action_id, "name" : action_name, "action" : "" })
        dm.db_update("callFlowResponse", parent_response_id, {"callFlowNextAction_id" : new_action})

        action_item = dm.db_get_item("callFlowAction",new_action)
        return render_template('callflow-item.html', action_item = action_item, action_responses = None)

    if action.startswith("action_response_select_"):
        callflow_id = g.item_selected
        action_response_id = action.removeprefix("action_response_select_")

        action_item = dm.db_get_item("callFlowAction",action_response_id)
        action_responses = dm.db_get_list_filtered("callFlowResponse", {"callFlowAction_id" : action_response_id})

        return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

    if action.startswith("action__clear_"):
        callflow_id = g.item_selected

        action_id = action.removeprefix("action__clear_")
        action = dm.db_get_item("callFlowAction",action_id )

        dm.db_delete("callFlowAction",action_id)

        #Clear all pointers to the item as we have deleted it
        items = dm.db_get_list_filtered("callFlowResponse", { 'callFlow_id': action['callFlow_id'], 'callFlowNextAction_id' : action_id,
                                             'callFlowAction_id' : action['parent_id']})
        for line in items:
            dm.db_update("callFlowResponse", line['id'],  { 'callFlowNextAction_id' : None })

        #Display our parent action now
        if action['parent_id'] > 0:
            action_item = dm.db_get_item("callFlowAction",action['parent_id'])
            action_responses = dm.db_get_list_filtered("callFlowResponse", {"callFlowAction_id" : action['parent_id']})
        else:
            #Root action
            action_item = None
            action_responses = None
        return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

    return f"Not Built yet TODO - /callflow POST {action}"
