import os, requests
#, time, config, json
import base64

class CxOne(object):
    #static
    fetch_token_url = 'https://au1.nice-incontact.com/authentication/v1/token/access-key'
    service_base_url = 'https://api-au1.niceincontact.com/incontactapi/services/v30.0/'
    access_token = None
    bu = None

    def __init__(self, client_key, client_secret ):
        self.client_key = client_key
        self.client_secret = client_secret

    #HTTP Request GET with default headers and customisable params
    def __getResponse(self,service_endpoint,params=None,):
        print("Getting service endpoint /" + service_endpoint)
        constructed_url = self.service_base_url + service_endpoint
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'User-Agent': 'WebApp-development',
        }
        return  requests.get(constructed_url, headers=headers, params = params, data = None, timeout=30000)

    #HTTP Post with default headers and customisable params
    def __postResponse(self,service_endpoint,params,data=None):
        print("Posting to service endpoint /" + service_endpoint)
        constructed_url = self.service_base_url + service_endpoint
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'User-Agent': 'WebApp-development',
        }
        return requests.post(constructed_url,headers=headers, data=data, params = params, timeout=30000 )

    # This function performs the bearer token creation.
    def get_token(self):
        print('Getting token')
        body = {
            'accessKeyId': self.client_key,
            'accessKeySecret': self.client_secret
        }
        try:
            response = requests.post(self.fetch_token_url, json=body, timeout=30000)
        except Exception as e:
            print (f'Exception {repr(e)}')
            return None

        self.access_token = response.json().get('access_token')
        #print('We got a token - %s' % self.access_token)
        self.bu = self.GetBusinessUnit()
        return self.access_token

    def Connect(self):
        return self.get_token()

    #Return the BU info
    def GetBusinessUnit(self):
        response = self.__getResponse('business-unit')
        business_units = response.json().get('businessUnits')
        return next(iter(business_units), None)

    def GetAudioList(self, root_path = None):
        response = self.__getResponse('folders' ,{ 'folderName' :  root_path })
        if response.status_code != 200:
            return []
        else:
            return response.json().get('files',[])

    def GetPocList(self):
        ##Get all available phone numbers
        response = self.__getResponse('phone-numbers')
        if response.status_code != 204:
            phone_numbers = response.json().get('phoneNumbers')
            print(f'Found phone numbers {len(phone_numbers) or '0'}')
        else:
            phone_numbers = []

        ##Now get all active POC as we need to remove these number from our list/define them more accurately
        response = self.__getResponse('points-of-contact')
        points_of_contact = response.json().get('pointsOfContact')
        print(f"Found poc numbers {response.json().get('totalRecords') or '0'}")

        #Fields we need contactAddress, isActive, scriptName
        #We need to be sure it is "mediaTypeId": 4, "outboundSkill": false,
        consolidated_list = dict()
        #For all phone numbers
        for number in phone_numbers:
            #print(number)
            consolidated_list[number] = ('-1','','Available POC')

        #Add all POC
        for poc in points_of_contact:
            #print(poc['contactAddress'])
            #print(poc['contactCode'])
            #print(poc['isActive'])
            #print(poc['scriptName'])
            if poc['mediaTypeId'] == 4:
                consolidated_list[poc['contactAddress']] = (poc['contactCode'], poc['isActive'], poc['scriptName'])

        #for number in phone_numbers:
        #    if number not in consolidated_list.keys():
        #        consolidated_list.add(number,('','',''))
        print('Consolidated record count - % s' % len(consolidated_list))
        return consolidated_list

    #List of all hoo - in original format from response
    def GetHooList(self):
        ##Get all undeleted Hoo
        params = { 'isDeleted': 'false', }
        response = self.__getResponse('hours-of-operation', params=params)
        hoo_list = response.json().get('hoursOfOperation')
        print('Found hoo count - % s' % len(hoo_list))
        return hoo_list

    def GetCampaignList(self):
        params = { 'isActive': 'true' }
        response = self.__getResponse('campaigns', params=params)
        campaign_list = response.json().get('campaigns')
        print('Found skill count - % s' % len(campaign_list))
        return campaign_list

    def GetSkillList(self):
        ##Get all active Skills
        params = { 'isActive': 'true', 'mediaTypeId' : 4 }
        response = self.__getResponse('skills', params=params)
        skill_list = response.json().get('skills')
        print('Found skill count - % s' % len(skill_list))
        return skill_list

    #Simple list of script names as defined by root search
    def GetScriptsList(self):
        #Cope with more than 100 scripts
        is_incomplete_enumeration = True
        consolidated_list = []
        while is_incomplete_enumeration:
            #Note that scripts/files/search seems to be for all files
            params = { 'fields': 'scriptName' , 'skip' :  len(consolidated_list)}
            response = self.__getResponse('scripts/search', params=params)
            script_list = response.json().get('scriptSearchDetails')
            print('Found Scripts:' , len(script_list or []))
            for script in (script_list or []):
                consolidated_list.append(script['scriptName'])
            if (len(script_list or [])) != 100:
                is_incomplete_enumeration = False

        return consolidated_list

    #Get contents of named script (JSON)
    def GetScript(self,filename):
        print('Getting Script ' , filename)
        params = { 'scriptPath': filename }
        response = self.__getResponse('scripts', params=params)
        return response.text

    #Read JSON from local drive and copy to CXone - note remoteFileName NOT used at this time
    def CreateScript(self,local_root : str ,local_filename : str , remote_path :str )-> str:
        print('Writing Script to BU ' , local_filename)
        fileContents = open(os.path.join(local_root, local_filename), "rt", encoding="utf-8").read()
        if remote_path:
            source_script_name = local_filename[:-5]
            destination_script_name = (remote_path + "\\" + source_script_name).replace('\\','\\\\')
            fileContents = fileContents.replace('"scriptName": "'+ source_script_name.replace('\\','\\\\') +'",' , '"scriptName": "'+ destination_script_name +'",')
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'User-Agent': 'WebApp-development',
            'Content-Type' : 'application/json'
        }
        service_endpoint = 'scripts'
        constructed_url = self.service_base_url + service_endpoint
        response = requests.post(constructed_url, data=fileContents, headers=headers, timeout=30000)
        #response = self.__getResponse('scripts', params=params)
        return response.ok
        #return None
        #Read binary file from local drive and copy to CXone, note we use the base path

    def CreateWav(self,localFileName,remoteFileName):
        print('Writing file to BU ' , remoteFileName)
        fileContents = open(localFileName, "rb").read()
        body = '{  "fileName": "' + remoteFileName + '",   "file": "' + (base64.b64encode(fileContents)).decode('ascii') + '", "overwrite": true }'
        response = self.__postResponse('files', params=None, data = body)
        return response.text

    def UploadItem(self,remote_item_name,file_contents):
        body = '{  "fileName": "' + remote_item_name + '",   "file": "' + (base64.b64encode(file_contents)).decode('ascii') + '", "overwrite": true }'
        response = self.__postResponse('files', params=None, data = body)
        return response.text

    def CreateCampaign(self,campaignName):
        print('Creating new Campaign ' , campaignName)
        body = '{  "campaigns": [{  "campaignName": "' + campaignName + '", "isActive": true, } ]}'
        response = self.__postResponse('campaigns', params=None, data = body)
        return response.json().get('campaignResults')[0].get('campaignId')

    #Untested
    def CreateTeam(self,teamName):
        print('Creating new team ' , teamName)
        body = '{  "teams": [{  "teamName": "' + teamName + '", "isActive": true, } ]}'
        response = self.__postResponse('campaigns', params=None, data = body)
        return response.json().get('results')[0].get('teamId')

    def CreateSkill(self,skillName,isOutbound: bool,campaignId: int):
        print('Creating new Skill ' , skillName)
        if isOutbound:
            body = '{ "skills": [{"mediaTypeId": 4, "skillName": "'+ skillName +'", "isOutbound": true, "requireDisposition": false, "campaignId": '+str(campaignId)+', "serviceLevelThreshold": 30, "serviceLevelGoal": 90, "enableShortAbandon" : false, "shortAbandonThreshold" : 15 } ] }'
        else:
            body = '{ "skills": [{"mediaTypeId": 4, "skillName": "'+ skillName +'", "isOutbound": false, "requireDisposition": false, "campaignId": '+str(campaignId)+', "serviceLevelThreshold": 30, "serviceLevelGoal": 90, "enableShortAbandon" : false, "shortAbandonThreshold" : 15 } ] }'
        response = self.__postResponse('skills', params=None, data = body)
        return response.json().get('skillsResults')[0].get('skillId')

    def CreateHoo(self,hoo_name : str) -> bool:
        return False

    def CreatePoc(self,pocNumber,pocName, scriptName):
        print('Creating entry point to script ' , pocNumber)
        body = '{  "pointOfContact": "' + pocNumber + '",   "pointOfContactName": "' + pocName + '", "scriptName": "'+ scriptName + '" }'
        response = self.__postResponse('points-of-contact', params=None, data = body)
        return response.text

    #Create a names static address book and add entries from list
    def CreateAddressBook(self, addressBookName, addressBookJson):
        #Create address book by name
        #https://developer.niceincontact.com/API/AdminAPI#/AddressBook/CreateAddressBookv4
        print('Creating address book ' + addressBookName)
        service_endpoint = 'address-books'

        constructed_url = self.service_base_url + service_endpoint
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'User-Agent': 'WebApp-development',
        }
        params = {
            'addressBookName': addressBookName , 
            'addressBookType ': 'Standard'
        }
        response = requests.post(constructed_url, params=params, headers=headers, timeout=30000)
        try:
            addressBookId = response.json().get('resultSet')['addressBookId']
        except Exception as e:
            print(f'Eception caught: {repr(e)}')
            return False
        #Now upload files to address book
        service_endpoint = 'address-books/' + addressBookId +'/entries'

        constructed_url = self.service_base_url + service_endpoint

        response = requests.post(constructed_url, json = addressBookJson , headers=headers, timeout=30000)
        #And finally give everyone access
        service_endpoint = 'address-books/' + addressBookId +'/assignment'
        constructed_url = self.service_base_url + service_endpoint

        data_list = []
        data_list.append( {'entityId' : 'All'})
        params = {
            'addressBookAssignments' : data_list 
        }

        response = requests.post(constructed_url, json = params , headers=headers, timeout=30000)
        return response.text

    #create new dispositions based on list
    def CreateDispositions(self,dispositionJson):
        #https://developer.niceincontact.com/API/AdminAPI#/Skills/post-dispositions
        #result =  self.PostJson(self.service_base_url + "dispositions",None,dispositionJson)
        #return result.txt
        return None

    def UploadTags(self, fileName):
        with open(fileName, "rt", encoding="utf-8") as f:
            for line in f:
                body = '{  "tagName": "' + line.strip().rstrip()[:40] + '",   "notes" : "NA" }'
                response = self.__postResponse('tags', params=None, data = body)
                if response.status_code != 200:
                    print("Error adding ", line)
        return True