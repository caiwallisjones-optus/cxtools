import sqlite3
import os
import platform
import shutil

from datetime import datetime, timedelta
from flask import g
from local import logger


dbname = "application.sql3lite"

def __build_select_query(table_name :str, params : dict , filter_params : dict ) -> str:
    #SELECT * FROM table WHERE
    query = "SELECT "
    for param in params:
        query = query + param + ","
    query = query[:-1] + " FROM " + table_name + " WHERE "
    for key in filter_params:
        query = query + key + " = ? AND "
    query = query[:-4]
    return  query

def __build_update_query(table_name :str, params : dict, filter_params : dict) -> str:
    #"UPDATE user SET activeproject = ? WHERE id = ?"
    query = "UPDATE " + table_name + " SET "
    for key in params:
        query = query + key + " = ?,"
    query = query[:-1] + " WHERE "
    for key in filter_params:
        query = query + key + " = ? AND "
    query = query[:-4]
    return  query

def __build_insert_query(table_name :str, params : dict ) -> str:
    #"UPDATE user SET activeproject = ? WHERE id = ?"
    query = "INSERT INTO " + table_name + " ("
    for key in params:
        query = query + key + ","
    query = query[:-1] + " ) VALUES ( "
    for key in params:
        query = query + " ?,"
    query = query[:-1] + ")"
    return  query

def __build_delete_query(table_name :str, filter_params) -> str:
    # project = db.execute("DELETE FROM callFlow WHERE id = ?", (callFlow_id,))
    query = "DELETE FROM " + table_name + " WHERE "
    for key in filter_params:
        query = query + key + " = ? AND "
    query = query[:-4]
    return  query

def __as_dictionary(result):
    data_list = []
    for row in result:
        row_dict = dict()
        i = 0
        for column in row:
            row_dict[result.description[i][0]] = column
            i = i + 1
        data_list.append(row_dict)
    return data_list

def __admin_execute_sql(script_name :str ):
    #backup file
    logger.info("Backing up database")
    destinationfile = dbname.replace(".sql3lite",f"{datetime.now().strftime("%Y_%m_%d_%H_%M")}.sql3lite")
    shutil.copyfile(dbname,destinationfile)
    print("Executing SQL Script")
    db = __connect_to_db()
    filename = f".//local//{script_name}"
    if not os.path.isfile(filename):
        print("Filename invalid:  %s ", filename)
    else:
        print("Filename %s" , filename)
        f = open(filename, "r", encoding="UTF-8")
        print("Executing SQL Script")
        try:
            result = db.executescript(f.read())
            print("Script executed ")
            print(repr(result))
        except Exception as e:
            print("Error executing script %s - %s" ,filename, e)

def __admin_execute_sql_from_string(script :str ):
    print("Executing SQL query ", script)
    db = __connect_to_db()
    print("Executing SQL Script")
    result = db.execute(script)
    results = result.fetchall()
    for row in results:
        print(row)

def __admin_backup_db():
    destination_file = dbname.replace(".sql3lite",f".{datetime.now().strftime("%Y_%m_%d_%H_%M")}")

    if platform.system() != "Windows":
        logger.info("Detected Linux environment - looking for DB in /home")
        if os.path.isfile("//home//" + dbname):
            logger.info("Backing up database")
            destination_file = "//home//" + dbname.replace(".sql3lite",f".{datetime.now().strftime("%Y_%m_%d_%H_%M")}_sql3lite")
        else:
            logger.info("ERROR: Unable to locate original file")
    else:
        logger.info("Detected windows environement - using local dbname and directory")

    logger.info("Backing up to %s", destination_file)
    shutil.copyfile(dbname,destination_file)

def __connect_to_db():
    """Used by admin functions to connect to the database - outside of the normal Flask context"""
    logger.info("__connect_to_db")
    if platform.system() != "Windows":
        logger.info("Detected Linux environment - looking for DB in /home")
        if os.path.isfile("//home//" + dbname):
            logger.info("Connecting to existing DB in home dir")
            db = sqlite3.connect("//home//" + dbname)
            #logger.info(f"Detected version {GetSetting("version")}")
            return db
        else:
            logger.info("Creating new database from schema...")
            db = sqlite3.connect(dbname)
            f = open(".//local//schema.sql", "r", encoding="UTF-8")
            db.executescript(f.read())
            #logger.info(f"Detected version {GetSetting("version")}")
            return db
    else:
        db = sqlite3.connect(dbname)
        #logger.info(f"Detected version {GetSetting("version")}")
        return db

