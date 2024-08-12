import cxone
import tts
import os
import db

hoo = db.Select("hoo",["id","name"],{"project_id" : 1 })
def SpeechToText():
    test = tts.Speech('<key>')
    directory_path = './CC'
    output_file = open("results.txt", "a")

    folder = os.fsencode(directory_path)

    for file in os.listdir(folder):
        filename = directory_path + "//" + os.fsdecode(file)
        if filename.endswith(('.wav')):
            result = test.get_text(filename)
            print(filename,chr(9),result[0]['Display'])
            output_file.write(filename + chr(9) + result[0]['Display'])

    output_file.close()

def DoSomething():
    key = ""
    secret = ""

    client = CXOne
    client.get_token()
    
    #Extract files from a demo BU
    #for file in client.GetScriptsList():
    #    file_contents = client.GetScript(file)
    #    output_file = open(file, "x")
    #    output_file.write(file_contents)
    #    output_file.close()

    #Upload files to new BU (modify the script list)
    #Get list of files from package directory
    inPath = ".\\packages\default\scripts"

    WriteToCxOne(client,inPath, "")
    
def WriteToCxOne(client,localFilePath,remoteFileName):
    #Do something here
    for filename in os.listdir(localFilePath):
        if os.path.isfile(localFilePath + '\\' + filename):
            pass
            client.WriteScript(localFilePath + "\\" +filename,remoteFileName )
        else:
            WriteToCxOne(client,localFilePath + "\\" + filename, filename)

    pass

    
    
DoSomething()