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
            item_id = request.form['id'] # get the value of the clicked button
            dm.delete("queue",item_id)
            return render_template('queue-list.html')

        ##          Queue-Item Actions
        if action == "item_create":
            #Create new queue details
            queue_name = request.form['name']
            logger.info("Creating queue details for %s", queue_name)
            logger.info("Creating user ID is %s in %s",  g.data_model.user_id ,g.data_model.project_id)
            #AddNewIfNoneEx(self, item_type : str, item_lookup_field,field_list : dict) -> int:
            new_queue_id = dm.AddNewIfNoneEx("queue","name", {"name" : queue_name})
            if new_queue_id > 0 :
                flash("Cannot use an existing name - choose a unique name for the queue","Information")
            g.item_selected = abs(new_queue_id)
            return render_template('queue-item.html')

        if action =="item_update":
            g.item_selected = request.form['id']
            queue_name = request.form['name']
            queue_skills =  request.form['skills']
            queue_hoo =  request.form['hoo']
            queue_email =  request.form['unattendedemail']
            #Updated the QueueHOO to the numeric number
            item_exists = dm.AddNewIfNoneEx("HOO","name",{ "name" : queue_hoo,
                                                        "description" : "<Added when creating queue - update details before publishing>"})
            #Now update the lookup so that we have the ID not the name in our lists
            queue_hoo = str(abs(item_exists))
            logger.info("Updating queue details for %s", queue_name)
            logger.info("QueueHoo %s" , queue_hoo)
            if not dm.update("queue", g.item_selected, {"name": queue_name, "skills" : queue_skills, "queuehoo" : queue_hoo, "unattendedemail" : queue_email}):
                flash("Error updating queue info - please recheck","Information")

            return render_template('queue-item.html')

        #Action updates from Queue-Item:
        if action =="queue_item_skill_new":
            #Append queueskill to list (table id!)
            g.item_selected = request.form.get('id',None)
            item = dm.db_get_item("queue",g.item_selected)
            queue_name = item['name']
            queue_skills =  item['skills']
            queue_hoo = item['queuehoo']
            queue_newskill = request.form['new_skill']
            if queue_skills is not None:
                skill_array = queue_skills.split(",")
                if queue_newskill not in skill_array:
                    skill_array.append(queue_newskill)
                    while '' in skill_array:
                        skill_array.remove('')
                    queue_skills = (",").join(skill_array)
            else:
                queue_skills = queue_newskill

            logger.info("Updating queue details for %s" ,queue_name)
            dm.update("queue", g.item_selected, {"name": queue_name, "skills" : queue_skills, "queuehoo" : queue_hoo})
            #local.db.update("queue",{"name": queue_name, "skills" : queue_skills, "queuehoo" : queue_hoo}, {"id" : g.item_selected})
            #actions = local.db.GetQueueActionsList(str(g.item_selected))
            return render_template('queue-item.html')

        if action =="queue_item_skill_remove":

            item_id = request.form['id']
            queue_name = request.form['name']
            queue_skills =  request.form['skills']
            queue_hoo = request.form['hoo']
            queue_skillremove = request.form['skill_remove']
            logger.info("Removing: %s", queue_skillremove)
            skill_array = queue_skills.split(",")
            queueskills =''
            if queue_skillremove in skill_array:
                skill_array.remove(queue_skillremove)
                queueskills = (",").join(skill_array)

            logger.info("queue_item_skill_remove for %s", queue_name)
            dm.update("queue", item_id, {"name": queue_name, "skills" : queueskills, "queuehoo" : queue_hoo})
            #local.db.UpdateQueue(item_id,queue_name,queueskills,queue_hoo)

            item = dm.db_get_item("queue",item_id)
            actions = dm.db_get_item("queueaction",item_id)
            return render_template('queue-item.html', item = item, actions= actions )

        if action  == "queue_action_new":
            #Create new queue action - this is called from the queue-item html
            g.item_selected = None
            queue_id = request.form.get('id',None)
            return render_template('queueaction-item.html', queue_id = queue_id)

        if action =="queue_action_edit":
            #Edit the queue action
            action_id = request.form['action_id']
            queue_id = request.form['queue_id']
            print(f'We are editing our action - {action_id}')
            g.item_selected = action_id
            return render_template('queueaction-item.html', queue_id = queue_id, action="queueaction")

        if action =="queue_action_delete":
            #Delete the queue action
            action_id = request.form['action_id']
            queue_id = request.form['queue_id']
            dm.delete("queueaction",action_id)
            #local.db.DeleteQueueAction(action_id)
            g.item_selected = request.form.get('id',None)
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
            param_list = ["","","","","",""]
            param_list[1] = request.form.get('param1','')
            param_list[2] = request.form.get('param2','')
            param_list[3] = request.form.get('param3','')
            param_list[4] = request.form.get('param4','')
            param_list[5] = request.form.get('param5','')
            #print(f'Param 1 {param_list[1]}')
            #print(f'Param 2 {param_list[2]}')
            dm.AddNewIfNoneEx("queueaction","queue_id",{"queue_id" : queue_id, "action" : queue_action, "param1" : 
                                                        ','.join(map(str, param_list)), "step_id" : 0})
            #local.db.AddQueueAction(queue_id,queue_action,(','.join(map(str, param_list)))[1:])
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
            #print(f'Param 1 {param_list[1]}')
            #print(f'Param 2 {param_list[2]}')
            #local.db.UpdateQueueAction(action_id,queue_action,(','.join(map(str, param_list)))[1:],"")
            dm.update("queueaction", action_id, {"action" : queue_action, "param1" : ','.join(map(str, param_list))})#[:1]
            g.item_selected = request.form['queue_id']
            return render_template('queue-item.html')

        if action =="queueaction_cancel":
            g.item_selected = request.form['queue_id']
            return render_template('queue-item.html')

        #Queue Hoo Operations
        if action =="queue_item_prequeueaction_new":
            g.item_selected = request.form['id']
            state = request.form['prequeueState']
            return render_template('queueaction-item.html', queue_id = g.item_selected, action="prequeue", state = state)

        if action =="queue_item_inqueueaction_new":
            g.item_selected = request.form['id']
            state = request.form['inqueueState']
            return render_template('queueaction-item.html', queue_id = g.item_selected, action="inqueue", state = state)

        if action.startswith("item_prequeue_remove_"):
            g.item_selected = request.form['id']
        if action.startswith("item_prequeue_remove_"):
            action_to_remove = action.replace("item_prequeue_remove_","")
            dm.db_get_item("queue",g.item_selected)
            queue_actions = dm.db_get_item("queue",g.item_selected)['prequeehooactions']
            if queue_actions is not None:
                queue_actions = [action for action in queue_actions if not action.startswith(action_to_remove)]
                queue_actions = (",").join(queue_actions)
                dm.update("queue", g.item_selected, {"prequeehooactions" : queue_actions})
            
            return render_template('queue-item.html')

        if action.startswith("item_inqueue_remove_"):
            g.item_selected = request.form['id']
            action_to_remove = action.replace("item_inqueue_remove_","")
            dm.db_get_item("queue",g.item_selected)
            queue_actions = dm.db_get_item("queue",g.item_selected)['prequeehooactions']
            if queue_actions is not None:
                queue_actions = [action for action in queue_actions if not action.startswith(action_to_remove)]
                queue_actions = (",").join(queue_actions)
                dm.update("queue", g.item_selected, {"queehooactions" : queue_actions})

            return render_template('queue-item.html')

        #Add HOO Actions
        if action == "queueaction_hoo_pre_cancel":
            g.item_selected =request.form['id']
            return render_template('queue-item.html')

        if action == "queueaction_hoo_in_cancel":
            g.item_selected =request.form['id']
            return render_template('queue-item.html')

        if action == "queueaction_hoo_pre_create":
            g.item_selected =request.form['id']
            state = request.form['state']
            action_type = request.form['queueActionsDropdown']
            ##TODO addthis as a function
            param_list = ["","","","","",""]
            param_list[1] = request.form.get('param1','')
            param_list[2] = request.form.get('param2','')
            param_list[3] = request.form.get('param3','')
            param_list[4] = request.form.get('param4','')
            param_list[5] = request.form.get('param5','')
            #print(f'Param 1 {param_list[1]}')
            #print(f'Param 2 {param_list[2]}')

            local.db.UpdateQueueHooActions(g.item_selected,'PREQUEUE',state,action_type,(','.join(map(str, param_list)))[1:])
            return render_template('queue-item.html')

        if action == "queueaction_hoo_in_create":
            g.item_selected =request.form['id']
            state = request.form['state']
            action_type = request.form['queueActionsDropdown']
            ##TODO addthis as a function
            param_list = ["","","","","",""]
            param_list[1] = request.form.get('param1','')
            param_list[2] = request.form.get('param2','')
            param_list[3] = request.form.get('param3','')
            param_list[4] = request.form.get('param4','')
            param_list[5] = request.form.get('param5','')
            print(f'Param 1 {param_list[1]}')
            print(f'Param 2 {param_list[2]}')

            local.db.UpdateQueueHooActions(g.item_selected,'QUEUE',state,action_type,(','.join(map(str, param_list)))[1:])
            return render_template('queue-item.html')

    print("Queue List")
    return render_template('queue-list.html')
