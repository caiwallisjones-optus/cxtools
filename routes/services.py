"""################################################################################
#
#   Author:         Cai Wallis-Jones
#   Description:    Simple async API Endpoints
#   Date:           30/10/24
#
################################################################################"""
from flask import Blueprint, jsonify, g

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

@bp.route('/services/<string:version>/get_queue_actions' , methods=['GET'])
@safe_route
def get_queue_actions(version):
    print(f'GET route get_actions - {version}')
    dm : local.datamodel.DataModel = g.data_model
    params = dm.GetQueueActions()

    if dm:
        return jsonify(params)

    return jsonify({'error': 'Params not found'}), 404

@bp.route('/services/<string:version>/get_params/<string:item_type>' , methods=['GET'])
@safe_route
def get_params(version,item_type):
    print(f'GET route get_params - {version} , {item_type}')
    dm : local.datamodel.DataModel = g.data_model
    params = dm.GetActionParams(item_type)

    if dm:
        return jsonify(params)

    return jsonify({'error': 'Params not found'}), 404