#Create / Connect to DB to ensure active DB ready
def init_db():
    logger.info("init_db")
    if platform.system() != "Windows":
        logger.info("Init DB")
        if os.path.isfile("//home//" + dbname):
            logger.info("Connecting to existing DB in home dir")
            db = sqlite3.connect("//home//" + dbname)
            return True
        
        db = sqlite3.connect("//home//" + dbname)
        logger.info("Creating new database from schema...")
        f = open(".//local//schema.sql", "r")
        db.executescript(f.read())
        logger.info("Created")
        return True
    else:
        logger.info("Detected windows")
        #Does the DB exist already
        if os.path.isfile(dbname):
            logger.info("Connecting to existing DB")
            db = sqlite3.connect(dbname)
            return True

        db = sqlite3.connect(dbname)
        logger.info("Creating new database from schema...")
        f = open(".//local//schema.sql", "r")
        db.executescript(f.read())
        return True

    return False

def create_db():
    logger.info("create_db")
    if platform.system() != "Windows":
        logger.info("Detected Linux")
        if os.path.isfile("//home//" + dbname):
            os.remove("//home//" + dbname)
            f = open(".//local//schema.sql", "r")
            db = sqlite3.connect("//home//" + dbname)
            db.executescript(f.read())
            return True
        
    logger.info("Detected windows- we dont have to do anything here")
    return False

def get_db():
    #logger.DEBUG("get_db")
    try:
        if platform.system() != "Windows":
            if "db" not in g:
                g.db = sqlite3.connect("//home//" + dbname)
            else:
                return g.db
        else:
            if "db" not in g:
                g.db = sqlite3.connect(dbname)
            else:
                return g.db
        return g.db
    except Exception as e:
        logger.critical("FATAL: Error opening database %s " , e)

def select_query(query: str) -> str:
    db = get_db()
    result = db.execute(query)
    return __as_dictionary(result)

def select(table_name : str ,fields : list ,filter_paramaters : dict) -> list :
    query = __build_select_query(table_name,fields,filter_paramaters)
    query_params = (tuple(filter_paramaters.values()))
    db = get_db()
    result = db.execute(query, query_params)
    return __as_dictionary(result)  

def select_first(table_name : str ,fields : list ,filter_paramaters : dict) -> dict:
    result =  select(table_name ,fields ,filter_paramaters)
    if len(result) == 0:
        return dict()
    return result[0]

def insert(table_name : str ,field_values : dict):

    query = __build_insert_query(table_name,field_values)
    query_params = (tuple(field_values.values()))
    db = get_db()
    result = db.execute(query, query_params)
    db.commit()
    return result.lastrowid

def update(table_name: str, field_values : dict , filter_paramaters : dict) -> str:
    query = __build_update_query(table_name,field_values,filter_paramaters)
    query_params = (tuple(field_values.values()) + tuple(filter_paramaters.values()))
    db = get_db()
    result = db.execute(query, query_params)
    db.commit()
    return result

def delete(table_name : str, filter_paramaters :dict) -> bool:
    query = __build_delete_query(table_name, filter_paramaters)
    query_params = (tuple(filter_paramaters.values()))
    db = get_db()
    result = db.execute(query, query_params)
    db.commit()
    return result

#Config settings
def add_setting(key, value):
    logger.info(">> add_setting")
    db = get_db()
    db.execute("INSERT INTO config (key,value) VALUES (?, ?)",(key,value,))
    db.commit()
    return "OK"

def get_setting(key):
    logger.info(">> get_setting")
    db = get_db()
    result = db.execute("SELECT value FROM config WHERE key = ?",(key,)).fetchone()[0]
    db.commit()
    return result

def AddUser(username,password):
    logger.info("AddUser")
    db = get_db()
    db.execute("INSERT INTO User (username,password) VALUES (?, ?)",(username,password))
    db.commit()
    return "OK"

#CallFlow
def GetCallFlowList(project_id):
    logger.info("GetCallFlowList %s", project_id )
    db = get_db()
    result = db.execute("SELECT * FROM callFlow WHERE project_id = ?", (project_id)).fetchall()
    for row in result:
        logger.info(row)
    return result

def GetCallFlow(item_id):
    logger.info("GetCallFlow %s" , id )
    db = get_db()
    result = db.execute("SELECT * FROM callFlow WHERE id = ?", (item_id,)).fetchone()
    logger.info(result)
    return result

def AddCallFlow(project_id,name,description,actions_root_id = None):
    logger.info("AddCallFlow %s" , project_id )
    db = get_db()
    result = db.execute("INSERT INTO callFlow (project_id,name,description,callFlowAction_id ) \
               VALUES (?, ?, ?, ?)",
               (project_id,name,description,actions_root_id))
    logger.info(result)
    db.commit()
    inserted_id = result.lastrowid
    #We will return the ID of the created object
    return str(inserted_id)

