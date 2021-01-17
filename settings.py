from utility.tools import readJson
import mysql.connector
import logging
import sys

global json
global db
global token
global logger


def init(json_filename="info.json", db_host="127.0.0.1", db_username="admin", db_password="password",
         db_database="discord"):

    # All testing portions of the bot should be removed before production
    # <testing--------------------------------------------------------------------------------------------------------->
    testing = True

    if len(sys.argv) == 2:
        if "false" in sys.argv[1] or "False" in sys.argv[1]:
            testing = False
    # <testing--------------------------------------------------------------------------------------------------------->

    # <logger---------------------------------------------------------------------------------------------------------->
    global logger
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("bot.log")
    discord_file_handler = logging.FileHandler("discord.log")
    console_handler = logging.StreamHandler()

    if testing:
        logger = logging.getLogger("Testing-Logger")
        logger.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    else:
        logger = logging.getLogger("Live-Logger")
        logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    discord_file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    discord_logger.addHandler(discord_file_handler)
    discord_logger.addHandler(console_handler)
    # <logger---------------------------------------------------------------------------------------------------------->

    # <json------------------------------------------------------------------------------------------------------------>
    global json
    json = readJson(json_filename)
    # <json------------------------------------------------------------------------------------------------------------>

    # <db-------------------------------------------------------------------------------------------------------------->
    global db
    db = mysql.connector.connect(
        host=db_host,
        user=db_username,
        password=db_password,
        database=db_database
    )

    my_cursor = db.cursor()

    global token
    token = None

    # more testing
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
    # <db-------------------------------------------------------------------------------------------------------------->
