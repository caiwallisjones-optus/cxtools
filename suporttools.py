"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Ad-Hoc commands - execute from command line
#   Date:           17/01/24
################################################################################"""
import os
import sys
import local.cxone
import local.tts
import logging
import json


#Read tab separated file with headers to make an array[] of dictionary objects
#First column must have column names
def ReadDataObjectArray(file_name : str) -> dict:
    """Read the file and load it as a dict list"""
    with open(file_name, encoding='utf-8') as f:
        headers = f.readline().strip().split('\t')
         # Read the remaining lines
        data_list = []
        for line in f:
            values = line.strip().split('\t')
            #Supported column names here:
            #https://developer.niceincontact.com/API/AdminAPI#/AddressBook/Create%20Address%20Book%20Entries
            data_dict = dict(zip(headers, values))
            data_list.append(data_dict)
    return data_list

def UploadScripts(client,localFilePath,remoteFilePath):
    #Allows recursion in request
    for file_name in os.listdir(localFilePath):
        if os.path.isfile(localFilePath + '\\' + file_name):
            client.create_script(localFilePath + "\\" +file_name, remoteFilePath + "\\" + file_name)
        else:
            UploadScripts(client,localFilePath + "\\" + file_name, remoteFilePath + "\\" + file_name)

def UploadWav(client,localFilePath,remoteFilePath):
    #Do something here
    for file_name in os.listdir(localFilePath):
        if os.path.isfile(localFilePath + '\\' + file_name):
            client.create_wav(localFilePath + "\\" +file_name,remoteFilePath + "\\\\" + file_name )
        else:
            UploadWav(client,localFilePath + "\\" + file_name, remoteFilePath + "\\\\" + file_name)
    return

def UploadAddressBook(client,file_name,address_book_name):
    #firstName\tLastName\temail\tphoneNumber\tmobile
    data = ReadDataObjectArray(file_name)
    client.create_address_book({ "addressBookEntries" : data})
    return

def UploadDispositions(client,file_name):
    #dispositionName\tisPreviewDisposition
    data = ReadDataObjectArray(file_name)
    client.create_dispositions({ "dispositions" : data})
    return

def UploadUnavailableCodes(client,file_name):
    #name\tisACW\tagentTimeout\tnotes
    #Slightly different - we have to do each one individually
    data_list = ReadDataObjectArray(file_name)
    for item in data_list:
        client.CreateUnavailableCode(item)
    return True

def upload_skills(client, file_name):
    #https://developer.niceincontact.com/API/AdminAPI#/Skills/post-skills
    #Minimal - skill_name\trequireManualAccept\tmedia_typeId = 4
    data = ReadDataObjectArray(file_name)
    client.CreateSkills({ "skills" : data})
    return True    

def setup_logging():
    # Create a custom logger
    app_log = logging.getLogger('cxsupporttools')
    app_log.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler('cxsupporttools.log')
    #file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
    file_handler.setFormatter(logging.Formatter('%(message)s'))
    app_log.addHandler(file_handler)
    app_log.level = logging.DEBUG
    return app_log


#Start our script here

logger = setup_logging()
logger.info("Started\n")

print('Please enter a task to perform (add options to supporttools.py as needed):')
print('     1. Read the WAV files in folder and extract as text')
print('     2. Upload items to CXone')
action = input("Enter action to perform: ")

match action:
    case '1':
        #Read the WAV files in folder and extract as text
        #inPath = ".\\packages\\default\\audio"
        key = input("Enter TTS key for azure: ")
        inPath = input("Enter path to read WAV files from: ")
        if not os.path.exists(inPath):
            print("Invalid path - terminating now")
            sys.exit()
        tts_client = local.tts.Speech(key)
        tts_client.get_token()

        if not tts_client.get_token():
            print("Failed to connect to TTS - terminating now")
            sys.exit()

        for root, dirs, files in os.walk(inPath):
            for file in files:
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path):
                    # Replace the following line with your actual processing logic
                    result = tts_client.get_text(file_path)
                    #result = [1]
                    #result[0] = {"Display": "Test"}

                    print(f"{file_path}\t{result[0]['Display']}")
                    logger.info("%s\t%s", file_path, result[0]['Display'])
                else:
                    print(f"Not a file {file}")
        
        print("Done")
        sys.exit()


key = input("Enter Key for BU: ")
secret = input("Enter Secret for BU: ")

cx_client = local.cxone.CxOne(key,secret)

if not cx_client.is_connected():
    print ("Print failed to connect to application - terminating now")
    sys.exit()

businessUnit = cx_client.get_business_unit()
if input("You are connecting to Business Unit:" + businessUnit['businessUnitName']+ " (press 'y' to continue): ") == "y":
    print('Validated BU - continuing')
else:
    print ("Invalid BU - terminating now")
    sys.exit()


print('Please enter a task to perform (add options to supporttools.py as needed):')
print('     1. Load holidays to BU')
print('     2. Load an address book to the BU')
print('     3. Load tags to BU')
action = input("Enter action to perform: ")

match action:
    case '1':
        holiday_file = input("Enter holiday file to add to the BU (default 'packages\\default\\holidays_sa.txt'): ")
        holiday_file = '.\\packages\\default\\holidays_sa.txt'
        holidays = ReadDataObjectArray(holiday_file)
        print (f'Found {len(holidays)} in file')
        hoo_id = input("Enter HOO ID to update: ")
        input('press any key to begin update')
        active_hoo = cx_client.get_hoo_list()
        hoo = None
        for hoo in active_hoo:
            if hoo['hoursOfOperationProfileId'] == int(hoo_id):
                original_hoo = hoo
                break
        if original_hoo is not None:
            cx_client.update_hoo(hoo_id,original_hoo,"", "", [], holidays)
    case '_':
        print('Invalid option detected please retry')


   #1. Upload all scripts to BU - remote path is NOT enabled for config at the moment
        #inPath = ".\\packages\\default\\scripts"
        #UploadScripts(client,inPath, "")

        #2. Upload all wav files from default path - remote path will always be root at the moment
        #inPath = ".\\packages\\default\\audio"
        #UploadWav(client,inPath, "Prompts\\\\Prod") #Output path not honoured at the moment - use in built path in script

        #3. Create Campaign
        #campaign_id = client.create_capaign('ContactCentre')
        ## Create Teams(Default and Customer)
        #4. Create No-Agent Skill
        #skillId = client.create_skill('Default - No Agent',False, campaign_id)
        #5. Add POC connected to Entry PROD and No agent skill
        #for poc in client.GetPocInfo():
        #    if (input("Would you like to connect the POC (" + poc + ") to the entry script? ")  == "y"):
        #        client.create_poc(poc,"ContactCentre","Entry_PROD")
        #Create skills in BRD manually at this time - need skill is t
        #Need to add outbound here too.
        # skillId = 10359694
        #print("Password Reset ",client.create_skill('Password Reset',False, campaign_id))
        #print("Schools Online",client.create_skill('Schools Online',False, campaign_id))
        #print("Student / School Enquiries",client.create_skill('Student and School Enquiries',False, campaign_id))
        #print("General",client.create_skill('General',False, campaign_id))
        #print("General",client.create_skill('Outbound',True, campaign_id))

        #Some other helper functions
        ##file_name = ".\\Schools.txt"
        ##address_book_name = "Administration"
        ##UploadAddressBook(client,file_name,address_book_name)

        #Add tags from list in text file
        #file_name = ".\\packages\\dcceew\\tags.txt"
        #client.upload_tags(file_name)
