"""##################################################################################################################
#   Description:    Provides a way to unify html/jinja/python with common code and data structures
#                   Helper used in web pages for dynamic content
##################################################################################################################"""
import os

from local import logger
import local.db
import local.cxone

class DataModel(object):
    """This is a view of data that the users can access based on their access priviledges"""
    __key  = None
    __secret = None
    __connection = None

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
                return None #TODO as user access is not restricted by project_id
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

    #Return list where we have ACTION|Explanation
    def GetQueueActions(self) -> list:
        return ["PLAY|PLAY - Play message and continue",
                "PLAYMUSIC|PLAYMUSIC - Play music based for period of  time",
                "PLAYMUSICEX|PLAYMUSICEX - Play music  from WAV file (include offset and duration)",
                "OFFERCAllBACK|CALLBACK - Offer callback to customer in queue",
                "VOICEMAILOPT|VOICEMAILOPT - Offer a voicemail within the call flow, continue if '1' is not selected",
                "EWT|PLAYEWT - Play estimated wait time",
                "PLACEINQUEUE|PLAYPIQ - Play place in queue",
                "NEXTSCRIPT|SCRIPT - Start custom script (PS Required)",
                "CUSTOMQUEUEEVENT|CUSTOM - Enter details provided by Optus PS",
                ]
    #Return list where we have ACTION|Explanation
    def GetMenuActions(self) -> list:
        return ["CHECKHOURS|CHECKHOO -Check attached hours of operation state",
                "PLAY|PLAY - Play message and continue",
                "MENU|MENU - Play menu and request a user response",
                "QUEUE|QUEUE - Queue call to a skill",
                "TRANSFER|XFER - call an external number",
                "VOICEMAILOPT|VOICEMAILOPT - Offer a voicemail within the call flow, continue if '1' is not selected",
                "VOICEMAIL|VOICEMAIL - Force call to voicemail and terminate call",
                "HANGUP|HANGUP - Play message, then terminate call",
                "CUSTOMQUEUEEVENT|CUSTOM - Execute custom action (PS required)",
                "NEXTSCRIPT|SCRIPT - Exit queue and apply custom actions (PS Required)",]

    def GetHooActions(self) -> list:
        return ["PLAY|PLAY - Play message and continue",
                "TRANSFER|XFER - call an external number",
                "VOICEMAIL|VOICEMAIL - Force call to voicemail and terminate call",
                "CALLBACK|CALLBACK - Offer callback to customer in queue",
                "HANGUP|HANGUP - Play message, then terminate call",
                "CUSTOMQUEUEEVENT|CUSTOM - Execute custom action (PS required)",
                "NEXTSCRIPT|SCRIPT - Exit queue and apply custom actions (PS Required)",]

    def GetActionParams(self,action : str  ) -> list :
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
                return ["Filename to play for menu|AUDIO_LOOKUP","Number of times to repeat the menu before naviagting to the fallback option (leave blank to keep repeating)|TEXT","Next step (0-9/Hash/Star)|TEXT","Suppress Error messages (true/false)|TEXT"]
            case "QUEUE":
                return ["Skill to queue call|SKILL_LOOKUP","Whisper on call answer (wav)|AUDIO_LOOKUP","Message to Pop|TEXT","Override Priority|TEXT","Override Routing|TEXT"]
            case "TRANSFER":
                return ["Filename to play before call transfer|AUDIO_LOOKUP","Number to transfer call to (E164)|TEXT"]
            case "CALLBACK":
                return ["Filename to play before callback|AUDIO_LOOKUP"]
            case "OFFERCAllBACK":
                return ["Filename to offer callback, (option 1 initiates callback)|AUDIO_LOOKUP"]
            case "VOICEMAIL":
                return ["Filename to play before voicemail|AUDIO_LOOKUP","Voicemail skill to submit call|SKILL_LOOKUP","Alternate email address to send VM|TEXT"]
            case "VOICEMAILOPT":
                return ["Filename to offer voicemail (option 1, default continues to next action)|AUDIO_LOOKUP","Voicemail skill to submit call|SKILL_LOOKUP","Alternate email address to send VM|TEXT"]
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

    #Define valid list of options for calid responses based on action type
    def GetActionResponsesForAction(self,action):
        if action == "CHECKHOURS":
            return ["Closed","Emergency","Meeting","Holiday","Weather","Other","Open" ]
        if action == "MENU":
            return  ["1","2","3","4","5","6","7","8","9","0","Star","Hash"]
        return None

    #true/false - return if the action ends the menu and begins queue
    def GetActionHasDefaultResponse(self,action):
        if action in [ "CHECKHOURS" , "PLAY" , "VOICEMAILOPT"]:
            return True
        #  QUEUE, TRANSFER,VOICEMAIL,HANGUP
        return False

    #Used in HTML build
    def GetPocList(self):
        return local.db.select("poc",["id","name"],{"project_id" : self.project_id })

    def GetHooList(self):
        return local.db.select("hoo",["id","name"],{"project_id" : self.project_id })

    def GetSkillList(self):
        return local.db.select("skill",["id","name"],{"project_id" : self.project_id })

    def GetUserWavList(self):
        return local.db.select("audio",["id","name"],{"project_id" : self.project_id , "isSystem" : False })

    def BuildItemParamList(self,request) -> dict:
        """Reads the active request and buils a list of parameters to add/update item in DB"""
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

    #def GetUserAudioList(self):
    #    return local.db.select("audio",["id","name","description","isSystem"],{"project_id" : self.project_id})

    def GetProject(self,project_id : int) -> dict :
        """Returns all DB project fields and values as as dictionary"""
        return local.db.select_first("project",["*"],{"user_id" : self.user_id, "id" : project_id})

    def GetProjectList(self) -> dict:
        """Returns list of all projects available to logged in user"""
        return local.db.select("project",["*"],{"user_id" : self.user_id})

    def GetUserList(self) -> dict:
        """Returns list of all users available to logged in user"""
        #TODO Add security here
        return local.db.select("user",["*"],{})

    def GetUser(self,user_id) -> dict:
        """Returns list of all users available to logged in user"""
        #TODO Add security here
        if user_id is None:
            return None
        return local.db.select("user",["*"],{"id" : user_id})[0]

    def IsAuthorisedPermission(self,auth_right : int) -> bool:
        """Returns true if the user is authorised to access the auth_right"""
        sql_query = f"SELECT name FROM user_role   INNER JOIN role_permission, permission ON role_permission.role_id  =  user_role.role_id AND permission.id = role_permission.permission_id  WHERE user_role.user_id = {self.user_id } AND permission.name = '{auth_right}'"
        results = local.db.select_query(sql_query)

        return len(results) > 0

    def db_get_list(self,list_type : str) -> list[dict]:
        """Read the application DB table and return all results as a list of dict
        param: list_type: The name of the table to query (using the current active project Id). """
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
        if item_type == "config":
            return local.db.select_first(item_type,["*"],{"key" : item_id})
        if item_type == "queueaction":
            return local.db.select_first(item_type,["*"],{"id" : item_id})
        if item_type == "callFlowAction":
            return local.db.select_first(item_type,["*"],{"id" : item_id})
        if item_type == "callFlowResponse":
            return local.db.select_first(item_type,["*"],{"id" : item_id})
        if item_id is None:
            return None
        return local.db.select_first(item_type,["*"],{"project_id" : self.project_id , "id" : item_id})

    def GetValue(self,item_type : str, lookup_field: str,lookup_value: str,return_field: str) -> object:
        """Read the DB table for item_type record and return the value expected"""
        if item_type is None or lookup_field is None or lookup_value is None or return_field is None or lookup_value == '':
            return ''
        return local.db.select_first(item_type,["*"],{"project_id" : self.project_id , lookup_field :lookup_value}).get(return_field,None) 

    #We cant have two routes to the same event so this cheats:
    def GetActionBreadcrumb(self,action_id : int) -> list:
        """Return a simple list so we can create a breadcrumb to the selected action"""
        def GetParent(breadcrumb_list, action_id : int) -> list:
            prior_action_id = local.db.select("callFlowResponse",["callFlowAction_id"],{ 'callFlowNextAction_id' : action_id})
            if len(prior_action_id) > 0 :
                prior_action = local.db.select("callFlowAction",["name","id"],{ 'id' : prior_action_id[0]['callFlowAction_id']})
                breadcrumb_list.insert(0,((prior_action[0]['name'] , prior_action[0]['id'],)))
                return GetParent(breadcrumb_list,prior_action_id[0]['callFlowAction_id'])
            else:
                return breadcrumb_list
        #Get parent and add to list
        breadcrumbs = []
        breadcrumbs = GetParent(breadcrumbs,action_id)
        #Get the response that lead to this action
        return breadcrumbs

    def ExportDnisSwitch(self) -> str:
        """Build the IVR menu's and entry points"""
        self.errors = []
        NEW_LINE = "\\r\\n"
        QUOTE = '\\"'
        TAB = "\\t"
        dnis_text = ""
        for call_flow in local.db.select("callFlow",["*"], {"project_id" : self.project_id}):
            logger.info("Parsing callflow %s", call_flow['id'])
            if call_flow['poc_list']:
                for poc in call_flow['poc_list'].split(','):
                    logger.info("Adding DNIS switch for POC %s" , poc)
                    poc_name = local.db.select_first("poc",["*"], {"project_id" : self.project_id , "id" : poc})
                    text += TAB + 'CASE '+ QUOTE + poc_name['name'] + QUOTE +  TAB + '//' + call_flow['name'] + NEW_LINE
            else:
                logger.info("Unable to add POC for call flow %s", call_flow['id'])
                self.errors.append(f"Unable to get POC for call flow {call_flow['name']}")
            dnis_text += TAB + '{' + NEW_LINE
            self.PruneCallFlow(call_flow['id'])
            #Create actions
            for action in local.db.select("callFlowAction","*",{"callFlow_id" : call_flow['id']}):
                dnis_text += TAB + 'AddOption('+ QUOTE +action['name'] + "," + action['action'] + ","
                #And get our params sorted here
                action_params = self.GetActionParams(action['action'])
                param_list = action['params'].split(",") if action['params'] is not None else []
                converted_params = ""
                for index,param in enumerate(action_params):
                    #Only perform this if there is a value in the param_list that we can use
                    if len(param_list) > index:
                        param_type = param.split("|")[1]
                        if param_type.endswith('LOOKUP'):
                            if param_type[:-7] ==  "AUDIO":
                                converted_param = str(self.GetValue(param_type[:-7],"id",param_list[index],"name"))
                            else:
                                converted_param = str(self.GetValue(param_type[:-7],"id",param_list[index],"external_id"))
                            if len(converted_param) < 1 or converted_param == 'None':
                                converted_param = ""
                            #    logger.debug("Error adding action %s - %s - %s " ,{action['id']} , {action['action']} , {action['name']} )
                            #    self.errors.append(f"Unable to locate parameter for action {action['action']} named {action['name']} - please ensure the action parameters have been syncronised")
                            converted_params += converted_param + ","
                        else:
                            if index >= len(param_list):
                                converted_params += ","
                            else:
                                converted_params += param_list[index] + ","

                # Add queue name to the end of the action line
                if action['action'] == "QUEUE":
                    dnis_text +=  converted_params + QUOTE + ')' + TAB + "//" + str(self.GetValue("SKILL","id",param_list[0],"name") + NEW_LINE)
                else:
                    dnis_text += converted_params + QUOTE + ')' + NEW_LINE
            dnis_text += NEW_LINE
            for response in local.db.select("callFlowResponse","*",{"callFlow_id" : call_flow['id']}):
                #Test for responses that havent been configured
                if response['callFlowNextAction_id'] is not None:
                    parent_name = local.db.select("callFlowAction","*",{"id" : response['callFlowAction_id']})[0]['name']
                    child_name = local.db.select("callFlowAction","*",{"id" : response['callFlowNextAction_id']})[0]['name']
                    dnis_text += TAB + 'AddResponse('+ QUOTE + parent_name + "," + response['response'] + "," +  child_name + QUOTE + ')' + NEW_LINE
                else:
                    logger.debug("Error adding response %s " ,{response['id']} )
                    self.errors.append(f"Some call flow responses are not terminated for response ID: {response['id ']}")

            dnis_text += NEW_LINE

            dnis_text += TAB + '}' + NEW_LINE
            #hooProfile and HooActions embedded in menu - not needed
        return dnis_text

    def ExportQueueSwitch(self) -> str:
        """Build the text to define all active queue data, to upload to CXone"""
        self.errors = []
        queue_text = ""
        NEW_LINE = "\\r\\n"
        QUOTE = '\\"'
        TAB = "\\t"
        queues = local.db.select("queue",["*"], {"project_id" : self.project_id})
        for queue in queues:
            for skill_id in queue['skills'].split(','):
                skill = local.db.select('skill',['external_id', 'name'],{ 'id': skill_id})
                queue_text += TAB + 'CASE ' +QUOTE + str(skill[0]['external_id']) + QUOTE + TAB +  '//' + skill[0]['name'] + NEW_LINE

            queue_text += TAB + '{' + NEW_LINE

            #Queue HOO config
            if queue['queuehoo'] is None:
                logger.debug("Error locating HOO for queue %s " ,{queue['id']})
                self.errors.append("Unable to locate HOO for queue")
            else:
                queue_hoo_external_id = local.db.select('hoo',['external_id'],{ 'id': str(queue['queuehoo'])})
                queue_text += TAB + 'ASSIGN global:hooProfile = ' + QUOTE + str(queue_hoo_external_id[0]['external_id']) + QUOTE + NEW_LINE

                #Add pre-queue and queue hoo action - these were added verbatim
                if queue['prequeehooactions'] is not None:
                    for action in queue['prequeehooactions'].split('|'):
                        queue_text += TAB + 'AddPreQueueHooAction(' + QUOTE + action + QUOTE + ')' + NEW_LINE
                if queue['queehooactions'] is not None:
                    for action in queue['queehooactions'].split('|'):
                        queue_text += TAB + 'AddQueueHooAction(' + QUOTE + action + QUOTE + ')' + NEW_LINE

            #Add queue actions
            queue_actions = local.db.select("queueAction","*", { 'queue_id' : queue['id'] })
            for action in queue_actions:
                queue_text += TAB + 'AddQueueAction(' + QUOTE +action['action'] + ':'  +str(action['param1']) + QUOTE + ')'+ NEW_LINE

            queue_text += TAB + '}' + NEW_LINE
        return queue_text

    def PruneCallFlow(self,call_flow_id : int) -> bool:
        """Remove all unlinked actions and responses for a call flow"""
        callflow_root = local.db.select_first("callFlow",['callFlowAction_id'],{"id" : call_flow_id}).get('callFlowAction_id',None)
        logger.debug("Pruning call flow %s",call_flow_id)
        if callflow_root is not None:
            #Get all actions and responses
            actions = local.db.select("callFlowAction",["id",],{"callFlow_id" : call_flow_id})
            logger.info("Actions counted %s" , len(actions))
            responses = local.db.select("callFlowResponse",["id","callFlowAction_id","callFlowNextAction_id"],{"callFlow_id" : call_flow_id})
            logger.info("Responses counted %s" , len(responses))
            #Get all the linked actions
            linked_actions = [x['callFlowNextAction_id'] for x in responses]
            linked_actions.append(callflow_root)
            linked_actions = list(set(linked_actions))
            logger.info("Linked actions %s" ,repr(linked_actions))
            #Delete all unlinked actions
            for action in actions:
                if action['id'] not in linked_actions:
                    logger.info("Removing action %s" ,  action['id'])
                    local.db.delete("callFlowAction",{"id" : action['id']})

            #Delete all unlinked responses
            for response in responses:
                if response['callFlowAction_id'] not in linked_actions:
                    logger.info("Removing action %s" ,  response['id'])
                    local.db.delete("callFlowResponse",{"id" : response['id']})
            return True
        else:
            logger.info("No actions in call flow")
            #TODO there may be nested or multiple levels of orphans - repeat until no deletions
        return True

    def BuildParamList(self, action_type :str, params :list) -> str:
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

    def AddNewIfNone(self, item_type :str, item_name : str, item_value : str) -> bool:
        """Quickly add WAV/SKILL/HOO with name and description
        RETURNS True if created, False if existing"""
        item_type = item_type.upper()
        if item_type == "AUDIO":
            existing = local.db.select("audio",["id"],{"project_id" : self.project_id , "name" : item_name })
            if len(existing) > 0:
                return False
            else:
                local.db.insert("audio",{ "name" : item_name , "description" : item_value , "project_id" : self.project_id , "localSize" : 0 })
                return True
        if item_type == "HOO":
            existing = local.db.select("hoo",["id","name"],{"project_id" : self.project_id , "name" : item_name })
            if len(existing) > 0:
                return False
            else:
                local.db.insert("hoo",{ "name"  : item_name , "description" : item_value , "project_id" : self.project_id })
                return True
        if item_type == "SKILL":
            existing = local.db.select("skill",["id","name"],{"project_id" : self.project_id , "name" : item_name })
            if len(existing) > 0:
                return False
            else:
                local.db.insert("skill",{ "name" : item_name , "description" : item_value , "project_id" : self.project_id })
                return True
        if item_type == "POC":
            existing = local.db.select("poc",["id"],{"project_id" : self.project_id , "name" : item_name })
            if len(existing) > 0:
                return False
            else:
                local.db.insert("poc",{ "name" : item_name , "description" : item_value , "project_id" : self.project_id })
                return True
        #We dont know what to do
        logger.info("Error identifying item type")
        return False

    def AddNewIfNoneEx(self, item_type : str, item_lookup_field : str ,field_list : dict) -> int:
        """Insert/Update item \n
        Note this does not work on tables with no project ID at this time \n
        :param: item_type - name of table
        :param: item_lookup_field - name of field we are looking for existing item
        :param: field list - dictionary of field name/value kvp 
        
        :returns: Negative item table ID  if new item, item table ID if existing item"""
        item_type = item_type.upper()
        existing = local.db.select_first(item_type,["id"],
                                        {"project_id" : self.project_id , item_lookup_field : field_list[item_lookup_field] })
        if existing is None or len(existing) == 0:
            field_list['project_id'] = self.project_id
            return -local.db.insert(item_type ,field_list)
        return existing['id']

    def AddNewIfNoneAdmin(self, item_type : str, item_lookup_field,field_list : dict) -> int:
        """Quickly add AUDIO/SKILL/HOO
        RETURNS True if created, False if existing"""
        item_type = item_type.upper()
        existing = local.db.select_first(item_type,["id"], {item_lookup_field : field_list[item_lookup_field] })
        if len(existing) == 0:
            return -local.db.insert(item_type ,field_list)
        return existing['id']

    def delete(self, item_type : str, item_id : int) -> bool:
        """Delete item from the DB"""
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

    def update(self, item_type : str, item_id : int, field_list : dict) -> bool:
        """Update item in the DB"""
        if item_type == "queueaction":
            local.db.update(item_type,field_list,{"id" : item_id})
            return True
        if item_type == "callFlowAction":
            local.db.update(item_type,field_list,{"id" : item_id})
            return True
        if item_type == "callFlowResponse":
            local.db.update(item_type,field_list,{"id" : item_id})
            return True
        if item_id is None:
            return False
        return local.db.update(item_type,field_list,{"project_id" : self.project_id , "id" : item_id})

    def IsValidated( self, package_element :str ) -> bool:
        return local.db.IsValidPackageElement(package_element, self.project_id)

    def ValidateConnection(self) -> bool:
        project = local.db.select_first("project","*",{"id" : self.project_id })

        self.__key  = project['user_key']
        self.__secret = project['user_secret']
        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                business_unit = self.__connection.GetBusinessUnit()
                self.connected_bu_name = business_unit['businessUnitName']
                self.connected_bu_id = business_unit['businessUnitId']
                local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "connection", "description" : "Connected successfully to business unit","success_state" : True })
                return True
        finally:
            pass
        local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "connection", "description" : "Failed to connect to business unit","success_state" : False })
        return False

    def ValidatePackage(self) -> bool:

        errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']

        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                local_files = []
                remote_files = set(self.__connection.GetScriptsList())
                local_root = ".//packages//" +project['deployment_type'].lower()+ "//scripts//"
                remote_root = project['instance_name'] + ( "\\" if len(project['instance_name']) >0 else "" )
                for path, subdirs, files in os.walk(local_root):
                    for name in files:
                        local_files.append(os.path.join(path[len(local_root):], name))
                        logger.info(os.path.join(path[len(local_root):], name))
                for filename in local_files:
                    if remote_root + filename[:-5] in remote_files:
                        errors.append(f"File found in destination path: {filename}" )
                    else:
                        logger.info("Remote file not found (valid): %s" , filename)
                if not errors:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "script", "description" : "Identified files at project darget destination","success_state" : True })
                    return True
                else:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "script", "description" : "Identified files at project darget destination","success_state" : False })
                    self.errors = errors
                    return False
        finally:
            pass
        return False

    def ValidateAudio(self) -> bool:
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
                remote_files = self.__connection.GetAudioList(remote_root)
                for filename in remote_files:
                    if(filename['fileNameWithPath'][:-4] in local_files) and (filename['isFolder'] is False):
                        errors.append(f"File found in destination: {filename['fileNameWithPath']}" )
                    else:
                        logger.info("Remote file not found in source files (valid): %s ", filename['fileNameWithPath'])
                if not errors:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "audio", "description" : "No existing files in destination path","success_state" : True })
                    return True
                else:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "audio", "description" : "Identified audio at project darget destination","success_state" : True })
                    errors.append("If you select DEPLOY all files that have been modified will be overwritten" )
                    self.errors = errors
                    return False
        finally:
            pass

        return False

    def ValidateSkillsConfig(self) -> bool:
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
                remote_skills = self.__connection.GetSkillList()
                for remote_skill in remote_skills:
                    for skill in local_skills:
                        if skill['name'] == remote_skill["skillName"]:
                            if skill['external_id'] !='':
                                errors.append(f"Skill name and external ID located: {skill['name']}" )
                            else:
                                errors.append(f"Skill name located (sync to update external ID): {skill['name']}" )
                        else:
                            pass
                            #logger.info(f"Local skill not found at destination (valid): {skill['Name']}")
                if not errors:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "skill", "description" : "Skills list validated with no overlap","success_state" : True })
                    return True
                else:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "skill", "description" : "Skill names overlap","success_state" : True })
                    self.errors = errors
                    return False
        finally:
            pass
        return False

    def ValidateHooConfig(self) -> bool:
        """Load skills from BU and determine if there are issues"""
        errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']

        #Read current HOO
        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                local_hoo = local.db.select("hoo",["*"],{"project_id" : self.project_id })
                remote_hoos = self.__connection.GetHooList()
                for remote_hoo in remote_hoos:
                    for hoo in local_hoo:
                        if hoo['name'] == remote_hoo["hoursOfOperationProfileName"]:
                            if hoo['external_id'] =='':
                                errors.append(f"HOO found in BU - system HOO ID updated: {hoo['Name']}" )
                        else:
                            pass
                            #logger.info(f"Local skill not found at destination (valid): {skill['Name']}")
                if not errors:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "hoo", "description" : "HOO list validated with no overlap","success_state" : True })
                    return True
                else:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "hoo", "description" : "HOO names overlap","success_state" : False })
                    self.errors = errors
                    return False
        finally:
            pass
        return False

    def UploadPackage(self) -> bool:
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
                        local_files.append(os.path.join(path[len(local_root):], name))
                for local_filename in local_files:
                    self.__connection.CreateScript(local_root, local_filename, remote_root_path)
                if not errors:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "upload", "action_object" : "script", "description" : "Files Uploaded","success_state" : True })
                    return True
                else:
                    local.db.insert("deployment",{"project_id" :project['id'] , "action" : "upload", "action_object" : "script", "description" : "Error uploading files","success_state" : False })
                    return False
        finally:
            pass
        return False

    def UploadAudioPackage(self) -> bool:
        self.errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']

        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                file_actions = []
                remote_root = project['instance_name'] + "/prompts/"
                file_actions =  [{**file, 'remote_path_file'.replace('\\', '/') : remote_root + file['name'] + '.wav', "local_file_path" : "./users/" + str(self.project_id) } for file in local.db.select("audio",['name','description','isSynced','id'],{"project_id" : self.project_id })]

                #tts set-up
                sub_key = local.db.get_setting("tts_key")
                voice_font = "en-AU-NatashaNeural"
                tts = local.tts.Speech(sub_key)

                #And upload
                for file in file_actions:
                    if file['isSynced'] != 1:
                        audio_response = tts.get_audio(file['description'], voice_font)
                        result = self.__connection.UploadItem(file['remote_path_file'].replace("\\","/"),audio_response)
                        if result == 200:
                            local.db.update("audio",{"isSynced" : True } , {"project_id" : self.project_id , "id" : file['id']})
                
                local.db.insert("deployment",{"project_id" :project['id'] , "action" : "deploy", "action_object" : "audio", "description" : "Uploaded audio files","success_state" : True })
                return True
        finally:
            pass

        return False

    def UploadHoo(self) -> bool:
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
                        external_id = self.__connection.CreateHoo(hoo['name'])
                        local.db.update("hoo",{'external_id': external_id },{"project_id" : self.project_id , "id" : hoo['id'] })

                local.db.insert("deployment",{"project_id" :project['id'] , "action" : "deploy", "action_object" : "hoo", "description" : "Uploaded HOO to BU","success_state" : True })
        finally:
            pass
        return False

    def UploadSkills(self) -> bool:
        self.errors = []
        project = local.db.select_first("project","*",{"id" : self.project_id })
        self.__key  = project['user_key']
        self.__secret = project['user_secret']
        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if self.__connection.is_connected():
                internal_skills =local.db.select("skill",["*"],{"project_id" : self.project_id})

                camapign_list = self.__connection.GetCampaignList()
                default_campaign_id = 0
                for campaign in camapign_list:
                    if campaign['campaignName'] == "Default":
                        default_campaign_id = campaign['campaignId']
                        break
                if default_campaign_id == 0:
                    default_campaign_id = self.__connection.CreateCampaign("Default")

                for skill in internal_skills:
                    if skill['external_id'] is None:
                        external_id = self.__connection.CreateSkill(skill['name'],skill['skill_type'], default_campaign_id)
                        if external_id is not None:
                            local.db.update("skill",{'external_id': external_id },{"project_id" : self.project_id , "id" : skill['id'] })
                        else:
                            self.errors.append(f"Unable to upload {skill['name']} - name must contain at least two characters and a maximum of thirty, and may only contain letters, numbers and the special characters ( . - _ : )") 
                local.db.insert("deployment",{"project_id" :project['id'] , "action" : "deploy", "action_object" : "skill", "description" : "Updated skills in BU","success_state" : True })
                return True
        finally:
            pass
        return False
