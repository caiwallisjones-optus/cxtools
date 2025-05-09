"""################################################################################
#   Author:         Cai Wallis-Jones
################################################################################"""
from flask import request,flash,Blueprint, g, render_template #Response #jsonify,

#from local import logger
import local.datamodel
from routes.common import safe_route

bp = Blueprint('admin', __name__)

@bp.route('/admin',  methods = ['GET', 'POST'])
@safe_route
def admin():
    """Route all admin requests"""
    dm : local.datamodel.DataModel = g.data_model
    if request.method == 'POST':
        action = request.form['action'] # get the value of the clicked button
        match action:
            case str() if action.startswith('item_'):
                return item_action(action)
            case 'create':
                g.item_selected = None
                return render_template('admin-item.html')
            case 'edit':
                g.item_selected = request.form['id']
                return render_template('admin-item.html')
            case 'delete':
                dm.db_delete("user",request.form['id'])


    #Default response
    return render_template('admin-list.html')

def item_action(action):
    """Route all item requests""" 
    dm : local.datamodel.DataModel = g.data_model

    match action:
        case 'item_create':
            name = request.form['username']
            password = request.form['password']

            if not dm.AddNewIfNoneAdmin("user","username", { "username": name, "password" : password }):
                flash("Username already exists - please use a unique name","Error")
                return render_template('admin-item.html')
        case 'item_update':
            item_id = request.form['id']
            values = g.data_model.request_paramlist(request)
            dm.db_update("user",item_id,values)
        case _:
            pass
    return render_template('admin-list.html')
