"""################################################################################
#
#   Author:         Cai Wallis-Jones
#   Description:    Simple async API Endpoints
#   Date:           17/01/24
#
################################################################################"""
import io
from flask import request,flash,Blueprint, g, render_template #jsonify,

from routes.common import safe_route
import local.db
import local.cxone

bp = Blueprint('deployment', __name__)


@bp.route('/deployment',  methods = ['GET', 'POST'])
@safe_route
def deployment():
    """General deployment process"""
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        client = None
        #project = local.db.Select("project","*",{ "id" : g.data_model.project_id})
        match action:
            case "bu_check":
                try:
                    g.data_model.ValidateConnection()
                    if g.data_model.connected_bu_name is not None:
                        flash(f"Successful connection to {g.data_model.connected_bu_name} ({g.data_model.connected_bu_id}) " +
                                "- this validation will expire in 24 hrs","Information")
                    else:
                        flash("Error connecting to business unit - please check you project key/secret","Error")
                except Exception as e:
                    print (f"Exception {e}")
                    result = "Unknown connection error - please try again later"
                    flash(result,"Error")
            case "package_validate":
                if g.data_model.ValidatePackage():
                    flash("No duplicate scripts identified - package can be deployed","Information")
                else:
                    flash("Duplicate files located on remote server - these scripts be overwritten if you deploy:<br>" +
                            "<br>".join(g.data_model.errors),"Warning")
            case "package_upload":
                if g.data_model.UploadPackage():
                    flash("Package base scripts uploaded","Information")
                else: flash("Something went wrong:<br>" + "<br>".join(g.data_model.errors),"Error")
            case "audio_validate":
                if g.data_model.ValidateAudio():
                    flash("No duplicate audio files located","Information")
                else:
                    flash("Audio files already exist in in destination - uploading will overwrite them" + "<br>".join(g.data_model.errors),"Warning")
            case "audio_upload":
                if g.data_model.UploadAudioPackage():
                    flash("Audio has been created and uploaded","Information")
                else:
                    flash("Something went wrong : " + "<br>".join(g.data_model.errors),"Error")
            case "hoo_validate":
                if g.data_model.ValidateHooConfig():
                    flash("All existing HOO have been linked and new HOO can be deployed to BU","Information")
                else:
                    flash("Review potential issues before deploying" + "<br>".join(g.data_model.errors),"Warning")
            case "hoo_upload":
                if g.data_model.UploadHoo():
                    flash("HOO have been created and uploaded","Information")
                    g.data_model.ValidateHooConfig()
                else:
                    flash("Something went wrong : " + "<br>".join(g.data_model.errors),"Error")
                    g.data_model.ValidateHooConfig()
            case "skills_validate":
                if g.data_model.ValidateSkillsConfig():
                    flash("No skills in BU that would be overwritten by this implentation","Information")
                else:
                    flash("Review potential issues before deploying" + "<br>".join(g.data_model.errors),"Warning")
            case "skills_upload":
                if g.data_model.UploadSkills():
                    flash("Skills have been created and uploaded","Information")
                    g.data_model.ValidateSkillsConfig()
                else:
                    flash("Something went wrong : " + "<br>".join(g.data_model.errors),"Error")
                    g.data_model.ValidateSkillsConfig()
            case "addressbook_upload":
                file = request.files['addressbook_file']
                address_name = request.form.get('addressbook_name')
                file.stream.seek(0)
                wrapper = io.TextIOWrapper(file.stream,  encoding="utf-8", )
                data_list = read_data_list(wrapper)

                client = None
                if (client is not None and client.get_token() is not None):
                    client.CreateAddressBook(address_name,{ "addressBookEntries" : data_list})
                    flash("Address book uploaded","Information")
                else:
                    flash("Error Uploading Address book","Error")
            case "dnis_review":
                switch_statement = g.data_model.ExportDnisSwitch()
                if not g.data_model.errors:
                    flash(switch_statement.replace('\n', '<br>'),"Information")
                    return render_template('deployment.html')

                else:
                    flash("Errors identified in building DNIS entries:<br>" + "<br>".join(g.data_model.errors),"Warning")
                    return render_template('deployment.html')
            case "dnis_upload":
                project = local.db.SelectFirst("project","*",{"id" :  g.data_model.project_id })
                key  = project['user_key']
                secret = project['user_secret']
                client = local.cxone.CxOne(key,secret)
                if client.Connect():
                    script = client.GetScript("PROD\\CustomEvents_PROD")
                    #Convert script to JSON 
                    #script_json = json.loads(script)
                    #node_id = None
                    #dnis_value = None
                    #for action in script_json['scriptContent']['actions']:
                    #    if action['label'] == 'DNIS Switch':
                    #        node_id = action['actionId']
                    #        break
                    #if node_id:
                    #    dnis_content = script_json['scriptContent']['properties'][node_id][0]['value']
                    #    new_content = g.data_model.ExportDnisSwitch()
                    #    updated_content = script.left(0, dnis_content.find('//****START')) + new_content + script.right(dnis_content.find('//****END'))
                    #    client.UploadItem("PROD\\CustomEvents_PROD",updated_content)
                    #Enumerate throught the JSON object for scriptContent.actions to find the node with the label == 'DNIS Switch' - set the nodeId = that node.actionId
                    #Find the node scriptContent.properties[actionId][0].value - this is a string
                    #Update value and replace contecnts beteen '//****START' and '//****END' with value from g.data_model.ExportDnisSwitch()

                    start_index = script.find('//****DNIS_START')
                    end_index = script.find('//****DNIS_END')
                    if start_index > 0 and end_index > 0:  
                        new_content = g.data_model.ExportDnisSwitch()
                        updated_content = script[0:start_index] + new_content + script[end_index:]
                        client.UploadItem("PROD\\CustomEvents_PROD",updated_content)
                    else:
                        flash("Unable to update content in DNIS switch - this must contain a DNIS switch with the //****DNIS_START and //****DNIS_END lines, this may be a non-compliant script","Error")
                    return render_template('deployment.html')
                else:
                    flash("Error connecting to CXOne","Error")

            case "queue_review":
                queue_statement = g.data_model.ExportQueueSwitch()
                if not g.data_model.errors:
                    flash(queue_statement.replace('\n', '<br>'),"Information")
                    return render_template('deployment.html')
                else:
                    flash("Errors identified in building Queues:<br>" + "<br>".join(g.data_model.errors),"Warning")
                    return render_template('deployment.html')
            
            case "queue_upload":
                project = local.db.SelectFirst("project","*",{"id" :  g.data_model.project_id })
                key  = project['user_key']
                secret = project['user_secret']
                client = local.cxone.CxOne(key,secret)
                if client.Connect():
                    script = client.GetScript("PROD\\CustomEvents_PROD")
                    start_index = script.find('//****QUEUE_START')
                    end_index = script.find('//****QUEUE_END')
                    if start_index > 0 and end_index > 0:  
                        new_content = g.data_model.ExportDnisSwitch()
                        updated_content = script[0:start_index] + new_content + script[end_index:]
                        client.UploadItem("PROD\\CustomEvents_PROD",updated_content)
                    else:
                        flash("Unable to update content in Queue switch - this must contain a Queue switch with the //****QUEUE_START and //****QUEUE_END lines, this may be a non-compliant script","Error")
                    return render_template('deployment.html')
                else:
                    flash("Error connecting to CXOne","Error")

            
            case _:
                flash("We haven't got that working yet","Information")

        return render_template('deployment.html')

    #Must be a standard GET request
    if not g.data_model.IsValidated("connection"):
        flash("You have not verified your project connection to the business unit recently - please validate before continuing","Information")
    return render_template('deployment.html')


def read_data_list(file_stream):
    """Helper function to read tsv and build a list of dict for eack line"""
    headers = str(file_stream.readline()).strip().split('\t')
    # Read the remaining lines
    data_list = []
    for line in file_stream.readlines():
        values = line.strip().split('\t')
        #Supported column names here:
        #https://developer.niceincontact.com/API/AdminAPI#/AddressBook/Create%20Address%20Book%20Entries
        data_dict = dict(zip(headers, values))
        data_list.append(data_dict)
    return data_list
