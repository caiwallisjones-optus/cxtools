"""################################################################################
#
#   Author:         Cai Wallis-Jones
#   Description:    Simple async API Endpoints
#   Date:           30/10/24
#
################################################################################"""
from flask import Blueprint, jsonify, g, request

import local.datamodel
from routes.common import safe_route
from app import socketio

bp = Blueprint('services_blueprint', __name__)



@bp.route('/services')
def index() -> tuple :
    """Used this route to check that the services are up

    Returns: HTTP 501"""
    return 'No valid route found ' , 501

@bp.route('/services/<string:version>/<path:path>')
def services(version :str ,path :str ) -> tuple:
    """Simple echo function

    Returns: This is version {version}, path {path}, 200"""
    return f'This is version {version}, path {path}' , 200

@bp.route('/services/<string:version>/task/<string:task_id>' , methods=['GET'] )
def task(version : str,task_id : str ) -> str:
    """Not in use

    Return: List of dict as json string """
    print(f'GET route task - {version} , {task_id}')
    dm : local.datamodel.DataModel = g.data_model
    task_info = dm.db_get_list_filtered("task",{'task_id' : task_id})

    if dm:
        return jsonify(task_info)

    return jsonify({'error': 'Task not found'}), 404


@bp.route('/services/<string:version>/get_queue_action_options' , methods=['GET'])
@safe_route
def get_queue_actions(version :str) -> str:
    """Get a list of the queue actions for a dropdown as name|description
    
    Return: List of dict as json string """
    print(f'GET route get_actions - {version}')
    dm : local.datamodel.DataModel = g.data_model
    params = dm.get_script_queue_actions()

    if dm:
        return jsonify(params)

    return jsonify({'error': 'Params not found'}), 404

@bp.route('/services/<string:version>/get_hoo_action_options' , methods=['GET'])
@safe_route
def get_hoo_actions(version:str ) -> str :
    """Get a list of the hoo actions for a dropdown as name|description
    
    Return: List of dict as json string """
    print(f'GET route get_actions - {version}')
    dm : local.datamodel.DataModel = g.data_model
    params = dm.get_script_hoo_actions()

    if dm:
        return jsonify(params)

    return jsonify({'error': 'Params not found'}), 404


@bp.route('/services/<string:version>/get_params/<string:item_type>' , methods=['GET'])
@safe_route
def get_params(version,item_type):
    """Get a list of the paramters that an actions will accept"""
    print(f'GET route get_params - {version} , {item_type}')
    dm : local.datamodel.DataModel = g.data_model
    params = dm.get_script_action_params(item_type)

    if dm:
        return jsonify(params)

    return jsonify({'error': 'Params not found'}), 404

@bp.route('/services/<string:version>/get_item/<string:item_type>/<string:item_id>' , methods=['GET'])
@safe_route
def get_action(version, item_type, item_id):
    """Get item (queueaction only at this time) as dictionary for the item type and item id"""
    print(f'GET route get_action - {version}')
    dm : local.datamodel.DataModel = g.data_model
    #Get auth tokem
    token = request.headers.get('Authorization')
    print(f"Token is {token}")
    if dm:
        match item_type:
            case "queueaction":
                action = dm.db_get_item("queueaction",item_id)
                return jsonify(action)
            case "audio_by_name":
                audio = dm.db_get_list_filtered("audio",  {"project_id" : dm.project_id, "name": item_id})
                if audio:
                    return jsonify(audio[0])
            case _:
                action = dm.db_get_item("item_type",item_id)
                return jsonify(action)

    return jsonify({'error': 'Action not found'}), 404

@bp.route('/services/audio/query' , methods=['GET'])  # Fixed route path
@safe_route
def query_audio():
    audio_name = request.args.get('name')
    dm : local.datamodel.DataModel = g.data_model

    audio = dm.db_get_list_filtered("audio",  {"project_id" : dm.project_id, "name": audio_name})
    if audio:
        return jsonify(audio[0])
    return jsonify({"error": "Audio not found"}), 404

@bp.route('/services/audio/update' , methods=['PUT'])
@safe_route
def update_audio():
    data = request.json
    audio_name = data.get('name')
    new_utterance = data.get('utterance')
    if local.db.update("audio", {"description": new_utterance, "isSynced" : 0}, {"name": audio_name}):
        return jsonify({"success": True})
    return jsonify({"error": "Failed to update audio"}), 400


@bp.route('/services/<string:version>/log/<string:correlation_key>/<string:log_level>/<string:log_type>', methods=['POST'])
def log(version, correlation_key:str, log_level :str, log_type :str):
    """Log a line of text to the log file"""
    print(f'GET route log - {version} , {log_level} , {log_type}')
    try:
        data = request.get_json()
        print(f'JSON data: {data}')

        if log_type.upper() == "LINE":
            socketio.emit('LINE', {'log_line' : data['line'] }, room='log')
        else:
            socketio.emit('DATA', data, room='log')

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"status" : "error", "message" : f"Log not sent to socket {repr(e)}"}),500

    return jsonify({"status" : "success", "message" : "Log sent to socket"}),200
