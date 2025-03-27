"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Ad-Hoc commands - execute from command line
#   Date:           17/01/24
################################################################################"""
import os
import sys
import local.cxone

#Read tab separated file with headers to make an array[] of dictionary objects
#Fist column must have column names
def ReadDataObjectArray(fileName : str) -> dict:
    with open(fileName, encoding='utf-8') as f:
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
    for filename in os.listdir(localFilePath):
        if os.path.isfile(localFilePath + '\\' + filename):
            client.CreateScript(localFilePath + "\\" +filename, remoteFilePath + "\\" + filename)
        else:
            UploadScripts(client,localFilePath + "\\" + filename, remoteFilePath + "\\" + filename)

def UploadWav(client,localFilePath,remoteFilePath):
    #Do something here
    for filename in os.listdir(localFilePath):
        if os.path.isfile(localFilePath + '\\' + filename):
            client.CreateWav(localFilePath + "\\" +filename,remoteFilePath + "\\\\" + filename )
        else:
            UploadWav(client,localFilePath + "\\" + filename, remoteFilePath + "\\\\" + filename)
    return

def UploadAddressBook(client,file_name,addressBookName):
    #firstName\tLastName\temail\tphoneNumber\tmobile
    data = ReadDataObjectArray(file_name)
    client.CreateAddressBook({ "addressBookEntries" : data})
    return

def UploadDispositions(client,file_name):
    #dispositionName\tisPreviewDisposition
    data = ReadDataObjectArray(file_name)
    client.CreateDispositions({ "dispositions" : data})
    return

def UploadUnavailableCodes(client,file_name):
    #name\tisACW\tagentTimeout\tnotes
    #Slightly different - we have to do each one individually
    data_list = ReadDataObjectArray(file_name)
    for item in data_list:
        client.CreateUnavailableCode(item)
    return 

def UploadSkills(client, fileName):
    #https://developer.niceincontact.com/API/AdminAPI#/Skills/post-skills
    #Minimal - skillName\trequireManualAccept\tmediaTypeId = 4
    data = ReadDataObjectArray(fileName)
    client.CreateSkills({ "skills" : data})
    return    

key = input("Enter Key for BU: ")
secret = input("Enter Secret for BU: ")

cx_client = local.cxone.CxOne(key,secret)

if not cx_client.is_connected():
    print ("Print failed to connect to application - terminating now")
    sys.exit()

businessUnit = cx_client.GetBusinessUnit()
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
        active_hoo = cx_client.GetHooList()
        hoo = None
        for hoo in active_hoo:
            if hoo['hoursOfOperationProfileId'] == int(hoo_id):
                original_hoo = hoo
                break
        if original_hoo is not None:
            cx_client.Update_Hoo(hoo_id,original_hoo,"", "", [], holidays)
    case '_':
        print('Invalid option detected please retry')


   #1. Upload all scripts to BU - remote path is NOT enabled for config at the moment
        #inPath = ".\\packages\\default\\scripts"
        #UploadScripts(client,inPath, "")

        #2. Upload all wav files from default path - remote path will always be root at the moment
        #inPath = ".\\packages\\default\\audio"
        #UploadWav(client,inPath, "Prompts\\\\Prod") #Output path not honoured at the moment - use in built path in script

        #3. Create Campaign
        #campaignId = client.CreateCampaign('ContactCentre')
        ## Create Teams(Default and Customer)
        #4. Create No-Agent Skill
        #skillId = client.CreateSkill('Default - No Agent',False, campaignId)
        #5. Add POC connected to Entry PROD and No agent skill
        #for poc in client.GetPocInfo():
        #    if (input("Would you like to connect the POC (" + poc + ") to the entry script? ")  == "y"):
        #        client.CreatePoc(poc,"ContactCentre","Entry_PROD")
        #Create skills in BRD manually at this time - need skill is t
        #Need to add outbound here too.
        # skillId = 10359694
        #print("Password Reset ",client.CreateSkill('Password Reset',False, campaignId))
        #print("Schools Online",client.CreateSkill('Schools Online',False, campaignId))
        #print("Student / School Enquiries",client.CreateSkill('Student and School Enquiries',False, campaignId))
        #print("General",client.CreateSkill('General',False, campaignId))
        #print("General",client.CreateSkill('Outbound',True, campaignId))

        #Some other helper functions
        ##filename = ".\\Schools.txt"
        ##addressBookName = "Administration"
        ##UploadAddressBook(client,filename,addressBookName)

        #Add tags from list in text file
        #filename = ".\\packages\\dcceew\\tags.txt"
        #client.UploadTags(filename)
