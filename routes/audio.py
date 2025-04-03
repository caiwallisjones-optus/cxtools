"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    
#   Date:           17/01/24
################################################################################"""
from io import BytesIO
import logging
from flask import request,flash,Blueprint, g, render_template,Response #jsonify,
from routes.common import safe_route

import local.datamodel


# Get the main logger
logger = logging.getLogger("cxtools")

bp = Blueprint('audio', __name__)

@bp.route('/audio',  methods = ['GET', 'POST'])
@safe_route
def audio():
    """Route all audio requests"""
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        #Audio-List
        if action == 'create':
            return render_template('audio-item.html')

        if action.startswith("download"):
            file_id = request.form['id'] # get the value of the item associated with the button
            file = local.db.select_first("audio","*",{ "id" : file_id})

            logger.info("Request for text to speech with a filename= %s", file['name'])
            try:
                sub_key = local.db.get_setting("tts_key")
                voice_font = "en-AU-NatashaNeural"

                tts : local.tts.Speech = local.tts.Speech(sub_key)
                tts.get_token()
                audio_response = tts.get_audio(file['description'], voice_font)
                logger.info("TTS file length %s" , len(audio_response) )

                with BytesIO(audio_response) as output:
                    output.seek(0)
                    filename : str = file['name']
                    if not filename.endswith(".wav"):
                        filename = filename + ".wav"
                    headers = {"Content-disposition": f"attachment; filename={filename}" }
                    return Response(output.read(), mimetype='audio/wav', headers=headers)
            except Exception as e:
                logger.info("Error: %s", e)
            flash("Unable to connect API", "Error")

        if action == 'import_list':
            flash("Import feature is not implemented yet","Information")

        if action == 'display_system_files':
            g.item_selected = "All"
            return render_template('audio-list.html')

        if action == 'edit':
            g.item_selected = request.form['id'] # get the value of the item associated with the button
            return render_template('audio-item.html')

        if action == 'delete':
            item_selected = request.form['id']
            local.db.delete("audio",{ "id" : item_selected})

        #Audio-Item
        if action == 'item_update':
            file_id = request.form['id']
            file_name = request.form['name']
            wording = request.form['description']
            if local.db.update("audio",{ "name" : file_name, "description" : wording , "isSynced" : False},{ "id" : file_id }):
                return render_template('audio-list.html')
            else:
                flash("Error updating audio","Error")
                g.item_selected = file_id
                return render_template('audio-item.html')

        if action == 'item_create':
            file_name = request.form['name']
            description = request.form['description']
            if not g.data_model.AddNewIfNone("audio",file_name,description):
                flash("File name already exists - please use a unique filename","Error")
                return render_template('audio-item.html')

            return render_template('audio-list.html')

    #Default response
    return render_template('audio-list.html')
