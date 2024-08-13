import os

root_package_path = "./packages"
root_user_path = "./users"

def CreateProjectFolder(username,projectname):
    newpath = root_user_path + "/" + username + "/" + projectname
    if not os.path.exists(root_user_path):
        os.makedirs(root_user_path)
    if not os.path.exists(newpath):
        os.makedirs(newpath)

def GetSystemAudioFileList(packagename):
        
    print("We are opening files from %s" % os.getcwd())
    print("Path is  %s" % root_package_path + '/' + packagename + "/systemaudio.txt")
    f = open(root_package_path + '/' + packagename + "/systemaudio.txt", 'r')
        
    audioDictionary = dict()

    for line in f:
        splits = line.split('\t')
        audioDictionary[splits[0]]= splits[1]

    f.close()
    print("We uploaded % s " % len(audioDictionary) )
        
    return audioDictionary