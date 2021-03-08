"""
Settings file for the bot, contains json data, databases and logging.

"""

import mysql.connector
from mysql.connector import errorcode
import json
import logging
import os

global info_json
global db
global token
global logger
global soundboard_db


def init(args):
    """Initializes all of the global variables"""

    # NOTE: All testing portions of the bot should be removed before production
    # <testing--------------------------------------------------------------------------------------------------------->
    if args.testing.lower() == "false":
        testing = False
    else:
        testing = True
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
    global info_json
    info_json = readJson(args.json)
    global token
    if testing:
        token = info_json["test_token"]
    else:
        token = info_json["live_token"]
    # <json------------------------------------------------------------------------------------------------------------>

    # <soundboard_db--------------------------------------------------------------------------------------------------->
    global soundboard_db

    if args.db_host is not None:
        host = args.db_host
    else:
        host = info_json['soundboard_database']['server_address']

    if args.db_username is not None:
        db_username = args.db_host
    else:
        db_username = info_json['soundboard_database']['username']

    if args.db_password is not None:
        db_password = args.db_host
    else:
        db_password = info_json['soundboard_database']['password']

    if args.db_name is not None:
        db_name = args.db_host
    else:
        db_name = info_json['soundboard_database']['database']

    soundboard_db = SoundboardDBManager(db_host=host, db_username=db_username, db_password=db_password,
                                        database_name=db_name)
    # <soundboard_db--------------------------------------------------------------------------------------------------->


class SoundboardDBManager:
    def __init__(self, db_host, db_username, db_password, database_name):
        try:
            self.db_host = db_host
            self.db_username = db_username
            self.db_password = db_password
            self.database_name = database_name

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
            sql = "INSERT INTO discord_soundboard (filename, name) VALUES (%s, %s)"
            val = (filename, name)
            self.my_cursor.execute(sql, val)
            self.db.commit()
            logger.info(f"adding sound to db filename:{filename}  name:{name}")
        except mysql.connector.errors.IntegrityError:
            raise ValueError
        except mysql.connector.Error as e:
            if e.errno == errorcode.CR_SERVER_GONE_ERROR:
                logger.info(f"server gone error attempting recovery")
                try:
                    self.db = mysql.connector.connect(
                        host=self.db_host,
                        user=self.db_username,
                        password=self.db_password,
                        database=self.database_name
                    )
                    self.my_cursor = self.db.cursor()

                    sql = "INSERT INTO discord_soundboard (filename, name) VALUES (%s, %s)"
                    val = (filename, name)
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
                    self.db = mysql.connector.connect(
                        host=self.db_host,
                        user=self.db_username,
                        password=self.db_password,
                        database=self.database_name
                    )
                    self.my_cursor = self.db.cursor()

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
                    self.db = mysql.connector.connect(
                        host=self.db_host,
                        user=self.db_username,
                        password=self.db_password,
                        database=self.database_name
                    )
                    self.my_cursor = self.db.cursor()

                    sql = "SELECT * FROM discord_soundboard"
                    self.my_cursor.execute(sql)
                    my_result = self.my_cursor.fetchall()
                    return my_result

                except Exception as e:
                    logger.warning(f"unknown exception while adding to db!")
                    logger.warning(e)

            else:
                logger.warning(f"unknown exception while adding to db!")
                logger.warning(e)

        except Exception as e:
            logger.warning("unknown exception while listing db!")
            logger.warning(e)

    def verify_db(self):
        """Checks database against files on server and manages database accordingly"""
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

        except mysql.connector.Error as e:
            if e.errno == errorcode.CR_SERVER_GONE_ERROR:
                logger.info(f"server gone error attempting recovery")
                try:
                    self.db = mysql.connector.connect(
                        host=self.db_host,
                        user=self.db_username,
                        password=self.db_password,
                        database=self.database_name
                    )
                    self.my_cursor = self.db.cursor()

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
                    logger.warning(f"unknown exception while adding to db!")
                    logger.warning(e)
            else:
                logger.warning(f"unknown exception while verifying db!")
                logger.warning(e)

        except Exception as e:
            logger.warning(f"unknown exception while verifying db!")
            logger.warning(e)


def readToken(filename):
    """reads a token from a file"""
    with open(filename, "r") as f:
        temp_token = f.readlines()
        f.close()
        return temp_token[0].strip()


def readJson(filename):
    """reads and returns json data"""
    with open(filename) as f:
        data = json.load(f)
        f.close()
        return data


def addToJson(filename, json_data, tag, data):
    """adds given data to a json file"""
    with open(filename, "w") as file:
        json_data[tag].append(data)
        json.dump(json_data, file, indent=4)
