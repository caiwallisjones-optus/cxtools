"""################################################################################
#
#   Author:         Cai Wallis-Jones
#   Description:    Simple async API Endpoints
#   Date:           30/10/24
#
################################################################################"""
from flask import Blueprint, jsonify, g

import local.datamodel


bp = Blueprint('services_blueprint', __name__)

@bp.route('/services')
def index():
    return 'No valid route found ' , 501

@bp.route('/services/<string:version>/task/<string:task_id>' , methods=['GET'] )
def task(version,task_id):
    print(f'GET route task - {version} , {task_id}')
    dm : local.datamodel.DataModel = g.datamodel
    task_info = dm.GetListFilteredBy("task",{'task_id' : task_id})

    if dm:
        return jsonify(task_info)

    return jsonify({'error': 'Task not found'}), 404


@bp.route('/services/<string:version>/<path:path>')
def services(version,path):
    return f'This is version {version}, path {path}'
