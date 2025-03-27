"""Simple file IO functions"""
import os

from local import logger

ROOT_PACKAGE_PATH = "./packages"
#ROOT_USER_PATH = "./users"

#def create_project_folder(username,projectname):
#    newpath = root_user_path + "/" + username + "/" + projectname
#    if not os.path.exists(root_user_path):
#        os.makedirs(root_user_path)
#    if not os.path.exists(newpath):
#        os.makedirs(newpath)

def get_system_audio_file_list(packagename):

    logger.info("We are opening files from %s" , os.getcwd())
    logger.info("Path is  %s" , ROOT_PACKAGE_PATH + '/' + packagename + "/systemaudio.txt")
    with open(ROOT_PACKAGE_PATH + '/' + packagename + "/systemaudio.txt", 'r', encoding="utf-8") as f:
        audio_dictionary = dict()
        for line in f:
            splits = line.split('\t')
            audio_dictionary[splits[0]]= splits[1]

    logger.info("We identified %s " , len(audio_dictionary) )
    return audio_dictionary
