##################################################################################################################
#
#   Description:    Provides a way to unify html/jinja/python with common code and data structures
#                   Helper used in web pages for dynamic content
#  
##################################################################################################################
import os

import local.db
import local.cxone

class DataModel(object):
    
    __key  = None
    __secret = None
    __api_connection = None
        
    user_id = None
    project_id =  None
    connected_bu_name = None
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
    
    #Return list where we have ACTION|Explanation
    def GetMenuActions(self) -> list:
        return ["CHECKHOURS|Check attached hours of operation state",
                "PLAY|Play WAV message and continue",
                "MENU|Play MENU and request a user response",
                "QUEUE|Queue call to a skill",
                "TRANSFER|Transfer call to an external number",
                "VOICEMAILOPT|Offer a voicemail within the call flow",
                "VOICEMAIL|Force call to voicemail and terminate call",
                "HANGUP|Play WAV message, then terminate call",
                "NEXTSCRIPT|Complete menu and use a custom script (PS required)",
                "CUSTOMEVENT|Execute custom action (PS required)",]
    
    #Get list of paramter descriptions and inout type for html rendering
    def GetActionParams(self,action : str  ) -> list :
        match action:
            case "CHECKHOURS":
                return ["Select Hours of operation to check|HOO_LOOKUP"]
            case "PLAY":
                return ["Filename to play|WAV_LOOKUP"]
            case "PLAYMUSIC":
                return ["Duration to play hold music|TEXT"]
            case "PLAYMUSICEX":
                return ["Filename to play for menu|WAV_LOOKUP","Start offset to play within file|TEXT","Duration to play|TEXT",]
            case "MENU":
                return ["Filename to play for menu|WAV_LOOKUP","Number of times to repeat the menu before naviagting to the fallback option (leave blank to keep repeating)|TEXT","Next step (0-9/Hash/Star)|TEXT","Play error messages on mis-keyed input (true/false)|TEXT"]
            case "QUEUE":
                return ["Skill to queue call|SKILL_LOOKUP"]
            case "TRANSFER":
                return ["Filename to play before call transfer|WAV_LOOKUP","Number to transfer call to (E164)|TEXT"]
            case "CALLBACK":
                return ["Filename to play before callback|WAV_LOOKUP"]
            case "OFFERCAllBACK":
                return ["Filename to offer callback, (option 1 initiates callback)|WAV_LOOKUP"]
            case "VOICEMAIL":
                return ["Filename to play before voicemail|WAV_LOOKUP","Voicemail skill to submit call|SKILL_LOOKUP","Alternate email address to send VM|TEXT"]
            case "VOICEMAILOPT":
                return ["Filename to offer voicemail (option 1, default continues to next action)|WAV_LOOKUP,Voicemail skill to submit call|SKILL_LOOKUP,Alternate email address to send VM|TEXT"]
            case "HANGUP":
                return ["Filename to play before hangup|WAV_LOOKUP"]
            case "NEXTSCRIPT":
                return ["Parameters provided by professional services (custom script name)|TEXT"]
            case "CUSTOMEVENT":
                return ["Parameters provided by professional services|TEXT"]
            #Specific to Queue and not common actions
            case "CUSTOMQUEUEEVENT":
                 return ["Parameters provided by professional services|TEXT"]
            case "PLACEINQUEUE":
                 return ["File to play 'You are currently...'|WAV_LOOKUP","File to play '...in the queue'|WAV_LOOKUP"]
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
        return local.db.Select("poc",["id","name"],{"project_id" : self.project_id })
    
    def GetHooList(self):
        return local.db.Select("hoo",["id","name"],{"project_id" : self.project_id })
        
    def GetSkillList(self):
        return local.db.Select("skill",["id","name"],{"project_id" : self.project_id })
    
    def GetUserWavList(self):
        return local.db.Select("audio",["id","filename"],{"project_id" : self.project_id , "isSystem" : False }) 
    
    #We cant have two routes to the same event so this cheats:
    def GetActionBreadcrumb(self,action_id : int) -> list:
        #Is this how we do private subs....?
        def GetParent(breadcrumb_list, action_id) -> list:
            prior_action_id = local.db.Select("callFlowResponse",["callFlowAction_id"],{ 'callFlowNextAction_id' : action_id})
            if len(prior_action_id) > 0 :
                prior_action = local.db.Select("callFlowAction",["name","id"],{ 'id' : prior_action_id[0]['callFlowAction_id']})
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
        errors = []
        sp = 4
        dnis_text = ""
        for call_flow in local.db.Select("callFlow",["*"], {"project_id" : self.project_id}):
            for poc in call_flow['poc_list'].split(','):
                poc_name = local.db.Select("poc",["*"], {"project_id" : self.project_id , "id" : poc,})
                dnis_text += (' '*sp) + 'CASE "' + poc_name[0]['name'] + '"\n'

            dnis_text += (' '*sp) + '{\n'
            #Create actions
            for action in local.db.Select("callFlowAction","*",{"callFlow_id" : poc_name[0]['id']}):
                dnis_text += ('  '*sp) + 'AddMenuAction("' +action['name'] + "," + action['action'] + "," +  action['params'] + '")\n'
            dnis_text += '\n'
            for response in local.db.Select("callFlowResponse","*",{"callFlow_id" : poc_name[0]['id']}):
                #Test for responses that havent been configured
                if response['callFlowNextAction_id'] != None:
                    parent_name = local.db.Select("callFlowAction","*",{"id" : response['callFlowAction_id']})[0]['name']
                    child_name = local.db.Select("callFlowAction","*",{"id" : response['callFlowNextAction_id']})[0]['name'] 
                    dnis_text += ('  '*sp) + 'AddMenuRespnse("' + parent_name + "," + response['response'] + "," +  child_name + '")\n'
                else:
                   errors.append(f"Some call flow responses are not terminated for{parent_name}") 
            
            dnis_text += '\n'

            dnis_text += (' '*sp) + '}\n'
            #hooProfile and HooActions embedded in menu - not needed
        return dnis_text
    
    def ExportQueueSwitch(self) -> str:
        sp = 8
        queue_text = ""
        errors = []
        queues = local.db.Select("queue",["*"], {"project_id" : self.project_id})
        for queue in queues:
            for skill in queue['skills'].split(','):
                skill_external_id = local.db.Select('skill',['external_id'],{ 'id': skill})
                queue_text += (' '*sp) + 'CASE "' + str(skill_external_id[0]['external_id']) +'"\n'
            #Set Hoo
            queue_text += (' '*sp) + '{\n'
            queue_hoo_external_id = local.db.Select('hoo',['external_id'],{ 'id': str(queue['queuehoo'])})
            queue_text += (' '*sp) + f'ASSIGN global:hooProfile = "{str(queue_hoo_external_id[0]['external_id'])}"\n'
            
            #Add queue actions
            queue_actions = local.db.Select("queueAction","*",{})
            for action in queue_actions:
                queue_text += (' '*sp) + 'AddQueueAction("'+action['action'] + ':'  +str(action['param1']) + '")\n'

            #Add pre-queue and queue hoo action - these were added verbatim
            queue_text += (' '*sp) + 'AddPreQueueHooAction("' +  queue['prequeehooactions']+ '")\n'
            queue_text += (' '*sp) + 'AddQueueHooAction("'  +  queue['queehooactions']+ '")\n'
            queue_text += (' '*sp) + '}\n'
        return queue_text

    #Converts list of clear text parameters (e.g Hoo1/Skill1) to the equivalent parameters with internal ID's
    #Creates skill/hoo/wav if this does NOT exist
    def BuildParamList(self, action_type :str, params :list) -> str:
        #Some params may need lookup based on action_type - not currently used
        #action_type
        comma_separated_string = ""
        for item in params:
            if item is None:
                comma_separated_string += ','
            else:
                comma_separated_string += item + ','
        comma_separated_string = comma_separated_string.rstrip(',')
        return comma_separated_string
    
    def AddNewIfNone(self, item_type :str, item_name : str, item_value : str):
        if item_type == "WAV":
            existing = local.db.Select("audio",["id","filename"],{"project_id" : self.project_id , "filename" : item_name })
            if len(existing) > 0:
                return
            else:
                 local.db.Insert("audio",{ "filename" : item_name , "wording" : item_value , "project_id" : self.project_id , "localSize" : 0 })
        
        #We dont know what to do
        print("Error identifying item type")
        return
    
    def ValidateConnection(self) -> bool:
        project = local.db.SelectFirst("project","*",{"id" : self.project_id })

        self.__key  = project['userkey']
        self.__secret = project['usersecret']
        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if (self.__connection.Connect()):
                businessUnit = self.__connection.GetBusinessUnit()
                self.connected_bu_name = businessUnit['businessUnitName']
                local.db.Insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "connection", "description" : "Connected successfully to business unit","success_state" : True })
                return True
        finally:
            pass
        local.db.Insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "connection", "description" : "Failed to connect to business unit","success_state" : False })
        return False

    def IsValidated( self, package_element :str ) -> bool:
        return local.db.IsValidPackageElement(package_element, self.project_id)
    
    def ValidatePackage(self) -> bool:
        errors = []
        project = local.db.SelectFirst("project","*",{"id" : self.project_id })
        self.__key  = project['userkey']
        self.__secret = project['usersecret']

        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if (self.__connection.Connect()):
                local_files = []
                remote_files = set(self.__connection.GetScriptsList())
                local_root = ".//packages//" +project['deploymenttype'].lower()+ "//scripts//"
                for path, subdirs, files in os.walk(local_root):
                    for name in files:
                        local_files.append(os.path.join(path, name))
                        print(os.path.join(path, name))
                for filename in local_files:
                    if((filename.replace("\\","\\\\"))[len(local_root):][:-5] in remote_files):
                        errors.append(f"File found in destination path: {filename}" )
                    else:
                        print(f"Remote file not found (valid): {filename.replace("\\","\\\\")[len(local_root):][:-5]}")
                if errors == []:
                    local.db.Insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "script", "description" : "Identified files at project darget destination","success_state" : True })
                    return True
                else:
                    local.db.Insert("deployment",{"project_id" :project['id'] , "action" : "validate", "action_object" : "script", "description" : "Identified files at project darget destination","success_state" : False })
                    return False
        finally:
            pass
        return False
    
    def UploadPackage(self) -> bool:
        errors = []
        project = local.db.SelectFirst("project","*",{"id" : self.project_id })
        self.__key  = project['userkey']
        self.__secret = project['usersecret']

        try:
            self.__connection = local.cxone.CxOne(self.__key,self.__secret)
            if (self.__connection.Connect()):
                local_root = ".//packages//" +project['deploymenttype'].lower()+ "//scripts//"
                local_files = []
                for path, subdirs, files in os.walk(local_root):
                    for name in files:
                        local_files.append(os.path.join(path, name))
                        if path != local_root:
                            remote_path =  project['instancename'] + "\\\\" + path[len(local_root):]
                        else:
                            remote_path = project['instancename']
                        upload_result = self.__connection.CreateScript(name, path, remote_path)
                if errors == []:
                    local.db.Insert("deployment",{"project_id" :project['id'] , "action" : "upload", "action_object" : "script", "description" : "Files Uploaded","success_state" : True })
                    return True
                else:
                    local.db.Insert("deployment",{"project_id" :project['id'] , "action" : "upload", "action_object" : "script", "description" : "Error uploading files","success_state" : False })
                    return False
        finally:
            pass
        return False
    
        