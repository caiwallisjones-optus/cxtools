"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Blueprint for Queue
#   Date:           17/01/24
################################################################################"""

from flask import request,flash,Blueprint, g, render_template #jsonify,
from routes import logger
from routes.common import safe_route

import local.datamodel

bp = Blueprint('queue', __name__)

@bp.route('/queue', methods=['GET','POST'])
@safe_route
def queue():
    """Display queue list page"""
    logger.debug("Queue Page")
    dm : local.datamodel.DataModel = g.data_model

    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        g.item_selected = request.form.get('id',None)
        logger.debug("Action is %s", action)
        if action =="create":
            return render_template('queue-item.html')

        if action =="edit":
            g.item_selected = request.form.get('id',None)
            return render_template('queue-item.html')

        if action == "delete":
            item_id = request.form['id']
            dm.db_delete("queue",item_id)
            return render_template('queue-list.html')

        ##          Queue-Item Actions
        if action == "item_create":
            #Create new queue details
            queue_name = request.form['name']
            logger.info("Creating queue details for %s", queue_name)
            logger.info("Creating user ID is %s in %s",  g.data_model.user_id ,g.data_model.project_id)
            #db_insert_or_update(self, item_type : str, item_lookup_field,field_list : dict) -> int:
            new_queue_id = dm.db_insert_or_update("queue","name", {"name" : queue_name})
            if new_queue_id > 0 :
                flash("Cannot use an existing name - choose a unique name for the queue","Information")
            g.item_selected = abs(new_queue_id)
            return render_template('queue-item.html')

        if action =="item_update":
            g.item_selected = request.form['id']
            update_queue(dm, dm.request_paramlist(request))
            return render_template('queue-item.html')

        #Action updates from Queue-Item:
        if action =="queue_item_skill_new":
            logger.info("Adding skill to queue")
            g.item_selected = request.form.get('id',None)
            params = dm.request_paramlist(request)
            logger.info("Updating skill in queue")
            if params['skills'] is not None:
                skill_array = params['skills'].split(",")
                print(repr(skill_array))
                print(repr(params))
                if params['new_skill'] not in skill_array:
                    skill_array.append(params['new_skill'])
                    params['skills'] = (",").join(skill_array)
            else:
                params['skills'] = params['new_skill']

            logger.info("Updating queue details for %s" ,params['name'])
            update_queue(dm, params)
            #dm.db_update("queue", g.item_selected, {"skills" : params['skills']})
            return render_template('queue-item.html')

        if action.startswith("queue_item_skill_remove_"):
            g.item_selected = request.form.get('id',None)
            params = dm.request_paramlist(request)
            update_queue(dm, params)

            skill_to_remove = action.replace("queue_item_skill_remove_","")
            logger.info("Removing: %s", skill_to_remove)
            skill_array = params['skills'].split(",")
            skill_array.remove(skill_to_remove)
            queue_skills = (",").join(skill_array)
            dm.db_update("queue", g.item_selected, {"skills" : queue_skills})

            return render_template('queue-item.html',)

        if action  == "queue_action_new":
            g.item_selected = request.form['id']
            update_queue(dm, dm.request_paramlist(request))
            #Create new queue action - this is called from the queue-item html
            g.item_selected = None
            queue_id = request.form.get('id',None)
            return render_template('queueaction-item.html', queue_id = queue_id)

        if action =="queue_action_edit":
            g.item_selected = request.form['id']
            update_queue(dm, dm.request_paramlist(request))
            print(f'Updsate')
            #Edit the queue action
            action_id = request.form['action_id']
            queue_id = request.form['queue_id']
            print(f'We are editing our action - {action_id}')
            g.item_selected = action_id
            return render_template('queueaction-item.html', queue_id = queue_id, action="queueaction")

        if action =="queue_action_delete":
            #g.item_selected = request.form['id']
            #update_queue(dm, dm.request_paramlist(request))
            
            #Delete the queue action
            action_id = request.form['action_id']
            queue_id = request.form['queue_id']
            dm.db_delete("queueaction",action_id)
            g.item_selected = request.form.get('queue_id',None)
            return render_template('queue-item.html')

        if action =="queue_action_up":
            return "Not Built yet TODO - 00003 " + action

        if action =="queue_action_down":
            return "Not Built yet TODO - 00004 " +  action

        #Action updates from QueueAction-Item:
        if action =="queueaction_create":
            #Create new queue action(blank)
            queue_id = request.form['queue_id']
            queue_action = request.form['queueActionsDropdown']
            param_list = ["","","","",""]
            param_list[0] = request.form.get('param1','')
            param_list[1] = request.form.get('param2','')
            param_list[2] = request.form.get('param3','')
            param_list[3] = request.form.get('param4','')
            param_list[4] = request.form.get('param5','')
            logger.debug(repr(param_list))
            dm.db_insert("queueaction",{"queue_id" : queue_id, "action" : queue_action, "param1" :
                                       ','.join(map(str, param_list)), "param2" : "", "step_id" : 0})
            g.item_selected = queue_id
            return render_template('queue-item.html')

        if action =="queueaction_update":
            action_id = request.form['id']
            queue_action = request.form['queueActionsDropdown']
            ##TODO addthis as a function
            param_list = ["","","","","",""]
            param_list[1] = request.form.get('param1','')
            param_list[2] = request.form.get('param2','')
            param_list[3] = request.form.get('param3','')
            param_list[4] = request.form.get('param4','')
            param_list[5] = request.form.get('param5','')
            dm.db_update("queueaction", action_id, {"action" : queue_action, "param1" : ','.join(map(str, param_list))})#[:1]
            g.item_selected = request.form['queue_id']
            return render_template('queue-item.html')

        if action =="queueaction_cancel":
            g.item_selected = request.form['queue_id']
            return render_template('queue-item.html')

        #Queue Hoo Operations
        if action =="queue_item_prequeueaction_new":
            g.item_selected = request.form['id']
            update_queue(dm, dm.request_paramlist(request))
            logger.debug("Adding pre-queue state")
            state = request.form['prequeueState']
            g.item_selected = None
            return render_template('queueaction-item.html', queue_id = request.form['id'], action="prequeue", state = state)

        if action =="queue_item_inqueueaction_new":
            g.item_selected = request.form['id']
            update_queue(dm, dm.request_paramlist(request))
            logger.debug("Adding queue state")
            state = request.form['inqueueState']
            g.item_selected = None
            return render_template('queueaction-item.html', queue_id = request.form['id'], action="inqueue", state = state)

        if action.startswith("item_prequeue_remove_"):
            g.item_selected = request.form['id']
            update_queue(dm, dm.request_paramlist(request))

            action_to_remove = action.replace("item_prequeue_remove_","")
            dm.db_get_item("queue",g.item_selected)
            queue_actions = dm.db_get_item("queue",g.item_selected)['prequeehooactions']
            if queue_actions is not None:
                queue_actions = [action for action in queue_actions if not action.startswith(action_to_remove)]
                queue_actions = (",").join(queue_actions)
                dm.db_update("queue", g.item_selected, {"prequeehooactions" : queue_actions})

            return render_template('queue-item.html')

        if action.startswith("item_inqueue_remove_"):
            g.item_selected = request.form['id']
            update_queue(dm, dm.request_paramlist(request))

            action_to_remove = action.replace("item_inqueue_remove_","")
            dm.db_get_item("queue",g.item_selected)
            queue_actions = dm.db_get_item("queue",g.item_selected)['prequeehooactions']
            if queue_actions is not None:
                queue_actions = [action for action in queue_actions if not action.startswith(action_to_remove)]
                queue_actions = (",").join(queue_actions)
                dm.db_update("queue", g.item_selected, {"queehooactions" : queue_actions})

            return render_template('queue-item.html')

        #Called from queueaction-item.html
        if action == "queueaction_hoo_pre_cancel":
            g.item_selected =request.form['queue_id']
            return render_template('queue-item.html')

        if action == "queueaction_hoo_in_cancel":
            g.item_selected =request.form['queue_id']
            return render_template('queue-item.html')

        if action == "queueaction_hoo_pre_create":
            g.item_selected =request.form['queue_id']
            state = request.form['state']
            action_type = request.form['queueActionsDropdown']
            ##TODO addthis as a function
            param_list = ["","","","","",""]
            param_list[0] = request.form['state']
            param_list[1] = request.form.get('param1','')
            param_list[2] = request.form.get('param2','')
            param_list[3] = request.form.get('param3','')
            param_list[4] = request.form.get('param4','')
            param_list[5] = request.form.get('param5','')
            current_actions = dm.db_get_item("queue",g.item_selected)['prequeehooactions'] + "|" + ','.join(map(str, param_list)).rstrip(',')
            current_actions = current_actions.lstrip('|')
            dm.db_update("queue", g.item_selected, {"prequeehooactions" : current_actions})

            return render_template('queue-item.html')

        if action == "queueaction_hoo_in_create":
            g.item_selected =request.form['queue_id']
            state = request.form['state']
            action_type = request.form['queueActionsDropdown']
            param_list = ["","","","","",""]
            param_list[0] = request.form['state']
            param_list[1] = request.form.get('param1','')
            param_list[2] = request.form.get('param2','')
            param_list[3] = request.form.get('param3','')
            param_list[4] = request.form.get('param4','')
            param_list[5] = request.form.get('param5','')
            logger.debug(repr(param_list))
            current_actions = dm.db_get_item("queue",g.item_selected)['queehooactions'] + "|" + ','.join(map(str, param_list)).rstrip(',')
            current_actions = current_actions.lstrip('|')
            dm.db_update("queue", g.item_selected, {"queehooactions" : current_actions})

            return render_template('queue-item.html')

    print("Queue List")
    return render_template('queue-list.html')

def update_queue(dm : local.datamodel.DataModel, values) -> bool:
    """Just update all values on a submit"""
    #Convert all values in form to values we can submit in DB
    #We need to convert the HOO to a number or creat if it does not exist
    if values['hoo'] != "":
        item_exists = dm.db_insert_or_update("HOO","name",{ "name" : values['hoo'],
                                        "description" : "<Added when creating queue - update details before publishing>"})
        values['queuehoo'] = str(abs(item_exists))
    if values['skills'] == "None":
        values['skills'] = None
    values.pop('hoo',None)
    values.pop('prequeueState',None)
    values.pop('inqueueState',None)
    values.pop('new_skill',None)
    values.pop('action_id',None)
    values.pop('queue_id',None)
    #
    if dm.db_update("queue",g.item_selected, values) is False:
        flash("Error updating queue info - please recheck","Information")

    return True
