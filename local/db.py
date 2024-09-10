import sqlite3
import os
import platform
from datetime import datetime, timedelta
from flask import Flask, g

dbname = 'application.sql3lite'

def __build_select_query(table_name :str, params : dict ,filter : dict ) -> str:
    # SELECT * FROM table WHERE
    query = "SELECT "
    for param in params:
        query = query + param + ","
    query = query[:-1] + " FROM " + table_name + " WHERE "
    for key in filter:
        query = query + key + " = ? AND "
    query = query[:-4]
    return  query   
    
def __build_update_query(table_name :str, params : dict, filter : dict) -> str:
    #'UPDATE user SET activeproject = ? WHERE id = ?'
    query = "UPDATE " + table_name + " SET "
    for key in params:
        query = query + key + " = ?,"
    query = query[:-1] + " WHERE "
    for key in filter:
        query = query + key + " = ?,"
    query = query[:-1]
    return  query   

def __build_insert_query(table_name :str, params : dict ) -> str:
    #'UPDATE user SET activeproject = ? WHERE id = ?'
    query = "INSERT INTO " + table_name + " ("
    for key in params:
        query = query + key + ","
    query = query[:-1] + " ) VALUES ( "
    for key in params:
        query = query + " ?,"
    query = query[:-1] + ")"
    return  query   

def __build_delete_query(table_name :str, filter) -> str:
    # project = db.execute('DELETE FROM callFlow WHERE id = ?', (callFlow_id,))
    query = "DELETE FROM " + table_name + " WHERE "
    for key in filter:
        query = query + key + " = ? AND "
    query = query[:-4]
    return  query   

##Use instead of init DB from classs
def __connect_to_db():
    print('init_db')
    if platform.system() != "Windows":
        print('Detected Linux?')
        if os.path.isfile('//home//' + dbname):
                print('Connecting to existing DB in home dir')
                db = sqlite3.connect('//home//' + dbname)   
                return db
        else:
            db = sqlite3.connect(dbname)
            print('Creating new database from schema...')
            cursor = db.cursor()
            f = open('.//local//schema.sql', 'r')
            db.executescript(f.read())
            return db
    
    return False
#Create / Connect to DB to ensure active DB ready
def init_db():
    print('init_db')
    if platform.system() != "Windows":
        print('Detected Linux?')
        if os.path.isfile('//home//' + dbname):
                print('Connecting to existing DB in home dir')
                db = sqlite3.connect('//home//' + dbname)   
                return True
        else:
            db = sqlite3.connect('//home//' + dbname)
            print('Creating new database from schema...')
            cursor = db.cursor()
            f = open('.//local//schema.sql', 'r')
            db.executescript(f.read())
            return True
    else:
        print('Detected windows')
        #Does the DB exist already
        if os.path.isfile(dbname):
                print('Connecting to existing DB')
                db = sqlite3.connect(dbname)   
                return True
        else:
            db = sqlite3.connect(dbname)
            print('Creating new database from schema...')
            cursor = db.cursor()
            f = open('.//local//schema.sql', 'r')
            db.executescript(f.read())
            return True
    
    return False

def create_db():
    print('create_db')
    if platform.system() != "Windows":
        print('Detected Linux')
        if os.path.isfile('//home//' + dbname):
                os.remove('//home//' + dbname)
                f = open('.//local//schema.sql', 'r')
                db = sqlite3.connect('//home//' + dbname)
                db.executescript(f.read())  
                return True
    else:
        print('Detected windows- we dont have to do anything here')
    return False

def get_db():
    try:
        if platform.system() != "Windows":
            if 'db' not in g:
                g.db = sqlite3.connect('//home//' + dbname)
            else:
                return g.db
        else:
            if 'db' not in g:
                g.db = sqlite3.connect(dbname)
            else:
                return g.db
        return g.db
    except:
        print("Error connecting to DB - panic")

