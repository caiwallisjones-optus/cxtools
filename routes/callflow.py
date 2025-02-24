"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    This is our callflow pages
#   Date:           17/01/24
################################################################################"""
from flask import request,flash,Blueprint, g, render_template,redirect #jsonify,
import flask_login

import local.datamodel
from routes.common import safe_route

bp = Blueprint('callflow', __name__)

@bp.route('/callflow', methods=['GET','POST'])
@safe_route
def callflow():
    """Display callflow page"""
    if request.method == 'GET':
        return render_template('callflow-list.html')

    #POST:
    action = request.form['action'] # get the value of the clicked button
    g.item_selected = request.form.get('id',None)
    if action =="create":
        g.item_selected = None
        return render_template('callflow-item.html')

    if action =="edit":
        item = local.db.GetCallFlow(g.item_selected)
        if item[5] is not None:
            action_item = local.db.GetCallFlowAction(item[5])
            action_responses = local.db.GetCallFlowActionResponses(action_item[0])
            return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

        return render_template('callflow-item.html', action_responses = None)

    if action == "delete":
        item_id = request.form['id'] # get the value of the clicked button
        local.db.DeleteCallFlow(item_id)
        return render_template('callflow-list.html')

    if action =="callflow_item_poc_new":
        callflow_id = request.form['id']
        callflow_name = request.form['name']
        callflow_description =  request.form['description']
        new_poc_id =  request.form['new_poc']

        item = local.db.GetCallFlow(callflow_id)
        ##Get poc by ID
        if item[4] is None:
            poc_list = new_poc_id
        else:
            poc_list = (item[4] + "," + new_poc_id).lstrip(',')
        ##Update callflow.
        local.db.UpdateCallFlow({ 'poc_list' :poc_list }, {'id': item[0]})
        return render_template('callflow-item.html', action_responses = None)

    ######
    ##          CallFlow-Item Actions
    ######
    if action == "item_create":
        #Create new queue details
        callflow_name = request.form['name']
        callflow_description =  request.form['description']

        callflow_id = local.db.AddCallFlow(flask_login.current_user.activeProjectId,callflow_name,callflow_description)
        if callflow_id.isnumeric():
            g.item_selected = callflow_id
            return render_template('callflow-item.html', action_item = None, action_responses = None)
        else:
            flash("Error creating new call flow","Error")
            return render_template('callflow-list.html')

    if action =="item_update":
        #Update Name and description as needed
        call_flow_id = request.form['id']
        call_flow_name = request.form['name']
        call_flow_description =  request.form['description']
        local.db.UpdateCallFlow({'name': call_flow_name,'description': call_flow_description },{'id' : call_flow_id })
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
            for action_element in g.data_model.GetActionParams(call_flow_action_type):
                #Add element names to appropriate list IF they do not exist
                if (len(call_flow_action_params[i]) > 0) and action_element.endswith("_LOOKUP"):
                    item_type  = action_element.split('|')[1][:-7]
                    item_exists = g.data_model.AddNewIfNoneEx(item_type,"name",{ "name" : call_flow_action_params[i],
                                                                "description" : "<Added when creating call flow - update details before publishing>"})
                    #Now update the lookup so that we have the ID not the name in our lists
                    call_flow_action_params[i] = str(abs(item_exists))
                i += 1
            #build param list
            action_params = g.data_model.BuildParamList(call_flow_action_type, (call_flow_action_params) )
            params = {'name' : call_flow_action_name,'action': call_flow_action_type, 'params' : action_params}
            query_filter = {'id' : call_flow_action_id}
            local.db.UpdateCallFlowAction(params,query_filter)

        action_item = local.db.GetCallFlowAction(call_flow_action_id)
        if action_item is not None:
            action_responses = local.db.GetCallFlowActionResponses(action_item[0])
        else:
            action_responses = None
        return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

    if action =="item_cancel":
        g.item_selected = None
        return redirect('/callflow')

    if action =="action_new":
        item_id = request.form['id']
        item = local.db.GetCallFlow(item_id)
        #Now build the param list for the actions
        action_id = request.form['action_id']
        action_type = request.form['action_type']
        action_parent = 0
        if action_id == '':
            action_name = "BEGIN"
        else:
            action_name = "Action"
        if not(action_id is None or action_id == ''):
            # We need to update the action with the action_type - and for this we only set the action_type
            params = {'action': action_type}
            query_filter = {'id' : action_id}
            local.db.UpdateCallFlowAction(params,query_filter)
            #Add default action as needed
            action_item = local.db.GetCallFlowAction(action_id)
            if g.data_model.GetActionHasDefaultResponse(action_type):
                local.db.AddActionResponse(g.item_selected,action_item[0],"Default",None)

            action_responses = local.db.GetCallFlowActionResponses(action_item[0])

            return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

        else:
            #Moving the config to when we have created the action
            action_added = local.db.AddCallFlowAction(g.item_selected,action_parent,action_name,action_type,"")
            #And set the child id as its our first:
            local.db.UpdateCallFlow({'name': item[2],'description': item[3] , 'callFlowAction_id' : action_added },{'id' : item_id })

            action_item = local.db.GetCallFlowAction(action_added)
            if g.data_model.GetActionHasDefaultResponse(action_type):
                local.db.AddActionResponse(g.item_selected,action_item[0],"Default",None)
                action_responses = local.db.GetCallFlowActionResponses(action_item[0])

        return render_template('callflow-item.html',action_item = action_item, action_responses = action_responses)

    if action == "action_response_new":
        callflow_id = request.form['id']
        action_id = request.form['action_id']
        action_response = request.form['action_response_new']

        #Add response for action_id
        local.db.AddActionResponse(callflow_id,action_id,action_response,None)
        action_item = local.db.GetCallFlowAction(action_id)
        action_responses = local.db.GetCallFlowActionResponses(action_item[0])
        return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

    if action.startswith("action_response_create_"):
        #Create a new response and update the existing response
        callflow_id = request.form['id']
        action_id = request.form['action_id']
        parent_response_id = action.removeprefix("action_response_create_")
        parent_response = local.db.GetCallFlowActionResponse(parent_response_id)
        action_name = request.form.get('action_name',"Action_") +"_" + parent_response[3]
        new_action = local.db.AddCallFlowAction(callflow_id,action_id,action_name ,"","")
        #Update our parent response to point to the new action
        local.db.UpdateCallFlowActionResponse(parent_response_id,new_action)

        action_item = local.db.GetCallFlowAction(new_action)
        action_responses = local.db.GetCallFlowActionResponses(new_action)
        return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

    if action.startswith("action_response_select_"):
        callflow_id = g.item_selected
        action_response_id = action.removeprefix("action_response_select_")
        #Get action response Id to get next action Id
        #item = local.db.GetCallFlow(g.item_selected)
        action_item = local.db.GetCallFlowAction(action_response_id)
        action_responses = local.db.GetCallFlowActionResponses(action_response_id)
        return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)

    if action.startswith("action__clear_"):
        callflow_id = g.item_selected

        action_id = action.removeprefix("action__clear_")
        action = local.db.SelectFirst("callFlowAction","*",{ 'id' :action_id} )

        local.db.Delete("callFlowAction",{ 'id' : action_id})

        #Clear all pointers to the item as we have deleted it
        local.db.Update("callFlowResponse", { 'callFlowNextAction_id' : None }, { 'callFlow_id': action['callFlow_id'],
                                                'callFlowNextAction_id' : action_id, 'callFlowAction_id' : action['parent_id']} )

        #Display our parent action now
        if action['parent_id'] > 0:
            action_item = local.db.GetCallFlowAction(action['parent_id'])
            action_responses = local.db.GetCallFlowActionResponses(action['parent_id'])
        else:
            #Root action so this is fairly clean
            action_item = None
            action_responses = None
        return render_template('callflow-item.html', action_item = action_item, action_responses = action_responses)
    return f"Not Built yet TODO - /callflow POST {action}"
