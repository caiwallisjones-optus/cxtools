import os

root_package_path = ".\\packages"
root_user_path = ".\\users"

def CreateProjectFolder(username,projectname):
    newpath = root_user_path + "\\" + username + "\\" + projectname
    if not os.path.exists(newpath):
        os.makedirs(newpath)

def GetSystemAudioFileList(packagename):
        
    f = open(root_package_path + '\\' + packagename + "\\systemaudio.txt", 'r')
        
    audioDictionary = dict()

    for line in f:
        splits = line.split('\t')
        audioDictionary[splits[0]]= splits[1]

    f.close()
    print("We uploaded % s " % len(audioDictionary) )
        
    return audioDictionary