def Select(table_name : str ,fields : list ,filter_paramaters : dict) -> list :
    query = __build_select_query(table_name,fields,filter_paramaters)
    params = (tuple(filter_paramaters.values()))
    db = get_db()
    result = db.execute(query, params)
    data_list = []
    for row in result:
        row_dict = dict()
        i = 0
        for column in row:
            row_dict[result.description[i][0]] = column
            i = i + 1
        data_list.append(row_dict)
    return data_list

def SelectFirst(table_name : str ,fields : list ,filter_paramaters : dict) -> dict:
    result =  Select(table_name ,fields ,filter_paramaters)
    if len(result) == 0:
        return dict()
    return result[0]
  
def Insert(table_name : str ,field_values : dict):

    query = __build_insert_query(table_name,field_values)
    params = (tuple(field_values.values()))
    db = get_db()
    result = db.execute(query, params)
    db.commit()
    return result.lastrowid

def Update(table_name: str, field_values : dict , filter_paramaters : dict) -> str:
    query = __build_update_query(table_name,field_values,filter_paramaters)
    params = (tuple(field_values.values()) + tuple(filter_paramaters.values()))
    db = get_db()
    result = db.execute(query, params)
    db.commit()
    return result

def Delete(table_name : str, filter_paramaters :dict) -> bool:
    query = __build_delete_query(table_name, filter_paramaters)
    params = (tuple(filter_paramaters.values()))
    db = get_db()
    result = db.execute(query, params)
    db.commit()
    return result

#Config settings
def AddSetting(key, value):
    print('AddSetting')
    db = get_db()
    result = db.execute('INSERT INTO config (key,value) VALUES (?, ?)',(key,value,))
    db.commit()
    return "OK"

def GetSetting(key):
    print('GetSetting')
    db = get_db()
    result = db.execute('SELECT value FROM config WHERE key = ?',(key,)).fetchone()[0]
    db.commit()
    return result

def AddUser(username,password):
    print('AddUser')
    db = get_db()
    result = db.execute('INSERT INTO User (username,password) VALUES (?, ?)',(username,password))
    db.commit()
    return "OK"

#CallFlow
def GetCallFlowList(project_id):
    print('GetCallFlowList ', project_id )
    db = get_db()
    result = db.execute('SELECT * FROM callFlow WHERE project_id = ?', (project_id)).fetchall()
    for row in result: 
        print(row)
    return result

def GetCallFlow(id):
    print('GetCallFlow ', id )
    db = get_db()
    result = db.execute('SELECT * FROM callFlow WHERE id = ?', (id,)).fetchone()
    print(result)
    return result

def AddCallFlow(project_id,name,description,actions_root_id = None):
    print('AddCallFlow ', project_id )
    db = get_db()
    result = db.execute('INSERT INTO callFlow (project_id,name,description,callFlowAction_id ) \
               VALUES (?, ?, ?, ?)',
               (project_id,name,description,actions_root_id))
    print(result)
    db.commit()
    inserted_id = result.lastrowid
    #We will return the ID of the created object
    return str(inserted_id)

#Call flow Actions
def GetCallFlowAction(action_id):
    print('GetCallFlowAction ', action_id )
    db = get_db()
    result = db.execute('SELECT * FROM callFlowAction WHERE id = ?', (action_id,)).fetchone()
    print(result)
    return result

def UpdateCallFlow(params: dict , filter : dict):
    #//print('UpdateCallFlow ', callFlow_id )
    
    #//db = get_db()
    #//db.execute('UPDATE callFlow SET name = ?, description = ? , callFlowAction_id = ?\
    #           WHERE id = ?', 
    #           (name,description,childAction,callFlow_id))
    #//db.commit()
    #//db.close()
    #//return "OK"
    db = get_db()
    query = __build_update_query("callFlow",params,filter)
    params = (tuple(params.values()) + tuple(filter.values()))
    result = db.execute(query, params)
    db.commit()
    inserted_id = result.lastrowid
    #We will return the ID of the created object
    return str(inserted_id)

def DeleteCallFlow(callFlow_id):
    db = get_db()
    project = db.execute('DELETE FROM callFlow WHERE id = ?', (callFlow_id,))
    #for row in project: 
    #    print(row)
    db.commit()
    return "OK"

