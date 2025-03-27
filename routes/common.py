"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Common utils used my mutiple routes
#   Date:           17/01/24
################################################################################"""
import functools
import traceback
import flask_login
from flask import g,request,render_template

import local.datamodel

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
                g.data_model = local.datamodel.DataModel(flask_login.current_user.id,flask_login.current_user.active_project )
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
