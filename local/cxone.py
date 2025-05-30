"""This module provides an simple TCP object to commcommunicate  with CX One REST API
   Tested API version : V30
"""
import os
import base64
import json
import requests
#, time, config, json
from local import logger

class CxOne(object):
    """Provides access to CXone API"""
    __ACCESS_URI = 'https://au1.nice-incontact.com/authentication/v1/token/access-key'
    __SERVICES_URI = 'https://api-au1.niceincontact.com/incontactapi/services/v30.0/'
    #_token_url = 'https://cxone.niceincontact.com/auth/token'
    __access_token:str = None
    __client_key:str = None
    __client_secret:str = None
    business_unit:str = None

    def __init__(self, client_key : str, client_secret : str ):
        """Initialise and get the token"""
        self.__client_key = client_key
        self.__client_secret = client_secret
        self.__get_token()

    def __get_token(self):
        """Get our bearer token"""
        logger.debug('>> __get_token')
        body = {
            'accessKeyId': self.__client_key,
            'accessKeySecret': self.__client_secret
        }
        try:
            response = requests.post(self.__ACCESS_URI, json=body, timeout=30)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.info("Error getting token: %s",e)
            return None

        self.__access_token = response.json().get('access_token')
        if self.__access_token is None:
            logger.info('Failed to get token')
            return None
        self.business_unit = self.get_business_unit()
        return self.__access_token

    def __get_response(self,service_endpoint :str , params: dict = None,) -> requests.Response:
        """HTTP Request GET with default headers and customisable params"""
        logger.debug("Getting service endpoint / %s", service_endpoint)
        constructed_url = self.__SERVICES_URI + service_endpoint
        headers = {
            'Authorization': 'Bearer ' + self.__access_token,
            'User-Agent': 'WebApp-development',
        }
        try:
            response = requests.get(constructed_url, headers=headers, params = params, data = None, timeout=30000)
            #response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.info("Error getting response: %s" , e)
            return None
        return response

    def __post_response(self,service_endpoint:str,params :dict  , data : dict = None) -> requests.Response:
        """HTTP Post with default headers and customisable params"""
        logger.debug("Posting to service endpoint / %s ", service_endpoint)
        constructed_url = self.__SERVICES_URI + service_endpoint
        headers = {
            'Authorization': 'Bearer ' + self.__access_token,
            'User-Agent': 'WebApp-development',
        }
        try:
            response = requests.post(constructed_url, headers=headers, data=data, params=params, timeout=30)
            #response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.info("Error posting response: %s", e)
            return None
        return response

    def __put_response(self, service_endpoint : str, params : dict , data : dict = None) -> requests.Response:
        """HTTP Put with default headers and customizable params"""
        logger.debug(">> __put_response to service endpoint / %s" , service_endpoint)
        constructed_url = self.__SERVICES_URI + service_endpoint
        headers = {
            'Authorization': 'Bearer ' + self.__access_token,
            'User-Agent': 'WebApp-development',
        }
        try:
            response = requests.put(constructed_url, headers=headers, data=data, params=params, timeout=30)
            #response.raise_for_status()
        except requests.exceptions.RequestException as e:
            logger.info("Error putting response: %s", e)
            return None
        return response

    def is_connected(self) -> bool:
        """Return true if we have a token"""
        return self.__access_token is not None

    #Return the BU info
    def get_business_unit(self):
        response = self.__get_response('business-unit')
        business_units = response.json().get('businessUnits')
        return next(iter(business_units), None)

    #Impersonatated admin ID
    def get_impersonated_admin(self) -> int:
        response = self.__get_response('agents')
        agents = response.json().get('agents')
        for agent in agents:
            if agent['firstName'] == "Impersonated" and agent['lastName'] == "Admin":
                return agent['agentId']
        return None

    def get_audio_list(self, root_path = None):
        response = self.__get_response('folders' ,{ 'folderName' :  root_path })
        if response.status_code != 200:
            return []
        else:
            return response.json().get('files',[])

    def get_poc_list(self):
        ##Get all available phone numbers
        response = self.__get_response('phone-numbers')
        if response.status_code != 204:
            phone_numbers = response.json().get('phoneNumbers')
            logger.info("Found phone numbers %s ", (len(phone_numbers) or '0'))
        else:
            phone_numbers = []

        ##Now get all active POC as we need to remove these number from our list/define them more accurately
        response = self.__get_response('points-of-contact')
        points_of_contact = response.json().get('pointsOfContact')
        logger.info("Found poc numbers %s", (response.json().get('totalRecords') or '0'))

        #Fields we need contactAddress, isActive, script_name
        #We need to be sure it is "media_typeId": 4, "outboundSkill": false,
        consolidated_list = dict()
        #For all phone numbers
        for number in phone_numbers:
            #logger.info(number)
            consolidated_list[number] = ('-1','','Available POC')

        #Add all POC
        for poc in points_of_contact:
            #logger.info(poc['contactAddress'])
            #logger.info(poc['contactCode'])
            #logger.info(poc['isActive'])
            #logger.info(poc['script_name'])
            if poc['media_typeId'] == 4:
                consolidated_list[poc['contactAddress']] = (poc['contactCode'], poc['isActive'], poc['contactDescription'] + " (" + poc['script_name'] + ")")

        #for number in phone_numbers:
        #    if number not in consolidated_list.keys():
        #        consolidated_list.add(number,('','',''))
        logger.info("Consolidated record count - %s", len(consolidated_list))
        return consolidated_list

    #List of all hoo - in original format from response
    def get_hoo_list(self):
        ##Get all undeleted Hoo
        params = { 'isDeleted': 'false', }
        response = self.__get_response('hours-of-operation', params=params)
        hoo_list = response.json().get('hoursOfOperation')
        logger.info("Found hoo count - %s" , len(hoo_list))
        return hoo_list

    def get_hoo(self, external_id):
        ##Get all undeleted Hoo
        params = { 'isDeleted': 'false', }
        response = self.__get_response(f'hours-of-operation/{external_id}', params=params)
        hoo_list = response.json()
        return hoo_list

    def get_skill(self, external_id):
        ##Get all undeleted Hoo
        response = self.__get_response(f'skills/{external_id}')
        skill_list = response.json()
        return skill_list

    def get_campaign_list(self):
        params = { 'isActive': 'true' }
        response = self.__get_response('campaigns', params=params)
        campaign_list = response.json().get('resultSet', {}).get('campaigns', [])
        logger.info("Found skill count %s", len(campaign_list))
        return campaign_list

    def get_skill_list(self):
        ##Get all active Skills
        params = { 'isActive': 'true'}
        response = self.__get_response('skills', params=params)
        skill_list = response.json().get('skills', {})
        logger.info("Found skill count - %s",  len(skill_list))
        return skill_list

    #Simple list of script names as defined by root search
    def get_scripts_list(self):
        #Cope with more than 100 scripts
        is_incomplete_enumeration = True
        consolidated_list = []
        while is_incomplete_enumeration:
            #Note that scripts/files/search seems to be for all files
            params = { 'fields': 'script_name' , 'skip' :  len(consolidated_list)}
            response = self.__get_response('scripts/search', params=params)
            script_list = response.json().get('scriptSearchDetails',[])
            logger.info("Found Scripts: %s" , len(script_list))
            for script in script_list:
                consolidated_list.append(script['script_name'])
            if (len(script_list)) != 100:
                is_incomplete_enumeration = False

        return consolidated_list

    #Get contents of named script (JSON)
    def get_script(self,filename):
        logger.info("Getting Script %s", filename)
        params = { 'scriptPath': filename }
        response = self.__get_response('scripts', params=params)
        return response.text

    #Read JSON from local drive and copy to CXone - note remote_file_name NOT used at this time
    def create_script(self,local_root : str ,local_filename : str , remote_path :str )-> str:
        logger.info("Writing Script to BU %s to %s", local_filename, remote_path )
        file_contents = open(os.path.join(local_root, local_filename), "rt", encoding="utf-8").read()
        if remote_path:
            # We need to find the sub dir path form the OS and replace with a double backslash - as per CXone format
            source_script_name = local_filename[:-5]
            source_script_name = source_script_name.replace(os.path.sep,'\\\\')
            # we meed to add the separate for the destination in cxone doubel backslash
            destination_script_name = remote_path.replace('\\',"\\\\") + "\\\\" + source_script_name
            destination_script_name = destination_script_name.replace(os.path.sep,'\\')
            logger.debug("destination_script_name %s", destination_script_name)
            logger.debug("source_script_name %s", source_script_name)

            file_contents = file_contents.replace('"script_name": "'+ source_script_name +'",' , '"script_name": "'+ destination_script_name +'",')
        headers = {
            'Authorization': 'Bearer ' + self.__access_token,
            'User-Agent': 'WebApp-development',
            'Content-Type' : 'application/json'
        }
        service_endpoint = 'scripts'
        constructed_url = self.__SERVICES_URI + service_endpoint
        response = requests.post(constructed_url, data=file_contents, headers=headers, timeout=30000)
        #response = self.__get_response('scripts', params=params)
        return response.ok
        #return None
        #Read binary file from local drive and copy to CXone, note we use the base path

    def create_wav(self,local_file_name,remote_file_name):
        logger.info('Writing file to BU %s' , remote_file_name)
        contents = open(local_file_name, "rb").read()
        body = '{  "fileName": "' + remote_file_name + '",   "file": "' + (base64.b64encode(contents)).decode('ascii') + '", "overwrite": true }'
        response = self.__post_response('files', params=None, data = body)
        return response.text

    def upload_file(self,remote_item_name,file_contents):
        body = '{  "fileName": "' + remote_item_name + '",   "file": "' + (base64.b64encode(file_contents)).decode('ascii') + '", "overwrite": true }'
        response = self.__post_response('files', params=None, data = body)
        return response.status_code

    def upload_script(self,override_path,file_contents):
        """Override path not enabled"""
        #if len(override_path) > 0:
        #    pass
        #with open('c:/temp/senttoCXOne.json','wb') as f:
        #    f.write(file_contents)
        logger.debug('Writing script to BU %s' , override_path)
        params = {
            'scriptPath': 'PROD\\CustomEvents_PROD',
            'lockScript' : True
        }
        lock_response = self.__put_response('scripts', params=params)
        if lock_response.status_code == 200:
            logger.debug("Locked script")
            script_response = self.__post_response('scripts', params=None, data = file_contents)
            logger.debug("Wrote script and got response %s", script_response.content)
        else:
            logger.debug("Failed to lock script")
            return lock_response
        params['lockScript'] = False
        lock_response = self.__put_response('scripts', params=params)
        logger.debug("Unlocked script and got response %s", lock_response.content)
        return script_response

    def create_capaign(self,campaign_name):
        logger.info('Creating new Campaign %s' , campaign_name)
        body = '{  "campaigns": [{  "campaign_name": "' + campaign_name + '", "isActive": true, } ]}'
        response = self.__post_response('campaigns', params=None, data = body)
        return response.json().get('campaignResults')[0].get('campaign_id')

    #Untested
    def create_team(self,team_name):
        logger.info('Creating new team %s' , team_name)
        body = '{  "teams": [{  "team_name": "' + team_name + '", "isActive": true, } ]}'
        response = self.__post_response('teams', params=None, data = body)
        return response.json().get('results')[0].get('teamId')

    def create_skill(self,skill_name :str, media_type:str, campaign_id: int) -> int:
        logger.info('Creating new Skill %s' , skill_name)
        match media_type:
            #Media Type IDs: Email = 1, Chat =3 , Phone = 4, Voice Mail = 5, Work Item = 6, Social = 8, Digital = 9
            case "Outbound":
                body = '{ "skills": [{"media_typeId": 4, "skill_name": "'+ skill_name +'", "isOutbound": true, "requireDisposition": false, "campaign_id": ' \
                        +str(campaign_id) +', "serviceLevelThreshold": 30, "serviceLevelGoal": 90, "enableShortAbandon" : false, "shortAbandonThreshold" :15}]}'
            case "Digital":
                body = '{ "skills": [{"media_typeId": 9, "skill_name": "'+ skill_name +'", "isOutbound": false, "requireDisposition": false, "campaign_id": ' \
                        + str(campaign_id)+', "serviceLevelThreshold": 30, "serviceLevelGoal": 90, "enableShortAbandon" : false, "shortAbandonThreshold" :15}]}'
            case "Voicemail":
                body = '{ "skills": [{"media_typeId": 5, "skill_name": "'+ skill_name +'", "isOutbound": false, "requireDisposition": false, "campaign_id": ' \
                        + str(campaign_id)+', "serviceLevelThreshold": 30, "serviceLevelGoal": 90, "enableShortAbandon" : false, "shortAbandonThreshold" :15}]}'
            case _:
                body = '{ "skills": [{"media_typeId": 4, "skill_name": "'+ skill_name +'", "isOutbound": false, "requireDisposition": false, "campaign_id": ' \
                        + str(campaign_id)+', "serviceLevelThreshold": 30, "serviceLevelGoal": 90, "enableShortAbandon" : false, "shortAbandonThreshold" :15}]}'

        response = self.__post_response('skills', params=None, data = body)
        if response.ok:
            return response.json().get('skillsResults',[])[0].get('skillId',0)
        else:
            return None

    def create_hoo(self,hoo_name : str) -> bool:

        #days = [ { "day" : "Monday", "openTime" : "09:00:00", "closeTime" : "17:00:00",
        # "hasAdditionalHours" : False, "additionalOpenTime" : "", "additionalCloseTime": "", "isClosedAllDay" : False}]
        #holidays = []
        #body = { "profileName" : hoo_name, "days" :days, "holidays" : holidays }
        #body = { "profileName" : hoo_name, "days" :days }
        body = '{ "profileName" : "'+ hoo_name + '" }'
        response = self.__post_response('hours-of-operation', params=None, data = body)
        return response.json().get('profileId',0)

    def update_hoo(self, hoo_id, hoo: dict, profile_name: str, description:str, days:list, holidays:list):
        if len(profile_name) < 1:
            profile_name = hoo['hoursOfOperationProfileName']
        if len(description) < 1:
            description = hoo['description']
        if len(days) < 1:
            days = hoo.get('days',[])
        if len(holidays) < 1:
            holidays = hoo.get('holidays',{})

        new_hoo = { "hoursOfOperationProfileName" : profile_name,"description": description , "days" : days, "holidays" : holidays}
        new_hoo['notes'] = hoo.get('notes','')
        response = self.__put_response(f'hours-of-operation/{hoo_id}', params=None, data = json.dumps(new_hoo))

        return response

    def create_poc(self,poc_number,poc_name, script_name):
        logger.info('Creating entry point to script %s' , poc_number)
        body = '{  "pointOfContact": "' + poc_number + '",   "pointOfContactName": "' + poc_name + '", "script_name": "'+ script_name + '" }'
        response = self.__post_response('points-of-contact', params=None, data = body)
        return response.text

    #Create a names static address book and add entries from list
    def create_address_book(self, address_book_name, address_book_json):
        #Create address book by name
        #https://developer.niceincontact.com/API/AdminAPI#/AddressBook/CreateAddressBookv4
        logger.info("Creating address book %s", address_book_name)
        service_endpoint = 'address-books'

        constructed_url = self.__SERVICES_URI + service_endpoint
        headers = {
            'Authorization': 'Bearer ' + self.__access_token,
            'User-Agent': 'WebApp-development',
        }
        params = {
            'address_book_name': address_book_name , 
            'addressBookType ': 'Standard'
        }
        response = requests.post(constructed_url, params=params, headers=headers, timeout=30000)
        try:
            address_book_id = response.json().get('resultSet')['address_book_id']
        except Exception as e:
            logger.info("Eception caught: %s" , repr(e))
            return False
        #Now upload files to address book
        service_endpoint = 'address-books/' + address_book_id +'/entries'

        constructed_url = self.__SERVICES_URI + service_endpoint

        response = requests.post(constructed_url, json = address_book_json , headers=headers, timeout=30000)
        #And finally give everyone access
        service_endpoint = 'address-books/' + address_book_id +'/assignment'
        constructed_url = self.__SERVICES_URI + service_endpoint

        data_list = []
        data_list.append( {'entityId' : 'All'})
        params = {
            'addressBookAssignments' : data_list 
        }

        response = requests.post(constructed_url, json = params , headers=headers, timeout=30000)
        return response.text

    #create new dispositions based on list
    def create_dispositions(self,disposition_json):
        """Not implemented yet"""
        logger.debug(disposition_json)
        #https://developer.niceincontact.com/API/AdminAPI#/Skills/post-dispositions
        #result =  self.PostJson(self.__SERVICES_URI + "dispositions",None,disposition_json)
        #return result.txt
        return None

    def upload_tags(self, filename):
        with open(filename, "rt", encoding="utf-8") as f:
            for line in f:
                body = '{  "tagName": "' + line.strip().rstrip()[:40] + '",   "notes" : "NA" }'
                response = self.__post_response('tags', params=None, data = body)
                if response.status_code != 200:
                    logger.info("Error adding %s", line)
        return True
