"""
Settings file for the bot, contains json data, databases and logging.
"""

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime
import json
import logging
import os

global info_json
global db
global token
global logger
global soundboard_db


def init(args):
    """Initializes global variables"""

    # <logger---------------------------------------------------------------------------------------------------------->
    global logger
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("bot.log")
    discord_file_handler = logging.FileHandler("discord.log")
    console_handler = logging.StreamHandler()

    logger = logging.getLogger("Logger")
    logger.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)

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
    global info_json
    with open(args.json, 'r') as f:
        info_json = json.load(f)
        f.close()
    global token
    token = info_json["token"]
    # <json------------------------------------------------------------------------------------------------------------>

    # <soundboard_db--------------------------------------------------------------------------------------------------->
    global soundboard_db

    if args.db_host is None:
        host = info_json['soundboard_database']['server_address']
    else:
        host = args.db_host

    if args.db_username is None:
        db_username = info_json['soundboard_database']['username']
    else:
        db_username = args.db_host

    if args.db_password is None:
        db_password = info_json['soundboard_database']['password']
    else:
        db_password = args.db_host

    if args.db_name is None:
        db_name = info_json['soundboard_database']['database']
    else:
        db_name = args.db_host

    soundboard_db = SoundboardDBManager(db_host=host, db_username=db_username, db_password=db_password,
                                        database_name=db_name)
    # <soundboard_db--------------------------------------------------------------------------------------------------->


class SoundboardDBManager:
    """
    Manages the soundboard database
    """
    def __init__(self, db_host, db_username, db_password, database_name):
        self.db = None
        self.my_cursor = None

        self.db_host = db_host
        self.db_username = db_username
        self.db_password = db_password
        self.database_name = database_name

        self.connect()

    def connect(self):
        """Connects to the database"""
        try:
            self.db = mysql.connector.connect(
                host=self.db_host,
                user=self.db_username,
                password=self.db_password,
                database=self.database_name
            )
            self.my_cursor = self.db.cursor()
        except mysql.connector.Error as e:
            if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logger.warning("Soundboard user name or password is Bad")
            elif e.errno == errorcode.ER_BAD_DB_ERROR:
                logger.warning("Database does not exist")
            else:
                logger.warning(e)

    def add_db_entry(self, filename: str, name: str):
        """Adds given filename to database with the given name"""
        try:
            sql = "INSERT INTO discord_soundboard (filename, name, date_added) VALUES (%s, %s, %s)"
            val = (filename, name, datetime.now())
            self.my_cursor.execute(sql, val)
            self.db.commit()
            logger.info(f"adding sound to db filename:{filename}  name:{name}")
        except mysql.connector.errors.IntegrityError:
            raise ValueError
        except mysql.connector.Error as e:
            if e.errno == errorcode.CR_SERVER_GONE_ERROR:
                logger.info(f"server gone error attempting recovery")
                try:
                    self.connect()

                    sql = "INSERT INTO discord_soundboard (filename, name, date_added) VALUES (%s, %s, %s)"
                    val = (filename, name, datetime.now())
                    self.my_cursor.execute(sql, val)
                    self.db.commit()
                    logger.info(f"adding sound to db filename:{filename}  name:{name}")
                except Exception as e:
                    logger.warning(f"unknown exception while adding to db!")
                    logger.warning(e)

        except Exception as e:
            logger.warning("unknown exception while adding to db!")
            logger.warning(e)

    def remove_db_entry(self, filename: str):
        """Removes database entry for the given filename"""
        try:
            if filename is not None:
                sql = "DELETE FROM discord_soundboard WHERE name = %s"
                adr = (filename,)
                self.my_cursor.execute(sql, adr)
                self.db.commit()
                logger.info(f"removed sound from db filename:{filename}")

        except mysql.connector.Error as e:
            if e.errno == errorcode.CR_SERVER_GONE_ERROR:
                logger.info(f"server gone error attempting recovery")
                try:
                    self.connect()

                    sql = "DELETE FROM discord_soundboard WHERE name = %s"
                    adr = (filename,)
                    self.my_cursor.execute(sql, adr)
                    self.db.commit()
                    logger.info(f"removed sound from db filename:{filename}")

                except Exception as e:
                    logger.warning(f"unknown exception while adding to db!")
                    logger.warning(e)
            else:
                logger.warning(f"unknown exception while adding to db!")
                logger.warning(e)

        except Exception as e:
            logger.warning("unknown exception while removing from db!")
            logger.warning(e)

    def list_db_files(self):
        """Returns a list of database entries"""
        try:
            sql = "SELECT * FROM discord_soundboard"
            self.my_cursor.execute(sql)
            my_result = self.my_cursor.fetchall()
            logger.info("list database files")
            return my_result

        except mysql.connector.Error as e:
            if e.errno == errorcode.CR_SERVER_GONE_ERROR:
                logger.info(f"server gone error attempting recovery")
                try:
                    self.connect()

                    sql = "SELECT * FROM discord_soundboard"
                    self.my_cursor.execute(sql)
                    my_result = self.my_cursor.fetchall()
                    return my_result

                except Exception as e:
                    logger.warning(f"List_db_file inner unknown exception while listing db!")
                    logger.warning(e)

            else:
                logger.warning(f"List_db_file unknown my sql exception while listing db!")
                logger.warning(e)

        except Exception as e:
            logger.warning("List_db_file unknown exception while listing db!")
            logger.warning(e)

    def verify_db(self):
        """Checks database against files on server and manages database accordingly
        #Note: This function is very inefficient and needs optimization
        """
        logger.info(f"verifying soundboard db!")
        db_files = []
        try:
            db_files = self.list_db_files()  # get list of database files

        except mysql.connector.Error as e:
            if e.errno == errorcode.CR_SERVER_GONE_ERROR:
                logger.info(f"server gone error attempting recovery")
                try:
                    self.connect()
                    db_files = self.list_db_files()

                except Exception as e:
                    logger.warning(f"unknown exception while adding to db!")
                    logger.warning(e)
            else:
                logger.warning(f"unknown exception while verifying db!")
                logger.warning(e)

        except Exception as e:
            logger.warning(f"unknown exception while verifying db!")
            logger.warning(e)
        try:
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


def add_to_json(filename, json_data, tag, data):
    """adds given data to a json file"""
    with open(filename, "w") as file:
        json_data[tag].append(data)
        json.dump(json_data, file, indent=4)