#Call flow action
def AddCallFlowAction(callflow_id,parentaction_id,name,action,params):
    print('AddCallFlowAction ', callflow_id )
    db = get_db()
    result = db.execute('INSERT INTO callFlowAction (callflow_id,parent_id,name,action,params ) \
               VALUES (?, ?, ?,?,?)',
               (callflow_id,parentaction_id,name,action,params))
    #print(result)
    db.commit()
    inserted_id = result.lastrowid
    #We will return the ID of the created object
    return str(inserted_id)

def UpdateCallFlowAction(params : dict,filter : dict ):
    db = get_db()
    query = __build_update_query("callFlowAction",params,filter)
    params = (tuple(params.values()) + tuple(filter.values()))

    result = db.execute(query, params)
    db.commit()
    #We will return the ID of the created object
    return str(result.rowcount)


#Call Flow Acation responses
def GetCallFlowActionResponse(id):
    print('GetCallFlowActionResponse ')
    db = get_db()
    result = db.execute('SELECT * FROM callFlowResponse WHERE id = ?', (id,)).fetchone()
    return result

def GetCallFlowActionResponses(action_item):
    print('GetCallFlowActionResponses ')
    db = get_db()
    result = db.execute('SELECT * FROM callFlowResponse WHERE callFlowAction_id = ?', (action_item,)).fetchall()
    return result

def AddActionResponse(callflow_id : int, action_id : int, action_response : str , next_action_id :int):
    print('AddActionResponse ')
    db = get_db()
    result = db.execute('INSERT INTO callFlowResponse (callFlow_id,callFlowAction_id,response,callFlowNextAction_id ) \
               VALUES (?, ?, ?,?)',
               (callflow_id,action_id,action_response,next_action_id,))
    #print(result)
    db.commit()
    inserted_id = result.lastrowid
    #We will return the ID of the created object
    return str(inserted_id)

def UpdateCallFlowActionResponse(action_response_id,new_action):
    print('UpdateCallFlowActionResponse ')
    db = get_db()
    result = db.execute('Update callFlowResponse SET callFlowNextAction_id = ? WHERE id = ?',
               (new_action,action_response_id,))
    db.commit()
    inserted_id = result.lastrowid
    #We will return the ID of the created object
    return str(inserted_id)

#Queues
def GetQueue(id):
    print('GetQueue ', id )
    db = get_db()
    result = db.execute('SELECT * FROM queue WHERE id = ?', (id,)).fetchone()
    print(result)
    return result

def GetQueueList(project_id):
    print('GetQueueList ', project_id )
    db = get_db()
    result = db.execute('SELECT * FROM queue WHERE project_id = ?', (project_id)).fetchall()
    for row in result: 
        print(row)
    return result

def GetQueueItemsList(queue_id):
    print('GetQueueList ', queue_id )
    db = get_db()
    result = db.execute('SELECT * FROM queueaction WHERE queue_id = ?', (queue_id)).fetchall()
    for row in result: 
        print(row)
    return result

def AddQueue(project_id,queue_name,queue_skills,queue_hoo):
    print('AddQueue ', project_id )
    db = get_db()
    result = db.execute('INSERT INTO queue (project_id,name,skills, queuehoo ) \
               VALUES (?, ?, ?, ?)',
               (project_id,queue_name,queue_skills,queue_hoo))
    db.commit()
    return result.lastrowid

def UpdateQueue(queue_id,queue_name,queue_skills,queue_hoo):
    print('UpdateQueue ', queue_id )
    
    db = get_db()
    db.execute('UPDATE queue SET name = ?, skills = ?, queuehoo = ? \
               WHERE id = ?', 
               (queue_name,queue_skills,queue_hoo,queue_id))
    db.commit()
    return "OK"

