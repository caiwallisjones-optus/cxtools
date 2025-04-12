"""Simple SQL lite access functions"""
# -*- coding: utf-8 -*-

import sqlite3
import os
import platform
import shutil

from datetime import datetime
from flask import g
from local import logger

DB_NAME = "application.sql3lite"

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
    destinationfile = DB_NAME.replace(".sql3lite",f"{datetime.now().strftime('%Y_%m_%d_%H_%M')}.sql3lite")
    shutil.copyfile(DB_NAME,destinationfile)
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
    destination_file = DB_NAME.replace(".sql3lite",f".{datetime.now().strftime("%Y_%m_%d_%H_%M")}")

    if platform.system() != "Windows":
        logger.info("Detected Linux environment - looking for DB in /home")
        if os.path.isfile("//home//" + DB_NAME):
            logger.info("Backing up database")
            destination_file = "//home//" + DB_NAME.replace(".sql3lite",f".{datetime.now().strftime("%Y_%m_%d_%H_%M")}_sql3lite")
        else:
            logger.info("ERROR: Unable to locate original file")
    else:
        logger.info("Detected windows environement - using local DB_NAME and directory")

    logger.info("Backing up to %s", destination_file)
    shutil.copyfile(DB_NAME,destination_file)

def __connect_to_db():
    """Used by admin functions to connect to the database - outside of the normal Flask context"""
    logger.info("__connect_to_db")
    if platform.system() != "Windows":
        logger.info("Detected Linux environment - looking for DB in /home")
        if os.path.isfile("//home//" + DB_NAME):
            logger.info("Connecting to existing DB in home dir")
            db = sqlite3.connect("//home//" + DB_NAME)
            #logger.info(f"Detected version {GetSetting("version")}")
            return db
        else:
            logger.info("Creating new database from schema...")
            db = sqlite3.connect(DB_NAME)
            f = open(".//local//schema.sql", "r", encoding="UTF-8")
            db.executescript(f.read())
            #logger.info(f"Detected version {GetSetting("version")}")
            return db
    else:
        db = sqlite3.connect(DB_NAME)
        #logger.info(f"Detected version {GetSetting("version")}")
        return db

#Create / Connect to DB to ensure active DB ready
def init_db():
    logger.info("init_db")
    if platform.system() != "Windows":
        logger.info("Init DB")
        if os.path.isfile("//home//" + DB_NAME):
            logger.info("Connecting to existing DB in home dir")
            db = sqlite3.connect("//home//" + DB_NAME)
            return True

        db = sqlite3.connect("//home//" + DB_NAME)
        logger.info("Creating new database from schema...")
        f = open(".//local//schema.sql", "r" , encoding="utf-8")
        db.executescript(f.read())
        logger.info("Created")
        return True
    else:
        logger.info("Detected windows")
        #Does the DB exist already
        if os.path.isfile(DB_NAME):
            logger.info("Connecting to existing DB")
            db = sqlite3.connect(DB_NAME)
            return True

        db = sqlite3.connect(DB_NAME)
        logger.info("Creating new database from schema...")
        f = open(".//local//schema.sql", "r", encoding="utf-8")
        db.executescript(f.read())
        return True

    return False

def create_db():
    logger.info("create_db")
    if platform.system() != "Windows":
        logger.info("Detected Linux")
        if os.path.isfile("//home//" + DB_NAME):
            os.remove("//home//" + DB_NAME)
            f = open(".//local//schema.sql", "r" , encoding = "utf-8")
            db = sqlite3.connect("//home//" + DB_NAME)
            db.executescript(f.read())
            return True

    logger.info("Detected windows- we dont have to do anything here")
    return False

def get_db():
    #logger.DEBUG("get_db")
    try:
        if platform.system() != "Windows":
            if "db" not in g:
                g.db = sqlite3.connect("//home//" + DB_NAME)
            else:
                return g.db
        else:
            if "db" not in g:
                g.db = sqlite3.connect(DB_NAME)
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

def select_first(table_name : str , fields : list ,filter_paramaters : dict) -> dict:
    result =  select(table_name ,fields ,filter_paramaters)
    if len(result) == 0:
        return None
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
