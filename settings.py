from utility.tools import readJson
import mysql.connector
import logging
import sys

global json
global db
global my_cursor
global token
global logger


def init(json_filename="info.json", db_host="127.0.0.1", db_username="admin", db_password="password",
         db_database="discord"):
    testing = True

    if len(sys.argv) == 2:
        if "false" in sys.argv[1] or "False" in sys.argv[1]:
            testing = False

    # <logger --------------------------------------------------------------------------------------------------------->
    global logger

    file_handler = logging.FileHandler("bot.log")
    console_handler = logging.StreamHandler()

    if testing:
        logger = logging.getLogger("TestingDebug")
        logger.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    else:
        logger = logging.getLogger("LiveDebug")
        logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    # <---------------------------------------------------------------------------------------------------------------->

    # <json------------------------------------------------------------------------------------------------------------>
    global json
    json = readJson(json_filename)
    # <---------------------------------------------------------------------------------------------------------------->

    # <db-------------------------------------------------------------------------------------------------------------->
    global db
    db = mysql.connector.connect(
        host=db_host,
        user=db_username,
        password=db_password,
        database=db_database
    )

    global my_cursor
    my_cursor = db.cursor()

    global token
    token = None

    if testing:
        sql = "SELECT * FROM tokens WHERE name ='Test'"
        my_cursor.execute(sql)
        my_result = my_cursor.fetchall()
        for x in my_result:
            token = x[1]
    else:
        sql = "SELECT * FROM tokens WHERE name ='Live'"
        my_cursor.execute(sql)
        my_result = my_cursor.fetchall()
        for x in my_result:
            token = x[1]
    # <---------------------------------------------------------------------------------------------------------------->