def UpdateQueueHooActions(queue_id,queue,state,action,params):
    print('UpdateQueueHoo ', queue_id )
    queueDetails = GetQueue(queue_id)
    queueHooState = state + ',' + action + ',' + params
    db = get_db()
    if queue == 'PREQUEUE':
        column = 5
    else:
        column = 6
    if queueDetails[column] != None:
        if state in queueDetails[column]:
            for hooState in  queueDetails[column].split('|'):
                if state in hooState:
                    #We are overwriting so do nothing
                    pass
                else:
                    #We dont have this one yet - so add it back in
                    queueHooState = queueHooState + "|" + hooState
        else:
            #This is a new state so just add it in
            queueHooState = str(queueDetails[column]) + '|' + queueHooState
    
    if queue == 'PREQUEUE':
        db.execute('UPDATE queue SET prequeehooactions = ? WHERE id = ?', (queueHooState,queue_id))
    else:
        db.execute('UPDATE queue SET queehooactions = ? WHERE id = ?', (queueHooState,queue_id))
   
    db.commit()
    return True

def DeleteQueueHooAction(queue_id,queue,actionToRemove):
    print('DeleteQueueHooAction ', queue_id,actionToRemove)
    db = get_db()
    if queue == 'PREQUEUE':
        #Get existing HOO states
        queueDetails = GetQueue(queue_id)
        if actionToRemove in queueDetails[5]:
            updatedActions = queueDetails[5].replace(actionToRemove, '')
            updatedActions = updatedActions.replace('||', '|')
            db.execute('UPDATE queue SET prequeehooactions = ? WHERE id = ?', (updatedActions,queue_id))
            db.commit()
            return True
        #No action to remove return false:
        return False
    
    return False
              
def DeleteQueue(queue_id):
    db = get_db()
    project = db.execute('DELETE FROM queue WHERE id = ?', (queue_id,))
    #for row in project: 
    #    print(row)
    db.commit()

#Queue Actions
def GetQueueActionsList(queue_id):
    print('GetQueueActionsList ', queue_id )
    db = get_db()
    result = db.execute('SELECT * FROM queueAction WHERE queue_id = ?', [queue_id]).fetchall()
    for row in result: 
        print(row)
    return result

def GetQueueActionStepCount(queue_id):
    print('GetQueueActionStepCount ', queue_id )
    db = get_db()
    result = db.execute('SELECT COUNT(*) FROM queueaction WHERE queue_id = ?', ([queue_id])).fetchone()[0]
    return int(result)

def AddQueueAction(queue_id,queue_action,param1,param2):
    print('AddQueueAction ', queue_id,queue_action,param1,param2 )
    db = get_db()
    result = db.execute('INSERT INTO queueaction (queue_id,action,param1,param2,step_id) \
               VALUES (?, ?, ?, ?,?)',
               (queue_id,queue_action,param1,param2,(GetQueueActionStepCount(queue_id)+1)))
    db.commit()
    return "OK"

def GetQueueAction(id):
    print('GetQueueAction ', id )
    db = get_db()
    result = db.execute('SELECT * FROM queueaction WHERE id = ?', (id,)).fetchone()
    print(result)
    return result

def DeleteQueueAction(action_id):

    db = get_db()
    project = db.execute('DELETE FROM queueaction WHERE id = ?', (action_id,))
    #for row in project: 
    #    print(row)
    db.commit()

def UpdateQueueAction(action_id,queue_action,param1,param2):
    print('UpdateQueueAction ', action_id )

    db = get_db()
    db.execute('UPDATE queueaction SET action = ?, param1 = ?, param2 = ? \
               WHERE id = ?', 
               (queue_action,param1,param2,action_id))
    db.commit()
    return "OK"

#Package
def IsValidPackageElement(package_element: str, project_id : int) -> bool:
    print('IsValidPackageElement ', project_id, package_element )
    db = get_db()
    #result = db.execute('SELECT success_state FROM deployment WHERE project_id = ? AND action_object =  ? AND action = "validate" AND created >= ? ', (project_id,package_element,datetime.today())).fetchone()
    result = db.execute('SELECT created FROM deployment WHERE project_id = ? AND action_object =  ? AND success_state = 1 AND action = "validate" AND created >= ?', (project_id,package_element,(datetime.today()- timedelta(1)))).fetchone()
    
    if result:
        return True
    return False