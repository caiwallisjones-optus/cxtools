"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Common utils used my mutiple routes
#   Date:           17/01/24
################################################################################"""
import functools
import logging
import traceback
import flask_login
from flask import g,request,render_template
from local.datamodel import DataModel

logger = logging.getLogger("cxtools")

def safe_route(func):
    """Load data model and initialise with current active project - if user is authenticated"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):

        try:
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)

            logger.info("%s >> %s" ,func.__name__ , signature)

            if flask_login.current_user.is_authenticated:
                g.active_section = request.endpoint
                g.data_model: DataModel = DataModel(flask_login.current_user.id,flask_login.current_user.active_project ) # type: ignore # type: DataModel
                g.item_selected = None
            else:
                g.data_model = None

            value = func(*args, **kwargs)
            #print(f"{func.__name__}() << {repr(value)}")

            logger.info("<< %s", func.__name__)
            return value
        except Exception as e:
            logger.error("Uncaught exception: %s ", repr(e))
            logger.error("%s",traceback.print_exc())

            return render_template('project-list.html')
    return wrapper_debug
