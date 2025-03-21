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


bp = Blueprint('services_blueprint', __name__)

@bp.route('/services')
def index():
    return 'No valid route found ' , 501

@bp.route('/services/<string:version>/<path:path>')
def services(version,path):
    return f'This is version {version}, path {path}'

@bp.route('/services/<string:version>/task/<string:task_id>' , methods=['GET'] )
def task(version,task_id):
    print(f'GET route task - {version} , {task_id}')
    dm : local.datamodel.DataModel = g.data_model
    task_info = dm.GetListFilteredBy("task",{'task_id' : task_id})

    if dm:
        return jsonify(task_info)

    return jsonify({'error': 'Task not found'}), 404


@bp.route('/services/<string:version>/get_queue_action_options' , methods=['GET'])
@safe_route
def get_queue_actions(version):
    """Get a list of the queue actions for a dropdown as name|description"""
    print(f'GET route get_actions - {version}')
    dm : local.datamodel.DataModel = g.data_model
    params = dm.GetQueueActions()

    if dm:
        return jsonify(params)

    return jsonify({'error': 'Params not found'}), 404

@bp.route('/services/<string:version>/get_hoo_action_options' , methods=['GET'])
@safe_route
def get_hoo_actions(version):
    """Get a list of the hoo actions for a dropdown as name|description"""
    print(f'GET route get_actions - {version}')
    dm : local.datamodel.DataModel = g.data_model
    params = dm.GetHooActions()

    if dm:
        return jsonify(params)

    return jsonify({'error': 'Params not found'}), 404


@bp.route('/services/<string:version>/get_params/<string:item_type>' , methods=['GET'])
@safe_route
def get_params(version,item_type):
    """Get a list of the paramters that an actions will accept"""
    print(f'GET route get_params - {version} , {item_type}')
    dm : local.datamodel.DataModel = g.data_model
    params = dm.GetActionParams(item_type)

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
        action = dm.GetItem("queueaction",item_id)
        return jsonify(action)

    return jsonify({'error': 'Action not found'}), 404

@bp.route('/services/<string:version>/log/<string:correlation_key>/<string:log_level>/<string:log_line>' , methods=['POST'])
@safe_route
def log(version, correlation_key, log_level, log_line):
    """Log a line of text to the log file"""
    print(f'GET route log - {version} , {log_level} , {log_line}')
    dm : local.datamodel.DataModel = g.data_model
    if dm:
        #dm.Log(correlation_key, log_level, log_line)
        return jsonify({'status': 'Logged'})

    return jsonify({'error': 'Log not found'}), 404
