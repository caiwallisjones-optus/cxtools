"""##################################################################################################################
#   Description:    Provides a way to unify html/jinja/python with common code and data structures
#                   Helper used in web pages for dynamic content
##################################################################################################################"""
import os
from datetime import datetime, timedelta

from local import logger
import local.db
import local.cxone


class DataModel(object):
    """This is a view of data that the users can access based on their access priviledges"""
    __key  = None
    __secret = None
    __connection = None

    NEW_LINE = "\\r\\n"
    QUOTE = '\\"'
    TAB = "\\t"

    __ACTION_LIST = {

    }
    user_id = None
    project_id =  None
    connected_bu_name = None
    connected_bu_id = None
    errors = []

    def __init__(self, user_id : int, project_id :int):
        self.user_id = user_id
        self.project_id = project_id
    #  Current list of common actions used in menus
    #  CHECKHOURS,Check hours of operation
    #  PLAY,Play message
    #  MENU,Play menu and request a user response
    #  QUEUE,Exit CallFlow and queue to a skill
    #  TRANSFER,Transfer to a external number
    #  VOICEMAILOPT,Offer a voicemail within the CallFlow
    #  VOICEMAIL,Force call to voicemail within the CallFlow
    #  HANGUP,Hang up the call

    def __get_security_filter(self, table_name : str) -> dict:
        """Returns the user security filter based on the table name - prevent unauth access to datebase"""
        #Default to return only data for current project
        #match table_name:
        match table_name:
            case "config" :
                return {'id': -1} #Prevent access to config data through the web interface
            case "user" :
                return None
            case "project" :
                return {"user_id" : self.user_id}
            case table_name if table_name in ["audio", "queue", "callFlow", "poc", "hoo", "skill", "deployment"]:
                return {"project_id" : self.project_id}
        #queueAction
        #queuextendedvariables
        #callFlowAction
        #callFlowResponse
        #tasks# prevent access to these tables
        #role
        #permission
        #role_permission
        #user_role
        return  {'id': -1} #Prevent access to config data through the web interface

    def get_script_queue_actions(self) -> list:
        """Actions that can occur in a queue action"""
        return ["PLAY|PLAY - Play message and continue",
                "PLAYMUSIC|PLAYMUSIC - Play music based for period of  time",
                "PLAYMUSICEX|PLAYMUSICEX - Play music  from WAV file (include offset and duration)",
                "OFFERCALLBACK|CALLBACK - Offer callback to customer in queue",
                "VOICEMAILOPT|VOICEMAILOPT - Offer a voicemail within the call flow, continue if '1' is not selected",
                "EWT|PLAYEWT - Play estimated wait time",
                "PLACEINQUEUE|PLAYPIQ - Play place in queue",
                "NEXTSCRIPT|SCRIPT - Start custom script (PS Required)",
                "CUSTOMEVENT|CUSTOM - Execute custom action (PS required)",
                ]

    def get_script_menu_actions(self) -> list:
        """Actions that can occur in a menu action"""
        return ["CHECKHOURS|CHECKHOO -Check attached hours of operation state",
                "PLAY|PLAY - Play message and continue",
                "MENU|MENU - Play menu and request a user response",
                "QUEUE|QUEUE - Queue call to a skill",
                "TRANSFER|XFER - call an external number",
                "VOICEMAILOPT|VOICEMAILOPT - Offer a voicemail within the call flow, continue if '1' is not selected",
                "VOICEMAIL|VOICEMAIL - Force call to voicemail and terminate call",
                "HANGUP|HANGUP - Play message, then terminate call",
                "CUSTOMEVENT|CUSTOM - Execute custom action (PS required)",
                "NEXTSCRIPT|SCRIPT - Exit queue and apply custom actions (PS Required)",]

    def get_script_hoo_actions(self) -> list:
        """Actions that can occur in an HOO action"""
        return ["PLAY|PLAY - Play message and continue",
                "TRANSFER|XFER - call an external number",
                "VOICEMAIL|VOICEMAIL - Force call to voicemail and terminate call",
                "CALLBACK|CALLBACK - Offer callback to customer in queue",
                "HANGUP|HANGUP - Play message, then terminate call",
                "CUSTOMEVENT|CUSTOM - Execute custom action (PS required)",
                "NEXTSCRIPT|SCRIPT - Exit queue and apply custom actions (PS Required)",]

    def get_script_action_params(self,action : str  ) -> list :
        match action:
            case "CHECKHOURS":
                return ["Select Hours of operation to check|HOO_LOOKUP"]
            case "PLAY":
                return ["Filename to play|AUDIO_LOOKUP"]
            case "PLAYMUSIC":
                return ["Duration to play hold music|TEXT"]
            case "PLAYMUSICEX":
                return ["Filename to play for menu|AUDIO_LOOKUP","Start offset to play within file|TEXT","Duration to play|TEXT",]
            case "MENU":
                return ["Filename to play for menu|AUDIO_LOOKUP",
                        "Number of times to repeat the menu before naviagting to the fallback option (leave blank to keep repeating)|TEXT",
                        "Next step (0-9/Hash/Star)|TEXT","Suppress Error messages (true/false)|BOOL"]
            case "QUEUE":
                return ["Skill to queue call|SKILL_LOOKUP","Whisper on call answer (wav)|AUDIO_LOOKUP",
                        "Message to Pop|TEXT","Override Priority|TEXT","Override Routing|TEXT"]
            case "TRANSFER":
                return ["Filename to play before call transfer|AUDIO_LOOKUP","Number to transfer call to (E164)|TEXT"]
            case "CALLBACK":
                return ["Filename to play before callback|AUDIO_LOOKUP"]
            case "OFFERCAllBACK":
                return ["Filename to offer callback, (option 1 initiates callback)|AUDIO_LOOKUP"]
            case "VOICEMAIL":
                return ["Filename to play before voicemail|AUDIO_LOOKUP",
                        "Voicemail skill to submit call|SKILL_LOOKUP",
                        "Alternate email address to send VM|TEXT"]
            case "VOICEMAILOPT":
                return ["Filename to offer voicemail (option 1, default continues to next action)|AUDIO_LOOKUP",
                        "Voicemail skill to submit call|SKILL_LOOKUP",
                        "Alternate email address to send VM|TEXT"]
            case "HANGUP":
                return ["Filename to play before hangup|AUDIO_LOOKUP"]
            case "NEXTSCRIPT":
                return ["Script Name to execute |TEXT","Parameters to pass to script|TEXT"]
            case "CUSTOMEVENT":
                return ["Custom Script to execute|TEXT","Parameters to pass to script|TEXT"]
            #Specific to Queue and not common actions
            case "CUSTOMQUEUEEVENT":
                return ["Custom Script to execute|TEXT","Parameters to pass to script|TEXT"]
            case "PLACEINQUEUE":
                return ["File to play 'You are currently...'|AUDIO_LOOKUP","File to play '...in the queue'|AUDIO_LOOKUP"]
            case "EWT":
                return []
            case _:
                return ["Unknown Action Parameters - see Optus for details|TEXT"]

    def get_script_action_type_responses(self,action):
        if action == "CHECKHOURS":
            return ["Closed","Emergency","Meeting","Holiday","Weather","Other","Open" ]
        if action == "MENU":
            return  ["1","2","3","4","5","6","7","8","9","0","Star","Hash"]
        return None

    def get_script_action_has_default(self,action):
        """Returns true if the action is not a final action"""
        if action in [ "CHECKHOURS" , "PLAY" , "VOICEMAILOPT","CUSTOMEVENT","CUSTOMQUEUEEVENT"]:
            return True
        #  QUEUE, TRANSFER,VOICEMAIL,HANGUP
        return False

    def request_paramlist(self,request) -> dict:
        """Reads the active request from the web page and builds a list of parameters to add/update item in DB"""
        #if request.endpoint == "project":
        parameters = dict(request.form )
        parameters.pop('id')
        parameters.pop('action')
        #Custom for projects
        if request.endpoint == "project":
            parameters['user_id'] = self.user_id
        if request.endpoint == "poc":
            parameters.pop('external_id')
        if request.endpoint == "skill":
            parameters.pop('external_id')
        if request.endpoint == "hoo":
            parameters.pop('external_id')
        return parameters

    def is_authorised(self,auth_right : int) -> bool:
        """Returns true if the user is authorised to access the auth_right"""
        sql_query = "SELECT name FROM user_role INNER JOIN role_permission, permission ON role_permission.role_id  =  user_role.role_id " + \
                        f"AND permission.id = role_permission.permission_id  WHERE user_role.user_id = {self.user_id } AND permission.name = '{auth_right}'"
        results = local.db.select_query(sql_query)

        return len(results) > 0

    def db_get_list(self,list_type : str) -> list[dict]:
        """Read the application DB table and return all results as a list of dict
        param: list_type: The name of the table to query (using the current active project Id). """
        if list_type == "user" and self.is_authorised("ADMIN"):
            return local.db.select(list_type,["*"],{})
        no_project_id = False
        if list_type in ["config","user","project","queueaction", "callflowaction","callflowresponse",""]:
            #These tables to not restrict by project ID - so are less protected - we need to ensure that this is not used
            # inappropriately
            no_project_id = True
        if no_project_id:
            return local.db.select(list_type,["*"],{"user_id" : self.user_id})
        else:
            return local.db.select(list_type,["*"],{"project_id" : self.project_id})


    def db_get_list_filtered(self,list_type : str, filter_list : dict ) -> list[dict]:
        """Read the application DB table and return all results as a list of dict including filter
        param: list_type: The name of the table to query (using the current active project Id). """
        #NOTE ensure all tables have a project_id and add that in there!!!
        return local.db.select(list_type,["*"],filter_list)

    def db_get_item(self,item_type :str , item_id : int) -> dict:
        """Read the application DB table for item_type and return first item as a dict\n
           :param: item_type - the name of the table to query (using the current active project Id , and item_id).\n 
           :param: item_id: - the id of the record in the table
           :returns: dict of the item or None if not found"""
        item_type = item_type.lower()
        if item_type == "project":
            return local.db.select_first(item_type,["*"],{"id" : item_id})
        if item_type == "config":
            return local.db.select_first(item_type,["*"],{"key" : item_id})
        if item_type == "queueaction":
            return local.db.select_first(item_type,["*"],{"id" : item_id})
        if item_type == "callflowaction":
            return local.db.select_first(item_type,["*"],{"id" : item_id})
        if item_type == "callflowresponse":
            return local.db.select_first(item_type,["*"],{"id" : item_id})
        if item_id is None:
            return None
        return local.db.select_first(item_type,["*"],{"project_id" : self.project_id , "id" : item_id})

    def db_get_value(self,item_type : str, lookup_field: str,lookup_value: str,return_field: str) -> object:
        """Read the DB table for item_type record and return the value expected"""
        if item_type is None or lookup_field is None or lookup_value is None or return_field is None or lookup_value == '':
            return ''
        no_project_id = False
        if item_type in ["config","user","project","queueaction", "callflowaction","callflowresponse",""]:
            #These tables to not restrict by project ID - so are less protected - we need to ensure that this is not used
            # inappropriately
            no_project_id = True
        if no_project_id:
            result = local.db.select_first(item_type,["*"],{lookup_field :lookup_value})
        else:
            result = local.db.select_first(item_type,["*"],{"project_id" : self.project_id , lookup_field :lookup_value})
        if result is None:
            return None
        return result.get(return_field,None)

    def db_insert(self, table_name : str ,field_values : dict) -> int:
        """Insert new item \n
        Note this does not work on tables with no project ID at this time \n
        :param: table_name - name of table
        :param: field_values - dict of values to insert into DB
        :returns: id of new record """
        return local.db.insert(table_name,field_values)

    def db_insert_or_update(self, item_type : str, item_lookup_field : str ,field_list : dict) -> int:
        """Insert/Update item \n
        Note this does not work on tables with no project ID at this time \n
        :param: table_name - name of table
        :param: item_lookup_field - name of field we are looking for existing item
        :param: field list - dictionary of field name/value kvp 
        
        :returns: Negative item table ID  if new item, item table ID if existing item"""
        item_type = item_type.lower()
        no_project_id = False
        if item_type in ["config","user","project","queueaction", "callflowaction","callflowresponse",""]:
            #These tables to not restrict by project ID - so are less protected - we need to ensure that this is not used
            # inappropriately
            no_project_id = True

        if no_project_id:
            #Get the item if it exist by checking the name and return the ID
            existing = local.db.select_first(item_type,["id"],
                            {item_lookup_field : field_list[item_lookup_field] })
        else:
            #Get the item if it exist by checking the name and return the ID
            existing = local.db.select_first(item_type,["id"],
                            {"project_id" : self.project_id , item_lookup_field : field_list[item_lookup_field] })

        if existing is None or len(existing) == 0:
            if not no_project_id:
                field_list['project_id'] = self.project_id
            return -local.db.insert(item_type ,field_list)
        return existing['id']

    def db_update(self, item_type : str, item_id : int, field_list : dict) -> bool:
        """Update item in the DB"""
        if item_id is None or len(field_list) == 0 or item_type is None:
            return False
        item_type = item_type.upper()
        no_project_id = False
        if item_type in ["PROJECT","USER","QUEUEACTION","CALLFLOWACTION","CALLFLOWRESPONSE"]:
            #These tables to not restrict by project ID - so are less protected - we need to ensure that this is not used
            # inappropriately
            no_project_id = True

        if no_project_id:
            return local.db.update(item_type,field_list,{"id" : item_id})
        else:
            return local.db.update(item_type,field_list,{"project_id" : self.project_id , "id" : item_id})

    def db_delete(self, item_type : str, item_id : int) -> bool:
        """Delete item from the lcal database
        :param: item_id - this will be the id in the table
        :return: """
        if item_type == "project":
            local.db.delete(item_type,{"id" : item_id})
            return True
        if item_type == "queueaction":
            local.db.delete(item_type,{"id" : item_id})
            return True
        if item_type == "callFlowAction":
            local.db.delete(item_type,{"id" : item_id})
            return True
        if item_type == "callFlowResponse":
            local.db.delete(item_type,{"id" : item_id})
            return True
        if item_id is None:
            return False
        return local.db.delete(item_type,{"project_id" : self.project_id , "id" : item_id})

    #We cant have two routes to the same event so this cheats:
    def script_get_action_breadcrumb(self,action_id : int) -> list:
        """Return a simple list so we can create a breadcrumb to the selected action"""
        def get_parent(breadcrumb_list, action_id : int) -> list:
            prior_action_id = local.db.select("callFlowResponse",["callFlowAction_id"],{ 'callFlowNextAction_id' : action_id})
            if len(prior_action_id) > 0 :
                prior_action = local.db.select("callFlowAction",["name","id"],{ 'id' : prior_action_id[0]['callFlowAction_id']})
                breadcrumb_list.insert(0,((prior_action[0]['name'] , prior_action[0]['id'],)))
                return get_parent(breadcrumb_list,prior_action_id[0]['callFlowAction_id'])
            else:
                return breadcrumb_list
        #Get parent and add to list
        breadcrumbs = []
        breadcrumbs = get_parent(breadcrumbs,action_id)
        #Get the response that lead to this action
        return breadcrumbs

    def export_dnis_switch(self) -> str:
        """Build the IVR menu's and entry points"""
        self.errors = []

        dnis_text = ""
        for call_flow in local.db.select("callFlow",["*"], {"project_id" : self.project_id}):
            logger.info("Parsing callflow %s", call_flow['id'])
            if call_flow['poc_list']:
                for poc in call_flow['poc_list'].split(','):
                    logger.info("Adding DNIS switch for POC %s" , poc)
                    poc_name = local.db.select_first("poc",["*"], {"project_id" : self.project_id , "id" : poc})
                    if poc_name is None:
                        logger.warning("POC with ID %s not found.", poc)
                        self.errors.append(f"POC with ID {poc} not found.")
                        dnis_text += self.TAB + 'CASE '+ self.QUOTE + "UNKNOWN" + self.QUOTE +  self.TAB + '//' + call_flow['name'] + self.NEW_LINE
                    else:
                        dnis_text += self.TAB + 'CASE '+ self.QUOTE + poc_name['name'] + self.QUOTE +  self.TAB + '//' + call_flow['name'] + self.NEW_LINE
            else:
                logger.info("Unable to add POC for call flow %s", call_flow['id'])
                self.errors.append(f"Unable to get POC for call flow {call_flow['name']}")
            dnis_text += self.TAB + '{' + self.NEW_LINE
            self.prune_callflow(call_flow['id'])
            #Create actions
            for action in local.db.select("callFlowAction","*",{"callFlow_id" : call_flow['id']}):
                dnis_text += self.TAB + 'AddOption('+ self.QUOTE +action['name'] + "," + action['action'] + ","
                #And get our params sorted here
                action_params = self.get_script_action_params(action['action'])
                param_list = str(action['params']).split(",") if action['params'] is not None else []
                converted_params = ""
                for index,param in enumerate(action_params):
                    #Only perform this if there is a value in the param_list that we can use
                    if len(param_list) > index:
                        param_type = param.split("|")[1]
                        if param_type.endswith('LOOKUP'):
                            if param_type[:-7] ==  "AUDIO":
                                converted_param = str(self.db_get_value(param_type[:-7],"id",param_list[index],"name"))
                            else:
                                converted_param = str(self.db_get_value(param_type[:-7],"id",param_list[index],"external_id"))
                            if len(converted_param) < 1 or converted_param == 'None':
                                converted_param = ""
                            #    logger.debug("Error adding action %s - %s - %s " ,{action['id']} , {action['action']} , {action['name']} )
                            #    self.errors.append(f"Unable to locate parameter for action {action['action']} named {action['name']} -
                            #       please ensure the action parameters have been syncronised")
                            converted_params += converted_param + ","
                        else:
                            if index >= len(param_list):
                                converted_params += ","
                            else:
                                converted_params += param_list[index] + ","

                # Add queue name to the end of the action line
                if action['action'] == "QUEUE":
                    dnis_text +=  converted_params + self.QUOTE + ')' + self.TAB + "//" + \
                        str(self.db_get_value("SKILL","id",param_list[0],"name") + self.NEW_LINE)
                elif action['action'] == "CHECKHOURS" and len(param_list) > 0:
                    hoo_name = str(self.db_get_value("HOO","id",param_list[0],"name"))
                    if hoo_name is None or len(hoo_name) == 0:
                        logger.debug("Error adding action %s - %s - %s " ,{action['id']} , {action['action']} , {action['name']} )
                        self.errors.append(f"Unable to locate parameter for action {action['action']} named {action['name']}")
                    else:
                        dnis_text +=  converted_params + self.QUOTE + ')' + self.TAB + "//" + \
                            hoo_name + self.NEW_LINE
                else:
                    dnis_text += converted_params + self.QUOTE + ')' + self.NEW_LINE
            dnis_text += self.NEW_LINE
            for response in local.db.select("callFlowResponse","*",{"callFlow_id" : call_flow['id']}):
                #Test for responses that havent been configured
                if response['callFlowNextAction_id'] is not None:
                    parent_name = local.db.select("callFlowAction","*",{"id" : response['callFlowAction_id']})[0]['name']
                    child_name = local.db.select("callFlowAction","*",{"id" : response['callFlowNextAction_id']})[0]['name']
                    dnis_text += self.TAB + 'AddResponse('+ self.QUOTE + parent_name + "," + response['response'] + "," + \
                                                          child_name + self.QUOTE + ')' + self.NEW_LINE
                else:
                    logger.debug("Error adding response %s " ,{response['id']} )
                    self.errors.append(f"Some call flow responses are not terminated for response ID: {response['id']}")

            dnis_text += self.NEW_LINE

            dnis_text += self.TAB + '}' + self.NEW_LINE
            #hooProfile and HooActions embedded in menu - not needed
        return dnis_text

    def export_queue_switch(self) -> str:
        """Build the text to define all active queue data, to upload to CXone"""
        self.errors = []

        queue_text = ""
        queues = local.db.select("queue",["*"], {"project_id" : self.project_id})
        for queue in queues:
            if queue['skills'] and queue['skills'] != 'None':
                for skill_id in queue['skills'].split(','):
                    if skill_id != "None":
                        skill = local.db.select('skill',['external_id', 'name'],{ 'id': skill_id})
                        if skill is None or len(skill) == 0:
                            queue_text += self.TAB + 'CASE ' +self.QUOTE + "UNKNOWN_SKILL" +self.QUOTE + self.TAB+'//' + "**DELETED SKILL in queue " + queue['name'] + self.NEW_LINE
                        else:
                            queue_text += self.TAB + 'CASE ' +self.QUOTE + str(skill[0]['external_id']) +self.QUOTE + self.TAB+'//' + skill[0]['name'] + self.NEW_LINE

                queue_text += self.TAB + '{' + self.NEW_LINE

                #Queue HOO config
                if queue['queuehoo'] is None:
                    logger.debug("Error locating HOO for queue %s " ,{queue['id']})
                    self.errors.append(f"Unable to locate HOO for queue {queue['name']}")
                    queue_text += self.TAB + 'ASSIGN global:hooProfile = '+ self.QUOTE + self.QUOTE + self.NEW_LINE
                else:
                    queue_hoo_external_id = local.db.select('hoo',['external_id'],{ 'id': str(queue['queuehoo'])})
                    if queue_hoo_external_id is None or len(queue_hoo_external_id) == 0:
                        logger.debug("Error locating external ID  for HOO in queue %s " ,{queue['id']})
                        self.errors.append(f"Error locating external ID  for HOO in queue {queue['name']}")
                    else:
                        queue_text += self.TAB + 'ASSIGN global:hooProfile = '+self.QUOTE+str(queue_hoo_external_id[0]['external_id'])+self.QUOTE + self.NEW_LINE

                    #Add extended attributes
                    if queue['extendedattributes'] is not None:
                        for attribute in queue['extendedattributes'].split('|'):
                            queue_text += self.TAB + 'global:' + attribute + self.NEW_LINE

                    #Add pre-queue and queue hoo action - these were added verbatim
                    if queue['prequeehooactions'] is not None:
                        for action in queue['prequeehooactions'].split('|'):
                            queue_text += self.TAB + 'AddPreQueueHooAction(' + self.QUOTE + action + self.QUOTE + ')' + self.NEW_LINE
                    if queue['queehooactions'] is not None:
                        for action in queue['queehooactions'].split('|'):
                            queue_text += self.TAB + 'AddQueueHooAction(' + self.QUOTE + action + self.QUOTE + ')' + self.NEW_LINE

                #Add queue actions
                queue_actions = local.db.select("queueAction","*", { 'queue_id' : queue['id'] })
                for action in queue_actions:
                    queue_text += self.TAB + 'AddQueueAction(' + self.QUOTE +action['action'] + ':'  +str(action['param1']) + self.QUOTE + ')'+ self.NEW_LINE

                queue_text += self.TAB + '}' + self.NEW_LINE
            else:
                self.errors.append(f"Unable to identify skills attached to queue {queue['name']} - skipped")

        return queue_text

    def prune_callflow(self,call_flow_id : int) -> bool:
        """Remove all unlinked actions and responses for a call flow"""

        while True:
            callflow_root = local.db.select_first("callFlow", ['callFlowAction_id'], {"id": call_flow_id}).get('callFlowAction_id', None)
            if callflow_root is None:
                logger.info("No actions in call flow")
                return True

            actions = local.db.select("callFlowAction", ["id"], {"callFlow_id": call_flow_id})
            responses = local.db.select("callFlowResponse", ["id", "callFlowAction_id", "callFlowNextAction_id"], {"callFlow_id": call_flow_id})
            linked_actions = [x['callFlowNextAction_id'] for x in responses if x['callFlowNextAction_id'] is not None]
            linked_actions.append(callflow_root)
            linked_actions = list(set(linked_actions))

            actions_to_delete = [action['id'] for action in actions if action['id'] not in linked_actions]
            responses_to_delete = [response['id'] for response in responses if response['callFlowAction_id'] not in linked_actions]

            if not actions_to_delete and not responses_to_delete:
                break

            for action_id in actions_to_delete:
                logger.info("Removing action %s", action_id)
                local.db.delete("callFlowAction", {"id": action_id})

            for response_id in responses_to_delete:
                logger.info("Removing response %s", response_id)
                local.db.delete("callFlowResponse", {"id": response_id})

        return True

    def build_param_list(self, action_type :str, params :list) -> str:
        """Return comma seprated list of all the params
        Note that the action type would allow look ups but we havent used it"""
        logger.info("Buildingf param list %s" , action_type)
        comma_separated_string = ""
        for item in params:
            if item is None:
                comma_separated_string += ','
            else:
                comma_separated_string += item + ','
        comma_separated_string = comma_separated_string.rstrip(',')
        return comma_separated_string

    def AddNewIfNoneAdmin(self, item_type : str, item_lookup_field,field_list : dict) -> int:
        """Quickly add AUDIO/SKILL/HOO
        RETURNS True if created, False if existing"""
        item_type = item_type.upper()
        existing = local.db.select_first(item_type,["id"], {item_lookup_field : field_list[item_lookup_field] })
        if len(existing) == 0:
            return -local.db.insert(item_type ,field_list)
        return existing['id']

    def package_validated(self, package_element :str ) -> bool:
        logger.info("is_valid_package_ement %s ", package_element )
        query = f"SELECT created FROM deployment WHERE project_id = {self.project_id} AND " \
                    + f"action_object = '{package_element}' AND success_state = 1 AND action = 'validate' AND " \
                    + f"created >= '{datetime.today()- timedelta(1)}' LIMIT 1"

        result = local.db.select_query(query)
        if result:
            return True
        return False

    def validate_connection(self) -> bool:
        project = local.db.select_first("project","*",{"id" : self.project_id })

        self.__key  = project['user_key']
        self.__secret = project['user_secret']
        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                business_unit = self.__connection.get_business_unit()
                self.connected_bu_name = business_unit['businessUnitName']
                self.connected_bu_id = business_unit['businessUnitId']
                local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "connection",
                                              "description" : "Connected successfully to business unit","success_state" : True })
                return True
        finally:
            pass
        local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "connection",
                                      "description" : "Failed to connect to business unit","success_state" : False })
        return False

    def validate_package(self) -> bool:

        errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']

        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                local_files = []
                remote_files = set(self.__connection.get_scripts_list())
                local_root = ".//packages//" +project['deployment_type'].lower()+ "//scripts//"
                remote_root = project['instance_name'] + ( "\\" if len(project['instance_name']) >0 else "" )
                for path, subdirs, files in os.walk(local_root):
                    for name in files:
                        logger.info("Found file to load: %s %s %s ", path,subdirs, files)
                        local_files.append(os.path.join(path[len(local_root):], name))
                        logger.info(os.path.join(path[len(local_root):], name))
                for filename in local_files:
                    if remote_root + filename[:-5] in remote_files:
                        errors.append(f"File found in destination path: {filename}" )
                    else:
                        logger.info("Remote file not found (valid): %s" , filename)
                if not errors:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "script",
                                                  "description" : "Identified files at project darget destination","success_state" : True })
                    return True
                else:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "script",
                                                  "description" : "Identified files at project darget destination","success_state" : False })
                    self.errors = errors
                    return False
        finally:
            pass
        return False

    def validate_audio(self) -> bool:
        errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']

        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                remote_root = project['instance_name'] + "/" + "prompts"
                local_files = []
                for file in local.db.select("audio",['name'],{"project_id" : self.project_id }):
                    local_files.append(remote_root + "/" + file['name'].replace("\\", "/"))
                remote_files = self.__connection.get_audio_list(remote_root)
                for filename in remote_files:
                    if(filename['fileNameWithPath'][:-4] in local_files) and (filename['isFolder'] is False):
                        errors.append(f"File found in destination: {filename['fileNameWithPath']}" )
                    else:
                        logger.info("Remote file not found in source files (valid): %s ", filename['fileNameWithPath'])
                if not errors:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "audio",
                                                  "description" : "No existing files in destination path","success_state" : True })
                    return True
                else:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "audio",
                                                  "description" : "Identified audio at project darget destination","success_state" : True })
                    errors.append("If you select DEPLOY all files that have been modified will be overwritten" )
                    self.errors = errors
                    return False
        finally:
            pass

        return False

    def validate_skills_config(self) -> bool:
        """Load skills from BU and determine if there are issues"""
        errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']

        #Read current skills
        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                local_skills = local.db.select("skill",["*"],{"project_id" : self.project_id })
                remote_skills = self.__connection.get_skill_list()
                for remote_skill in remote_skills:
                    for skill in local_skills:
                        if skill['name'] == remote_skill["skill_name"]:
                            if skill['external_id'] !='':
                                errors.append(f"Skill name and external ID located: {skill['name']}" )
                            else:
                                errors.append(f"Skill name located (sync to update external ID): {skill['name']}" )
                        else:
                            pass
                            #logger.info(f"Local skill not found at destination (valid): {skill['Name']}")
                if not errors:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "skill",
                                                  "description" : "Skills list validated with no overlap","success_state" : True })
                    return True
                else:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "skill",
                                                  "description" : "Skill names overlap","success_state" : True })
                    self.errors = errors
                    return False
        finally:
            pass
        return False

    def validate_hoo_config(self) -> bool:
        """Load hoo from BU and determine if there are issues"""
        errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']

        #Read current HOO
        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                local_hoo = local.db.select("hoo",["*"],{"project_id" : self.project_id })
                remote_hoos = self.__connection.get_hoo_list()
                for remote_hoo in remote_hoos:
                    for hoo in local_hoo:
                        if hoo['name'] == remote_hoo["hoursOfOperationProfileName"]:
                            if hoo['external_id'] =='':
                                errors.append(f"HOO found in BU - system HOO ID updated: {hoo['Name']}" )
                        else:
                            pass
                            #logger.info(f"Local skill not found at destination (valid): {skill['Name']}")
                if not errors:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "hoo",
                                                  "description" : "HOO list validated with no overlap","success_state" : True })
                    return True
                else:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "hoo",
                                                  "description" : "HOO names overlap","success_state" : False })
                    self.errors = errors
                    return False
        finally:
            pass
        return False

    def upload_package(self) -> bool:
        errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']

        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                local_files = []
                local_root = ".//packages//" +project['deployment_type'].lower()+ "//scripts//"
                remote_root_path = project['instance_name']
                for path, subdirs, files in os.walk(local_root):
                    for name in files:
                        logger.info("Creating script from : %s %s %s ", path,subdirs, files)
                        local_files.append(os.path.join(path[len(local_root):], name))
                for local_filename in local_files:

                    self.__connection.create_script(local_root, local_filename, remote_root_path)
                if not errors:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "upload", "action_object" : "script",
                                                  "description" : "Files Uploaded","success_state" : True })
                    return True
                else:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "upload", "action_object" : "script",
                                                  "description" : "Error uploading files","success_state" : False })
                    return False
        finally:
            pass
        return False

    def upload_audio_package(self) -> bool:
        self.errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']

        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                file_actions = []
                remote_root = project['instance_name'] + "/prompts/"
                file_actions =  [{**file, 'remote_path_file'.replace('\\', '/') : remote_root + file['name'] + '.wav',
                                  "local_file_path" : "./users/" + str(self.project_id) } for file in local.db.select("audio",['name','description',
                                    'isSynced','id'],{"project_id" : self.project_id })]

                #tts set-up
                sub_key = local.db.get_setting("tts_key")
                voice_font = "en-AU-NatashaNeural"
                tts = local.tts.Speech(sub_key)

                #And upload
                for file in file_actions:
                    if file['isSynced'] != 1:
                        audio_response = tts.get_audio(file['description'], voice_font)
                        result = self.__connection.upload_file(file['remote_path_file'].replace("\\","/"),audio_response)
                        if result == 200:
                            local.db.update("audio",{"isSynced" : True } , {"project_id" : self.project_id , "id" : file['id']})

                local.db.insert("deployment",{"project_id" :project['id'] , "action" : "deploy", "action_object" : "audio",
                                              "description" : "Uploaded audio files","success_state" : True })
                return True
        finally:
            pass

        return False

    def upload_hoo(self) -> bool:
        self.errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']
        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                hoo_actions =  local.db.select("hoo",["*"],{"project_id" : self.project_id})
                for hoo in hoo_actions:
                    if hoo['external_id'] is None:
                        external_id = self.__connection.create_hoo(hoo['name'])
                        local.db.update("hoo",{'external_id': external_id },{"project_id" : self.project_id , "id" : hoo['id'] })

                local.db.insert("deployment",{"project_id" :project['id'] , "action" : "deploy", "action_object" : "hoo",
                                              "description" : "Uploaded HOO to BU","success_state" : True })
        finally:
            pass
        return False

    def upload_skills(self) -> bool:
        self.errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']
        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                internal_skills =local.db.select("skill",["*"],{"project_id" : self.project_id})

                camapign_list = self.__connection.get_campaign_list()
                default_campaign_id = 0
                for campaign in camapign_list:
                    if campaign['campaign_name'] == "Default":
                        default_campaign_id = campaign['campaign_id']
                        break
                if default_campaign_id == 0:
                    default_campaign_id = self.__connection.create_capaign("Default")

                for skill in internal_skills:
                    if skill['external_id'] is None:
                        external_id = self.__connection.create_skill(skill['name'],skill['skill_type'], default_campaign_id)
                        if external_id is not None:
                            local.db.update("skill",{'external_id': external_id },{"project_id" : self.project_id , "id" : skill['id'] })
                        else:
                            self.errors.append(f"Unable to upload {skill['name']} - "\
                                                + "name must contain at least two characters and a maximum of thirty, and may only contain letters,"\
                                                + "numbers and the special characters ( . - _ : )")
                local.db.insert("deployment",{"project_id" :project['id'] , "action" : "deploy", "action_object" : "skill",
                                              "description" : "Updated skills in BU","success_state" : True })
                return True
        finally:
            pass
        return False

    def get_queue_tables(self) -> list:
        """Retrieve the list of queue tables from the database."""
        data = local.db.select("queue", ["*"],{ "project_id" : self.project_id })
        for item in data:
            prompts_list = []
            skills = item['skills']
            updated_skills = []
            if skills is not None:
                skills = skills.split(',')
                for skill in skills:
                    updated_skill = self.db_get_value("skill","id",skill,"name")
                    if updated_skill is not None:
                        updated_skills.append(updated_skill)
                    else:
                        updated_skills.append("Deleted skill")
                item['skills'] = "|".join(updated_skills)

            hoo_id = item['queuehoo']
            if hoo_id is not None:
                hoo = self.db_get_item("hoo",hoo_id)
                if hoo is not None:
                    if hoo['daily_pattern'] is not None:
                        item['daily_pattern'] = hoo['daily_pattern'].replace(",","|")
                    else:
                        item['daily_pattern'] = "Undefined"
                    item['holiday_pattern'] = hoo['holiday_pattern']
                    item['queuehoo'] = hoo['name']
                else:
                    item['daily_pattern'] = "Undefined"
                    item['holiday_pattern'] = "Undefined"
                    item['queuehoo'] = "Undefined"
            else:
                item['daily_pattern'] = "Undefined"
                item['holiday_pattern'] = "Undefined"
                item['queuehoo'] = "Undefined"
            #Add the queue prompts to the list
            #Unattended,VOICEMAIL,CCG_Unattended,CCG_Voicemail,,,
            queue_items = item.get('prequeehooactions',"")  or ""
            prompts_list = []
            if queue_items != "":
                queue_items = queue_items.split('|')
                for queue_item in queue_items:
                    if queue_item is not None and len(queue_item) > 2:
                        try:
                            prompts_list.append(queue_item.split(',')[2])
                        except IndexError:
                            logger.debug("Error parsing queue item %s" , queue_item)
                            self.errors.append(f"Error parsing queue item {queue_item}")

            queue_items = item.get('queehooactions',"") or ""
            if queue_items != "":
                queue_items = queue_items.split('|')
                for queue_item in queue_items:
                    if queue_item is not None and len(queue_item) > 2:
                        try:
                            prompts_list.append(queue_item.split(',')[2])
                        except IndexError:
                            logger.debug("Error parsing queue item %s" , queue_item)
                            self.errors.append(f"Error parsing queue item {queue_item}")

            actions = self.db_get_list_filtered("queueAction",{"queue_id" : item["id"]})
            queue_actions = []
            if actions is not None:
                for action in actions:
                    queue_actions.append((action['action']) + ":" + str(action['param1']))
                    prompts_list.append(str(action['param1']).split(',')[0])
            item['queue_actions'] = "|".join(queue_actions)
            #Remove duplicates and numbers
            prompts_list = list(set(prompts_list))
            item['prompts'] = "|".join(prompts_list)

        return data

    def get_dnis_tables(self) -> list:
        """Retrieve the list of callflows."""
        expanded_call_flow = []
        data = local.db.select("callflow", ["*"],{ "project_id" : self.project_id })
        #For each callflow enumerate the actions
        for call_flow in data:
            logger.info("Processing call flow %s", call_flow['name'])
            call_flow_actions = self.db_get_list_filtered("callFlowAction",{ "callFlow_id" : call_flow['id']})
            for action in call_flow_actions:
                new_line = call_flow.copy()
                for k, v in action.items():
                    new_line["action_"+k] = v
                #Now add all next actions responses
                call_flow_responses = self.db_get_list_filtered("callFlowResponse",{ "callFlowAction_id" : action['id']})
                logger.debug(repr(call_flow_responses))
                call_flow_responses = sorted(call_flow_responses, key=lambda item: list(item.values())[3])
                
                responses_id = []
                responses_name = []
                #Get all unconnected items first
                for response in call_flow_responses:
                    child_responses = self.db_get_list_filtered("callFlowResponse",{ "callFlowAction_id" : response['callFlowNextAction_id']})
                    if len(child_responses) < 1:
                        responses_name.append(response['response'])
                        responses_id.append(str(response['callFlowNextAction_id']))
                #Now add the rest of them
                for response in call_flow_responses:
                    if response['response'] not in responses_name:
                        responses_name.append(response['response'])
                        responses_id.append(str(response['callFlowNextAction_id']))

                new_line['responses_name'] = "|".join(responses_name)
                new_line['responses_id'] = "|".join(responses_id)

                #Now work out the action params
                #Convert the actgion params to something we can use
                param_types = self.get_script_action_params(new_line["action_action"])
                if new_line["action_params"] is None:
                    new_line["action_params"] = ""
                param_values = new_line["action_params"].split(",")
                #Enumerate through the paramvalues and extract the type from the param_types
                #For each param value, if it is a lookup type, convert it to the name of the item
                #If it is a number, convert it to the name of the item
                for index , value in enumerate(param_values):
                    if value is not None and len(value) > 0:
                        param_type =param_types[index].split("|")[1]
                        if param_type == "AUDIO_LOOKUP":
                            param_result = self.db_get_list_filtered("audio",{"id" : value})
                            if len(param_result) > 0:
                                param_values[index] = param_result[0]['name']
                        elif param_type == "SKILL_LOOKUP":
                            param_result = self.db_get_list_filtered("skill",{"id" : value})
                            if len(param_result) > 0:
                                param_values[index] = param_result[0]['name']
                        elif param_type == "HOO_LOOKUP":
                            param_result = self.db_get_list_filtered("hoo",{"id" : value})
                            if len(param_result) > 0:
                                param_values[index] = param_result[0]['name']

                new_line['action_expanded_params'] = "|".join(param_values)
                expanded_call_flow.append(new_line)

        return expanded_call_flow
