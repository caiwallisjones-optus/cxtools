"""################################################################################
#
#   Author:         Cai Wallis-Jones
#   Description:    Simple async API Endpoints
#   Date:           17/01/24
#
################################################################################"""
import io
import functools
import traceback
from flask import request,flash,Blueprint, g, render_template #jsonify,
import flask_login
import local.datamodel

bp = Blueprint('deployment', __name__)

def safe_route(func):
    """Load data model and initialise with current active project - if user is authenticated"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):

        try:
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)
            print(f"{func.__name__} >> ({signature})")

            if flask_login.current_user.is_authenticated:
                g.active_section = request.endpoint
                g.data_model = local.datamodel.DataModel(flask_login.current_user.id,flask_login.current_user.activeProjectId )
                g.item_selected = None
            else:
                g.data_model = None

            value = func(*args, **kwargs)
            #print(f"{func.__name__}() << {repr(value)}")

            print(f"<< {func.__name__}() <<")
            return value
        except Exception as e:
            print("Exception: ", repr(e))
            traceback.print_exc()
            return render_template('project-list.html')
    return wrapper_debug

@bp.route('/deployment')
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
                        flash(f"Successful connection to {g.data_model.connected_bu_name} ({g.data_model.connected_bu_id}) " &
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
                    return switch_statement.replace('\n', '<br>')
                else:
                    flash("Errors identified in building DNIS entries:<br>" + "<br>".join(g.data_model.errors),"Warning")
            case "queue_review":
                queue_statement = g.data_model.ExportQueueSwitch()
                if not g.data_model.errors:
                    return queue_statement.replace('\n', '<br>')
                else:
                    flash("Errors identified in building Queues:<br>" + "<br>".join(g.data_model.errors),"Warning")
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
