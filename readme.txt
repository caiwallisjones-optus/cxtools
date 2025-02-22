Date        Version     Comments
27/01/24    0.0.0       Started with Azure quickstart
30/01/24    0.0.0       Added configuration parser/ini file
06/02/24    0.0.0       Added SQLLite and backend data tables - cache process for data
06/08/24    0.0.0       Removed configuration and refactoring, updated deployment pages and added HTML for ease of use

Resources:
#https://learn.microsoft.com/en-us/azure/app-service/quickstart-python?tabs=flask%2Cwindows%2Cazure-cli%2Cvscode-deploy%2Cdeploy-instructions-azportal%2Cterminal-bash%2Cdeploy-instructions-zip-azcli
#https://pypi.org/project/Flask-Login/
#https://github.com/MicrosoftTranslator/Text-Translation-API-V3-Flask-App-Tutorial

CRTL F CTRL K - format HTML


#Setting up .venv
#Navigate to root
(.venv) C:\Users\P58769\source\repos\CXone>

cd \users\P58769\source\repos\CXone

.venv\scripts\activate

flask --debug run

BUGS:
14/1/24   Get audio does not enumerate sub folders for files
               
          When adding a new skill we are only adding name and desciption
               - we can use the getParmam list to be more generic we need to add the format type
          We now put PROD and dev into subfolders so we also need to udpate env variable to match this in deployment and script suff
          Add a prune function to remove orphan action/responses in the menu trees

TODO:
                    