#Call flow Actions
def GetCallFlowAction(action_id):
    logger.info("GetCallFlowAction %s" , action_id )
    db = get_db()
    result = db.execute("SELECT * FROM callFlowAction WHERE id = ?", (action_id,)).fetchone()
    logger.info(result)
    return result

def UpdateCallFlow(params: dict , filter_parms : dict):
    db = get_db()
    query = __build_update_query("callFlow",params,filter_parms)
    query_params = (tuple(params.values()) + tuple(filter_parms.values()))
    result = db.execute(query, query_params)
    db.commit()
    inserted_id = result.lastrowid
    #We will return the ID of the created object
    return str(inserted_id)

def DeleteCallFlow(callFlow_id):
    db = get_db()
    db.execute("DELETE FROM callFlow WHERE id = ?", (callFlow_id,))
    #for row in project:
    #    logger.info(row)
    db.commit()
    return "OK"

#Call flow action
def AddCallFlowAction(callflow_id,parentaction_id,name,action,params):
    logger.info("AddCallFlowAction %s" , callflow_id )
    db = get_db()
    result = db.execute("INSERT INTO callFlowAction (callflow_id,parent_id,name,action,params ) \
               VALUES (?, ?, ?,?,?)",
               (callflow_id,parentaction_id,name,action,params))
    #logger.info(result)
    db.commit()
    inserted_id = result.lastrowid
    #We will return the ID of the created object
    return str(inserted_id)

def UpdateCallFlowAction(params : dict,filter_params : dict ):
    db = get_db()
    query = __build_update_query("callFlowAction",params,filter_params)
    query_params = (tuple(params.values()) + tuple(filter_params.values()))

    result = db.execute(query, query_params)
    db.commit()
    #We will return the ID of the created object
    return str(result.rowcount)


#Call Flow Acation responses
def GetCallFlowActionResponse(action_id):
    logger.info("GetCallFlowActionResponse ")
    db = get_db()
    result = db.execute("SELECT * FROM callFlowResponse WHERE id = ?", (action_id,)).fetchone()
    return result

def GetCallFlowActionResponses(action_item):
    logger.info("GetCallFlowActionResponses ")
    db = get_db()
    result = db.execute("SELECT * FROM callFlowResponse WHERE callFlowAction_id = ?", (action_item,)).fetchall()
    return result

def AddActionResponse(callflow_id : int, action_id : int, action_response : str , next_action_id :int):
    logger.info("AddActionResponse ")
    db = get_db()
    result = db.execute("INSERT INTO callFlowResponse (callFlow_id,callFlowAction_id,response,callFlowNextAction_id ) \
               VALUES (?, ?, ?,?)",
               (callflow_id,action_id,action_response,next_action_id,))
    #logger.info(result)
    db.commit()
    inserted_id = result.lastrowid
    #We will return the ID of the created object
    return str(inserted_id)

def UpdateCallFlowActionResponse(action_response_id,new_action):
    logger.info("UpdateCallFlowActionResponse ")
    db = get_db()
    result = db.execute("Update callFlowResponse SET callFlowNextAction_id = ? WHERE id = ?",
               (new_action,action_response_id,))
    db.commit()
    inserted_id = result.lastrowid
    #We will return the ID of the created object
    return str(inserted_id)

#Queues
def GetQueue(queue_id):
    logger.info("GetQueue %s" , id )
    db = get_db()
    result = db.execute("SELECT * FROM queue WHERE id = ?", (queue_id,)).fetchone()
    logger.info(result)
    return result

def GetQueueList(project_id):
    logger.info("GetQueueList %s", project_id )
    db = get_db()
    result = db.execute("SELECT * FROM queue WHERE project_id = ?", (project_id)).fetchall()
    for row in result:
        logger.info(row)
    return result

def GetQueueItemsList(queue_id):
    logger.info("GetQueueList %s" , queue_id )
    db = get_db()
    result = db.execute("SELECT * FROM queueaction WHERE queue_id = ?", (queue_id)).fetchall()
    for row in result:
        logger.info(row)
    return result

def AddQueue(project_id,queue_name,queue_skills,queue_hoo):
    logger.info("AddQueue %s", project_id )
    db = get_db()
    result = db.execute("INSERT INTO queue (project_id,name,skills, queuehoo ) \
               VALUES (?, ?, ?, ?)",
               (project_id,queue_name,queue_skills,queue_hoo))
    db.commit()
    return result.lastrowid

def UpdateQueue(queue_id,queue_name,queue_skills,queue_hoo):
    logger.info("UpdateQueue %s", queue_id )

    db = get_db()
    db.execute("UPDATE queue SET name = ?, skills = ?, queuehoo = ? \
               WHERE id = ?",
               (queue_name,queue_skills,queue_hoo,queue_id))
    db.commit()
    return "OK"

