import local.cxone
import os
import json
import csv

#Read tab separated file with headers to make an array[] of dictionary objects
#Fist column must have column names
def ReadDataObjectArray(fileName):
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
            pass
            client.CreateScript(localFilePath + "\\" +filename, remoteFilePath + "\\" + filename)
        else:
            UploadScripts(client,localFilePath + "\\" + filename, remoteFilePath + "\\" + filename)

    pass

def UploadWav(client,localFilePath,remoteFilePath):
    #Do something here
    for filename in os.listdir(localFilePath):
        if os.path.isfile(localFilePath + '\\' + filename):
            pass
            client.CreateWav(localFilePath + "\\" +filename,remoteFilePath + "\\\\" + filename )
        else:
            UploadWav(client,localFilePath + "\\" + filename, remoteFilePath + "\\\\" + filename)
    return


def UploadAddressBook(client,fileName,addressBookName):
    #firstName\tLastName\temail\tphoneNumber\tmobile
    data = ReadDataObjectArray(fileName)
    client.CreateAddressBook({ "addressBookEntries" : data})
    client
    return

def UploadDispositions(client,fileName):
    #dispositionName\tisPreviewDisposition
    data = ReadDataObjectArray(fileName)
    client.CreateDispositions({ "dispositions" : data})
    return

def UploadUnavailableCodes(client,fileName):
    #name\tisACW\tagentTimeout\tnotes
    #Slightly different - we have to do each one individually
    data_list = ReadDataObjectArray(fileName)
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

client = local.cxone.CxOne(key,secret)

if (client.get_token()):
    businessUnit = client.GetBusinessUnit()
    if (input("You are connecting to Business Unit:" + businessUnit['businessUnitName']+ " (press 'y' to continue): ") == "y"):
        print("Starting")
        
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
        #filename = ".\Admin.txt"
        #addressBookName = "Administration"
        #UploadAddressBook(client,filename,addressBookName)

        #Add tags from list in text file
        #filename = ".\\packages\\dcceew\\tags.txt"
        #client.UploadTags(filename)

    else:
        print("Aborted")
else:
    print("Unable to get valid token")
 


