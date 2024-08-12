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
    
    #TODO:: This does nothing ATM
    def GetMenuActions(self):
        #  CHECKHOURS,Check hours of operation
        #  PLAY,Play message
        #  MENU,Play menu and request a user response
        #  QUEUE,Exit CallFlow and queue to a skill
        #  TRANSFER,Transfer to a external number
        #  VOICEMAILOPT,Offer a voicemail within the CallFlow
        #  VOICEMAIL,Force call to voicemail within the CallFlow
        #  HANGUP,Hang up the call
        return 
    
    #Get list of paramter descriptions and inout type for html rendering
    def GetActionParams(self,action):
        match action:
            case "CHECKHOURS":
                return ["Select Hours of operation to check|<HOOLOOKUP>"]
            case "PLAY":
                return ["Filename to play|<WAVLOOKUP>"]
            case "MENU":
                return ["Filename to play for menu|<WAVLOOKUP>"]
            case "QUEUE":
                return ["Skill to Queue call|<SKILLLOOKUP>"]
            case "TRANSFER":
                return ["Filenmae to play before transfer|<WAVLOOKUP>","Number to transfer call to (E164)|<TEXT>"]
            case "VOICEMAIL":
                return ["Fiilenmae to play before voicemail|<WAVLOOKUP>"]
            case "VOICEMAILOPT":
                return ["Filenmae to offer voicemail (option 1)|<WAVLOOKUP>"]
            case "HANGUP":
                return ["Fiilenmae to play before hangup|<WAVLOOKUP>"]
            case _:
                return ["Custom Action Parameters - see Optus for details:","<TEXT>"]
     
    #Define valid list of options for calid responses based on action type 
    def GetActionResponsesForAction(self,action):
        if action == "CHECKHOURS":
            return ["Closed","Emergency","Meeting","Holiday","Weather","Other","Open" ]
        if action == "MENU":
            return  ["1","2","3","4","5","6","7","8","9","0","Star","Hash"]
        if action == "VOICEMAILOPT":
            return  ["1"]
        return None
   
    #true/false - return if the action ends the menu and begins queue
    def GetActionHasDefaultResponse(self,action):
        if action in [ "CHECKHOURS" , "PLAY" , "MENU" , "VOICEMAILOPT"]:
            return True
        #  QUEUE, TRANSFER,VOICEMAIL,HANGUP
        return False   

    #Used in HTML build
    def GetHooList(self):
        return local.db.Select("hoo",["id","name"],{"project_id" : self.project_id })
        
    def GetSkillList(self):
        return local.db.Select("skill",["id","name"],{"project_id" : self.project_id })
    
    def GetUserWavList(self):
        return local.db.Select("audio",["id","filename"],{"project_id" : self.project_id , "isSystem" : False }) 