def UpdateQueueHooActions(queue_id,queue,state,action,params):
    logger.info("UpdateQueueHoo %s", queue_id )
    queueDetails = GetQueue(queue_id)
    queueHooState = state + "," + action + "," + params
    db = get_db()
    if queue == "PREQUEUE":
        column = 5
    else:
        column = 6
    if queueDetails[column] != None:
        if state in queueDetails[column]:
            for hooState in  queueDetails[column].split("|"):
                if state in hooState:
                    #We are overwriting so do nothing
                    pass
                else:
                    #We dont have this one yet - so add it back in
                    queueHooState = queueHooState + "|" + hooState
        else:
            #This is a new state so just add it in
            queueHooState = str(queueDetails[column]) + "|" + queueHooState

    if queue == "PREQUEUE":
        db.execute("UPDATE queue SET prequeehooactions = ? WHERE id = ?", (queueHooState,queue_id))
    else:
        db.execute("UPDATE queue SET queehooactions = ? WHERE id = ?", (queueHooState,queue_id))

    db.commit()
    return True

def DeleteQueueHooAction(queue_id,queue,action_to_remove):
    logger.info("DeleteQueueHooAction %s, %s", queue_id,action_to_remove)
    db = get_db()
    if queue == "PREQUEUE":
        #Get existing HOO states
        queue_details = select_first('queue',"*",{'id' : queue_id})
        actions = queue_details['prequeehooactions'].split("|")
        new_actions = []
        for action in actions:
            if not action.startswith(action_to_remove):
                new_actions.append(action)
        db.execute("UPDATE queue SET prequeehooactions = ? WHERE id = ?", ("| ".join(new_actions),queue_id))
        db.commit()
        return True
    if queue == "QUEUE":
        #Get existing HOO states
        queue_details = select_first('queue',"*",{'id' : queue_id})
        actions = queue_details['queehooactions'].split("|")
        new_actions = []
        for action in actions:
            if not action.startswith(action_to_remove):
                new_actions.append(action)
        db.execute("UPDATE queue SET queehooactions = ? WHERE id = ?", ("|".join(new_actions),queue_id))
        db.commit()
        return True
    return False

def DeleteQueue(queue_id):
    db = get_db()
    db.execute("DELETE FROM queue WHERE id = ?", (queue_id,))
    db.commit()

#Queue Actions
def GetQueueActionsList(queue_id):
    logger.info("GetQueueActionsList %s", queue_id )
    db = get_db()
    result = db.execute("SELECT * FROM queueAction WHERE queue_id = ?", [queue_id]).fetchall()
    for row in result:
        logger.info(row)
    return result

def GetQueueActionStepCount(queue_id):
    logger.info("GetQueueActionStepCount %s", queue_id )
    db = get_db()
    result = db.execute("SELECT COUNT(*) FROM queueaction WHERE queue_id = ?", ([queue_id])).fetchone()[0]
    return int(result)

def AddQueueAction(queue_id,queue_action,params):
    logger.info("AddQueueAction %s, %s, %s" , queue_id,queue_action,params)
    db = get_db()
    db.execute("INSERT INTO queueaction (queue_id,action,param1,param2,step_id) \
               VALUES (?, ?, ?, ?,?)",
               (queue_id,queue_action,params,"",(GetQueueActionStepCount(queue_id)+1)))
    db.commit()
    return "OK"

def GetQueueAction(queue_action_id):
    logger.info("GetQueueAction %s", queue_action_id )
    db = get_db()
    result = db.execute("SELECT * FROM queueaction WHERE id = ?", (queue_action_id,)).fetchone()
    logger.info(result)
    return result

def DeleteQueueAction(action_id):
    db = get_db()
    db.execute("DELETE FROM queueaction WHERE id = ?", (action_id,))
    db.commit()

def UpdateQueueAction(action_id,queue_action,param1,param2):
    logger.info("UpdateQueueAction %s", action_id )

    db = get_db()
    db.execute("UPDATE queueaction SET action = ?, param1 = ?, param2 = ? \
               WHERE id = ?",
               (queue_action,param1,param2,action_id))
    db.commit()
    return "OK"

#Package
def IsValidPackageElement(package_element: str, project_id : int) -> bool:
    logger.info("IsValidPackageElement %s %s", project_id, package_element )
    db = get_db()
    #result = db.execute("SELECT success_state FROM deployment WHERE project_id = ? AND action_object =  ? AND action = "validate" AND created >= ? ", (project_id,package_element,datetime.today())).fetchone()
    result = db.execute('SELECT created FROM deployment WHERE project_id = ? AND action_object =  ? AND success_state = 1 AND action = "validate" AND created >= ?', (project_id,package_element,(datetime.today()- timedelta(1)))).fetchone()

    if result:
        return True
    return False
