##################################################################################################################
#
#   Description:    Provides a way to unify html/jinja/python with common code and data structures
#                   Helper used in web pages for dynamic content
#  
##################################################################################################################
import local.db

class DataModel(object):
    
    user_id = None
    project_id =  None

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
        return ["CHECKHOURS|Check hours of operation",
                "PLAY|Play message",
                "MENU|Play menu and request a user response",
                "QUEUE|Exit CallFlow and queue to a skill",
                "TRANSFER|Transfer to a external number",
                "VOICEMAILOPT|Offer a voicemail within the call flow",
                "VOICEMAIL|Force call to voicemail within the call flow",
                "HANGUP|Hang up the call",
                "NEXTSCRIPT|Complete menu and use a custom script (PS required)",
                "CUSTOMEVENT|Execute custom action (PS required)",]
    
    #Get list of paramter descriptions and inout type for html rendering
    def GetActionParams(self,action):
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
                return ["Filename to play for menu|WAV_LOOKUP","Number of times to repeat the menu before naviagting to the fallback option (leave blank to keep repeating)|TEXT","Next step (0-9/Hash/Star)|TEXT","Play error messages on mis-keyed input|TEXT"]
            case "QUEUE":
                return ["Skill to queue call|SKILL_LOOKUP"]
            case "TRANSFER":
                return ["Filename to play before call transfer|WAV_LOOKUP","Number to transfer call to (E164)|TEXT"]
            case "CALLBACK":
                return ["Filename to play before callback|WAV_LOOKUP"]
            case "OFFERCAllBACK":
                return ["Filename to offer callback, (option 1 initiates callback)|WAV_LOOKUP"]
            case "VOICEMAIL":
                return ["Filename to play before voicemail|WAV_LOOKUP"]
            case "VOICEMAILOPT":
                return ["Filename to offer voicemail (option 1, default continues to next action)|WAV_LOOKUP"]
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
    def GetActionBreadcrumb(self,callflow_id,action_id : int) -> list:
        #def GetParent(action_id):
        #    prior_action_id = local.db.Select("callFlowResponse",["callFlowAction_id"],{ 'callFlowNextAction_id' : action_id})
        #    if prior_action_id is not None:
        #        prior_action_name = local.db.Select("callFlowAction",["name"],{ 'id' : prior_action_id})
        #        return GetParent(action_id) + prior_action_name + "|" + prior_action_id
        #    else:
        #        return None
        
        #Get parent and add to list
        breadcrumbs = []
        
        #Get the response that lead to this action
        return None

    def ExportDnisSwith(self) -> str:
        sp = 8
        dnis_text = ""
        dnis = local.db.Select("callFlow",["*"], {"project_id" : self.project_id})
        for entry_point in dnis:
            for poc in dnis['poc_list'].split(','):
                pass
                #skill_external_id = local.db.Select('skill',['external_id'],{ 'id': skill})
                #queue_text += (' '*sp) + 'CASE "' + str(skill_external_id[0]['external_id']) +'"\n'
            #Set Hoo
            dnis_text += (' '*sp) + '{\n'
            #queue_hoo_external_id = local.db.Select('hoo',['external_id'],{ 'id': str(queue['queuehoo'])})
            #queue_text += (' '*sp) + f'ASSIGN global:hooProfile = "{str(queue_hoo_external_id[0]['external_id'])}"\n'
            dnis_text += (' '*sp) + '}\n'
            
        return dnis_text
    
    def ExportQueueSwitch(self) -> str:
        sp = 8
        queue_text = ""
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
        comma_separated_string = ""
        for item in params:
            if item is None:
                comma_separated_string += ','
            else:
                comma_separated_string += item + ','
        comma_separated_string = comma_separated_string.rstrip(',')
        return comma_separated_string