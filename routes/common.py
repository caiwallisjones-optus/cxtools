"""################################################################################
#   Author:         Cai Wallis-Jones
#   Description:    Common utils used my mutiple routes
#   Date:           17/01/24
################################################################################"""
import functools
import logging
import traceback
import flask_login
from flask import g,request,render_template, flash, redirect

import local.datamodel
from local import logger

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
                g.data_model = local.datamodel.DataModel(flask_login.current_user.id,flask_login.current_user.active_project )
                g.item_selected = None
            else:
                g.data_model = None
                flash("You have been logged out - please log in again","Information")
                logger.info("User is not authenticated")
                logger.info("<< %s << redirected to login", func.__name__)
                return redirect('/login')

            value = func(*args, **kwargs)

            logger.info("<< %s", func.__name__)
            return value
        except Exception as e:
            logger.error("Uncaught exception: %s ", repr(e))
            logger.error("%s",traceback.print_exc())

            flash(f"Please provide details to support: {repr(e)} ","Uncaught error in application")
            logger.info("<< %s", func.__name__)
            return redirect('/project')

    return wrapper_debug


def unsafe_route(func):
    """We are not authenticating before we display the page - this is mainly for logging"""
    @functools.wraps(func)
    def wrapper_debug(*args, **kwargs):

        try:
            args_repr = [repr(a) for a in args]
            kwargs_repr = [f"{k}={repr(v)}" for k, v in kwargs.items()]
            signature = ", ".join(args_repr + kwargs_repr)

            logger.info("%s >> %s (not authenticated)" ,func.__name__ , signature)

            g.active_section = request.endpoint
            g.data_model = local.datamodel.DataModel(-1,-1 )

            logger.info("<< %s", func.__name__)
            value = func(*args, **kwargs)

            logger.info("<< %s", func.__name__)
            return value
        except Exception as e:
            logger.error("Uncaught exception: %s ", repr(e))
            logger.error("%s",traceback.print_exc())

            flash(f"Please provide details to support: {repr(e)} ","Uncaught error in application")
            logger.info("<< %s", func.__name__)
            return redirect('/project')
    return wrapper_debug
