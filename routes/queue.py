"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Blueprint for Queue
#   Date:           17/01/24
################################################################################"""
from flask import request,flash,Blueprint, g, render_template #jsonify,

import local.datamodel
from routes.common import safe_route

bp = Blueprint('queue', __name__)

@bp.route('/queue', methods=['GET','POST'])
@safe_route
def queue():
    """Display queue list page"""
    print("Queue Page")
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        g.item_selected = request.form.get('id',None)
        print(f"Action is {action}")
        if action =="create":
            return render_template('queue-item.html')

        if action =="edit":
            g.item_selected = request.form.get('id',None)
            return render_template('queue-item.html')

        if action == "delete":
            item_id = request.form['id'] # get the value of the clicked button
            local.db.DeleteQueue(item_id)
            return render_template('queue-list.html')

        ##          Queue-Item Actions
        if action == "item_create":
            #Create new queue details
            queue_name = request.form['name']
            print(f"Creating queue details for {queue_name}")
            print(f"Creating user ID is {g.data_model.user_id} in {g.data_model.project_id}")
            #AddNewIfNoneEx(self, item_type : str, item_lookup_field,field_list : dict) -> int:
            new_queue_id = g.data_model.AddNewIfNoneEx("queue","name", {"name" : queue_name})
            if new_queue_id < 0 :
                g.item_selected = abs(new_queue_id)
            else:
                flash("Cannot use an existing name - choose a unique name for the queue","Information")
            return render_template('queue-item.html')

        if action =="item_update":
            g.item_selected = request.form['id']
            queue_name = request.form['name']
            queue_skills =  request.form['skills']
            queue_hoo =  request.form['hoo']
            #Updated the QueueHOO to the numeric number
            item_exists = g.data_model.AddNewIfNoneEx("HOO","name",{ "name" : queue_hoo,
                                                        "description" : "<Added when creating queue - update details before publishing>"})
            #Now update the lookup so that we have the ID not the name in our lists
            queue_hoo = str(abs(item_exists))
            print(f"Updating queue details for {queue_name}")
            print(f"QueueHoo {queue_hoo}")
            err_msg  = local.db.UpdateQueue(g.item_selected,queue_name,queue_skills,queue_hoo)
            flash(err_msg,"Information")

            return render_template('queue-item.html')

        #Action updates from Queue-Item:
        if action =="queue_item_skill_new":
            #Append queueskill to list (table id!)
            g.item_selected = request.form.get('id',None)
            item = g.data_model.GetItem("queue",g.item_selected)
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

            print(f"Updating queue details for {queue_name}")
            local.db.Update("queue",{"name": queue_name, "skills" : queue_skills, "queuehoo" : queue_hoo}, {"id" : g.item_selected})
            actions = local.db.GetQueueActionsList(str(g.item_selected))
            return render_template('queue-item.html')

        if action =="queue_item_skill_remove":

            item_id = request.form['id']
            queue_name = request.form['name']
            queue_skills =  request.form['skills']
            queue_hoo = request.form['hoo']
            queue_skillremove = request.form['skill_remove']
            print(f"Removing: {queue_skillremove}")
            skill_array = queue_skills.split(",")
            queueskills =''
            if queue_skillremove in skill_array:
                skill_array.remove(queue_skillremove)
                queueskills = (",").join(skill_array)

            print(f"**Updating queue details for {queue_name}")
            print(f"**QueueHoo {queue_name}")
            local.db.UpdateQueue(item_id,queue_name,queueskills,queue_hoo)

            item = local.db.GetQueue(item_id)
            actions = local.db.GetQueueActionsList(item_id)
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
            return render_template('queueaction-item.html', queue_id = queue_id, action="queueaction")

        if action =="queue_action_delete":
            #Delete the queue action
            action_id = request.form['action_id']
            queue_id = request.form['queue_id']
            local.db.DeleteQueueAction(action_id)
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
            print(f'Param 1 {param_list[1]}')
            print(f'Param 2 {param_list[2]}')
            #g.data_model.AddNewIfNoneEx("queueaction","queue_id",{"queue_id" : queue_id, "action" : queue_action, "param1" : ', '.join(map(str, param_list), "step_id" : 0})
            local.db.AddQueueAction(queue_id,queue_action,(','.join(map(str, param_list)))[1:])
            g.item_selected = queue_id
            return render_template('queue-item.html')

        if action =="queueaction_update":
            action_id = request.form['id']
            queue_action = request.form['queueActionsDropdown']
            param_list = ["","","","","",""]
            param_list[1] = request.form.get('param1','')
            param_list[2] = request.form.get('param2','')
            param_list[3] = request.form.get('param3','')
            param_list[4] = request.form.get('param4','')
            param_list[5] = request.form.get('param5','')
            print(f'Param 1 {param_list[1]}')
            print(f'Param 2 {param_list[2]}')
            local.db.UpdateQueueAction(action_id,queue_action,(','.join(map(str, param_list)))[1:],"")

            g.item_selected = request.form['queue_id']
            return render_template('queue-item.html')

        if action =="queueaction_cancel":
            g.item_selected = request.form['queue_id']
            return render_template('queue-item.html')

        #Queue Hoo Operations
        if action =="queue_item_inqueueaction_new":
            queue_id = request.form['id']
            state = request.form['inqueueState']
            return render_template('queueaction-item.html', queue_id = queue_id, action="inqueue", state = state)
        
        if action =="queue_item_prequeueaction_new":
            queue_id = request.form['id']
            state = request.form['prequeueState']
            return render_template('queueaction-item.html', queue_id = queue_id, action="prequeue", state = state)
        
        if action == "queue_item_prequeueaction_remove":
            queue_id = request.form['id']
            action_to_remove = request.form['queue_item_prequeueaction_remove']
            local.db.DeleteQueueHooAction(queue_id,'QUEUE',action_to_remove)

            item = local.db.GetQueue(queue_id)
            return render_template('queue-item.html', item = item)
    print("Queue List")
    return render_template('queue-list.html')
