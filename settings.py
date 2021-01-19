from utility.tools import readJson
import mysql.connector
import logging
import sys
import os

global json
global db
global token
global logger
global soundboard_db


def init(json_filename="info.json",
         db_host="127.0.0.1",
         db_username="admin",
         db_password="password",
         db_database_name="discord"):

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
        database=db_database_name
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
    # <soundboard_db--------------------------------------------------------------------------------------------------->
    global soundboard_db
    soundboard_db = SoundboardDBManager()
    # <soundboard_db--------------------------------------------------------------------------------------------------->


class SoundboardDBManager:
    def __init__(self):
        self.db = mysql.connector.connect(
            host="database.sodersjerna.com",
            user="Pycharm",
            password="plop9100",
            database="Pycharm"
        )

        self.my_cursor = self.db.cursor()

    def add_db_entry(self, filename: str, name: str):
        try:
            sql = "INSERT INTO discord_soundboard (filename, name) VALUES (%s, %s)"
            val = (filename, name)
            self.my_cursor.execute(sql, val)
            self.db.commit()
            logger.info(f"adding sound to db filename:{filename}  name:{name}")
        except mysql.connector.errors.IntegrityError:
            raise ValueError

    def remove_db_entry(self, soundclip_name: str):
        sql = "DELETE FROM discord_soundboard WHERE name = %s"
        adr = (soundclip_name,)
        self.my_cursor.execute(sql, adr)
        self.db.commit()

    def list_db_files(self):
        sql = "SELECT * FROM discord_soundboard"
        self.my_cursor.execute(sql)
        my_result = self.my_cursor.fetchall()
        return my_result

    def verify_db(self):
        logger.info(f"verifying soundboard db!")
        try:
            db_files = self.list_db_files()

            for file in os.listdir("./soundboard"):
                if file.endswith(".mp3"):
                    for temp in db_files:
                        if temp[0] == file:
                            db_files.remove(temp)

            for file in db_files:
                self.remove_db_entry(file[1])

            for file in os.listdir("./soundboard"):
                if file.endswith(".mp3"):
                    if [db_file for db_file in db_files if db_file[1] == file]:
                        continue
                    else:
                        try:
                            self.add_db_entry(file.lower(), file.replace(".mp3", "").lower())
                        except ValueError:
                            continue
        except Exception as e:
            logger.warning(f"unknown exception while verifying db!")
            logger.warning(e)
