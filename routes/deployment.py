"""################################################################################
#
#   Author:         Cai Wallis-Jones
#   Description:    Simple async API Endpoints
#   Date:           17/01/24
#
################################################################################"""
import io
import json
from flask import request,flash,Blueprint, g, render_template #jsonify,
from markupsafe import Markup
from routes import logger
from routes.common import safe_route
import local.cxone


bp = Blueprint('deployment', __name__)


@bp.route('/deployment',  methods = ['GET', 'POST'])
@safe_route
def deployment():
    """General deployment process"""

    dm : local.datamodel.DataModel = g.data_model
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        client = None
        match action:
            case "bu_check":
                try:
                    g.data_model.validate_connection()
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
                if g.data_model.validate_package():
                    flash("No duplicate scripts identified - package can be deployed","Information")
                else:
                    flash("Duplicate files located on remote server - these scripts be overwritten if you deploy:<br>" +
                            "<br>".join(g.data_model.errors),"Warning")
            case "package_upload":
                if g.data_model.upload_package():
                    flash("Package base scripts uploaded","Information")
                else: flash("Something went wrong:<br>" + "<br>".join(g.data_model.errors),"Error")
            case "audio_validate":
                if g.data_model.validate_audio():
                    flash("No duplicate audio files located","Information")
                else:
                    flash("Audio files already exist in in destination - uploading will overwrite them" + "<br>".join(g.data_model.errors),"Warning")
            case "audio_upload":
                if g.data_model.upload_audio_package():
                    flash("Audio has been created and uploaded","Information")
                else:
                    flash("Something went wrong : " + "<br>".join(g.data_model.errors),"Error")
            case "hoo_validate":
                if g.data_model.validate_hoo_config():
                    flash("All existing HOO have been linked and new HOO can be deployed to BU","Information")
                else:
                    flash("Review potential issues before deploying" + "<br>".join(g.data_model.errors),"Warning")
            case "hoo_upload":
                if g.data_model.upload_hoo():
                    flash("HOO have been created and uploaded","Information")
                    g.data_model.upload_hoo()
                else:
                    flash("Something went wrong : " + "<br>".join(g.data_model.errors),"Error")
                    g.data_model.validate_hoo_config()
            case "skills_validate":
                if g.data_model.validate_skills_config():
                    flash("No skills in BU that would be overwritten by this implentation","Information")
                else:
                    flash("Review potential issues before deploying" + "<br>".join(g.data_model.errors),"Warning")
            case "skills_upload":
                if g.data_model.upload_skills():
                    flash("Skills have been created and uploaded","Information")
                    g.data_model.validate_skills_config()
                else:
                    flash("Something went wrong : " + "<br>".join(g.data_model.errors),"Error")
                    g.data_model.validate_skills_config()
            case "addressbook_upload":
                file = request.files['addressbook_file']
                address_name = request.form.get('addressbook_name')
                file.stream.seek(0)
                wrapper = io.TextIOWrapper(file.stream,  encoding="utf-8", )
                data_list = read_data_list(wrapper)

                client = None
                if client is not None and (client.is_connected() is True):
                    client.create_address_book(address_name,{ "addressBookEntries" : data_list})
                    flash("Address book uploaded","Information")
                else:
                    flash("Error Uploading Address book","Error")
            case "dnis_review":
                switch_statement = g.data_model.export_dnis_switch().replace(' ','&nbsp;').replace('\\r\\n','\n').replace('\\t','    ').replace('\\"','"')
                if not g.data_model.errors:
                    logger.info("DNIS review - errors found %s", g.data_model.errors)
                    flash(Markup(f"Review the data below and deploy or copy to CustomEvents - DNIS Switch:<br><br> <pre>{switch_statement}</pre>")
                          ,"Information")
                    return render_template('deployment.html')

                else:
                    flash("Errors identified in building DNIS entries:<br>" + "<br>".join(g.data_model.errors),"Warning")
                    flash(Markup(f"Review the data below and deploy or copy to CustomEvents - DNIS Switch:<br><br> <pre>{switch_statement}</pre>")
                          ,"Information")
                    return render_template('deployment.html')

            case "dnis_upload":
                project = dm.db_get_item("project",g.data_model.project_id)
                key  = project['user_key']
                secret = project['user_secret']
                client = local.cxone.CxOne(key,secret)
                if client.is_connected():
                    script = client.get_script(f"{project['instance_name']}\\CustomEvents_PROD")
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
                    #    new_content = g.data_model.export_dnis_switch()
                    #    updated_content = script.left(0, dnis_content.find('//****START')) + new_content + script.right(dnis_content.find('//****END'))
                    #    client.upload_file("PROD\\CustomEvents_PROD",updated_content)
                    #Enumerate throught the JSON object for scriptContent.actions to find the node with the
                    # label == 'DNIS Switch' - set the nodeId = that node.actionId
                    #Find the node scriptContent.properties[actionId][0].value - this is a string
                    #Update value and replace contecnts beteen '//****START' and '//****END' with value from g.data_model.export_dnis_switch()
                    data = json.loads(script)
                    data['schemaVersion']=  "1.0.0"
                    final_json = { "scriptContent" : data}
                    for  key, node in final_json['scriptContent']['actions'].items():
                        node['xws'] = node['x']
                        node['yws'] = node['y']
                    result = json.dumps(final_json,indent=1)
                    #with open('c:/temp/infile.json','wb') as f:
                    #    f.write(byte_string)

                    start_index = result.find('//****DNIS_START\\r\\n') + len('//****DNIS_START\\r\\n')
                    end_index = result.find('//****DNIS_END\\r\\n')
                    if start_index > 0 and end_index > 0:
                        new_content = g.data_model.export_dnis_switch()
                        updated_content = result[0:start_index] + new_content + result[end_index:]
                        byte_string = updated_content.encode('utf-8')
                        byte_string = byte_string.replace(b'\x0D\x0A',b'\x0A')
                        response = client.upload_script("",byte_string)
                        if response == 206:
                            flash("DNIS switch updated","Information")
                        else:
                            flash(f"Check if the info completed - we got {response} " +
                                  "//****QUEUE_START and //****QUEUE_END lines, this may be a non-compliant script","Error")
                    return render_template('deployment.html')
                else:
                    flash("Error connecting to CXOne","Error")

            case "dnis_table":
                #Get list of call flows from the data model
                return render_template('deployment-table.html', items = g.data_model.get_dnis_tables())

            case "queue_table":
                #Get list of queues from the data model
                return render_template('deployment-table.html', items = g.data_model.get_queue_tables())

            case "queue_review":
                queue_statement = g.data_model.export_queue_switch().replace(' ','&nbsp;').replace('\\r\\n','\n').replace('\\t','    ').replace('\\"','"')
                if not g.data_model.errors:
                    flash(Markup(f"<pre>{queue_statement}</pre>"),"Information")
                    return render_template('deployment.html')
                else:
                    flash("Errors identified in building Queues:<br>" + "<br>".join(g.data_model.errors),"Warning")
                    flash(Markup(f"Review the data below and deploy or copy to CustomEvents - Queue :<br><br> <pre>{queue_statement}</pre>"),"Information")
                    return render_template('deployment.html')

            case "queue_upload":
                project = dm.db_get_item("project",g.data_model.project_id)
                key  = project['user_key']
                secret = project['user_secret']
                client = local.cxone.CxOne(key,secret)
                if client.is_connected():
                    script = client.get_script(f"{project['instance_name']}\\CustomEvents_PROD")

                    data = json.loads(script)
                    data['schemaVersion']=  "1.0.0"
                    final_json = { "scriptContent" : data}
                    for  key, node in final_json['scriptContent']['actions'].items():
                        node['xws'] = node['x']
                        node['yws'] = node['y']
                    result = json.dumps(final_json,indent=1)
                    start_index = result.find('//****QUEUE_START\\r\\n') + len('////****QUEUE_START\\r\\n')
                    end_index = result.find('//****QUEUE_END\\r\\n')
                    if start_index > 0 and end_index > 0:
                        logger.info("located place in script to replace queue switch")
                        new_content = g.data_model.export_queue_switch()
                        logger.info("New content to be inserted %s", new_content)
                        updated_content = result[0:start_index] + new_content + result[end_index:]
                        byte_string = updated_content.encode('utf-8')
                        byte_string = byte_string.replace(b'\x0D\x0A',b'\x0A')
                        response = client.upload_script("",byte_string)
                        logger.info("Response from CXOne %s", response)
                        if response == 206:
                            flash("Queue switch updated","Information")
                        else:
                            flash(f"Check if the info completed - we got {response} " +
                                  "//****QUEUE_START and //****QUEUE_END lines, this may be a non-compliant script","Error")
                    return render_template('deployment.html')
                else:
                    flash("Error connecting to CXOne","Error")
            case _:
                flash("We haven't got that working yet","Information")

        return render_template('deployment.html')

    #Must be a standard GET request
    if not g.data_model.package_validated("connection"):
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
