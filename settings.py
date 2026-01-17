"""
Settings file for the bot, contains json data, databases and logging.
"""

VERSION = "0.0.2"

import mysql.connector
from mysql.connector import errorcode
from datetime import datetime, timedelta
import re
import json
import logging
import os

global info_json
global db
global token
global logger
global soundboard_db
global ban_db
global version_db


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
        db_username = args.db_username

    if args.db_password is None:
        db_password = info_json['soundboard_database']['password']
    else:
        db_password = args.db_password

    if args.db_name is None:
        db_name = info_json['soundboard_database']['database']
    else:
        db_name = args.db_name

    soundboard_db = SoundboardDBManager(db_host=host, db_username=db_username, db_password=db_password,
                                        database_name=db_name)
    # <soundboard_db--------------------------------------------------------------------------------------------------->

    # <ban_db---------------------------------------------------------------------------------------------------------->
    global ban_db
    ban_db = BanDBManager(db_host=host, db_username=db_username, db_password=db_password,
                          database_name=db_name)
    # <ban_db---------------------------------------------------------------------------------------------------------->

    # <version_db------------------------------------------------------------------------------------------------------>
    global version_db
    version_db = VersionDBManager(db_host=host, db_username=db_username, db_password=db_password,
                                  database_name=db_name)
    # <version_db------------------------------------------------------------------------------------------------------>


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
                except mysql.connector.Error as retry_error:
                    logger.error(f"Database error during retry: {retry_error}")
                    raise
            else:
                logger.error(f"Database error: {e}")
                raise

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

                except mysql.connector.Error as retry_error:
                    logger.error(f"Database error during retry while removing: {retry_error}")
                    raise
            else:
                logger.error(f"Database error while removing: {e}")
                raise

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

                except mysql.connector.Error as retry_error:
                    logger.error(f"Database error during retry while listing: {retry_error}")
                    raise
            else:
                logger.error(f"Database error while listing: {e}")
                raise

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

                except mysql.connector.Error as retry_error:
                    logger.error(f"Database error during retry while verifying: {retry_error}")
                    return
            else:
                logger.error(f"Database error while verifying: {e}")
                return
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
        except OSError as e:
            logger.error(f"File system error while verifying db: {e}")
        except mysql.connector.Error as e:
            logger.error(f"Database error while verifying db: {e}")


def add_to_json(filename, json_data, tag, data):
    """adds given data to a json file"""
    with open(filename, "w") as file:
        json_data[tag].append(data)
        json.dump(json_data, file, indent=4)


def parse_ban_duration(duration_str: str):
    """
    Parses a duration string into a timedelta.
    Supports: Xm (minutes), Xh (hours), Xd (days), or 'x'/'permanent' for permanent bans.
    Returns None for permanent bans, or a timedelta for timed bans.
    Raises ValueError for invalid formats.
    """
    duration_str = duration_str.strip().lower()

    # Check for permanent ban
    if duration_str in ('x', 'permanent', 'perm', 'forever'):
        return None

    # Parse duration with regex
    match = re.match(r'^(\d+)([mhd])$', duration_str)
    if not match:
        raise ValueError(f"Invalid duration format: {duration_str}. Use Xm, Xh, Xd, or 'x' for permanent.")

    value = int(match.group(1))
    unit = match.group(2)

    if value <= 0:
        raise ValueError("Duration must be a positive number.")

    if unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)


class BanDBManager:
    """
    Manages the bot ban database
    """
    def __init__(self, db_host, db_username, db_password, database_name):
        self.db = None
        self.my_cursor = None

        self.db_host = db_host
        self.db_username = db_username
        self.db_password = db_password
        self.database_name = database_name

        self.connect()
        self._create_table()

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
                logger.warning("Ban DB: user name or password is bad")
            elif e.errno == errorcode.ER_BAD_DB_ERROR:
                logger.warning("Ban DB: Database does not exist")
            else:
                logger.warning(f"Ban DB: {e}")

    def _create_table(self):
        """Creates the ban table if it doesn't exist"""
        try:
            sql = """
                CREATE TABLE IF NOT EXISTS discord_bans (
                    user_id VARCHAR(255) PRIMARY KEY,
                    username VARCHAR(255),
                    banned_by VARCHAR(255),
                    banned_at DATETIME,
                    expires_at DATETIME NULL,
                    reason VARCHAR(500)
                )
            """
            self.my_cursor.execute(sql)
            self.db.commit()
            logger.info("Ban table verified/created")
        except mysql.connector.Error as e:
            logger.error(f"Failed to create ban table: {e}")

    def _execute_with_reconnect(self, operation, *args, **kwargs):
        """Helper to execute database operations with automatic reconnection"""
        try:
            return operation(*args, **kwargs)
        except mysql.connector.Error as e:
            if e.errno == errorcode.CR_SERVER_GONE_ERROR:
                logger.info("Ban DB: server gone error, attempting recovery")
                self.connect()
                return operation(*args, **kwargs)
            else:
                raise

    def add_ban(self, user_id: str, username: str, banned_by: str, duration: timedelta = None, reason: str = None):
        """
        Adds a ban to the database.
        :param user_id: Discord user ID
        :param username: Discord username (for display purposes)
        :param banned_by: Admin who issued the ban
        :param duration: timedelta for ban length, or None for permanent
        :param reason: Optional reason for the ban
        """
        def _do_add():
            banned_at = datetime.now()
            expires_at = banned_at + duration if duration else None

            sql = """
                INSERT INTO discord_bans (user_id, username, banned_by, banned_at, expires_at, reason)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                    username = VALUES(username),
                    banned_by = VALUES(banned_by),
                    banned_at = VALUES(banned_at),
                    expires_at = VALUES(expires_at),
                    reason = VALUES(reason)
            """
            val = (str(user_id), username, banned_by, banned_at, expires_at, reason)
            self.my_cursor.execute(sql, val)
            self.db.commit()
            logger.info(f"Added ban for user {username} (ID: {user_id}), expires: {expires_at}")
            return expires_at

        return self._execute_with_reconnect(_do_add)

    def remove_ban(self, user_id: str):
        """Removes a ban from the database"""
        def _do_remove():
            sql = "DELETE FROM discord_bans WHERE user_id = %s"
            self.my_cursor.execute(sql, (str(user_id),))
            self.db.commit()
            affected = self.my_cursor.rowcount
            logger.info(f"Removed ban for user ID: {user_id}, rows affected: {affected}")
            return affected > 0

        return self._execute_with_reconnect(_do_remove)

    def is_banned(self, user_id: str):
        """
        Checks if a user is currently banned.
        Returns ban info dict if banned, None if not banned.
        Automatically cleans up expired bans.
        """
        def _do_check():
            sql = "SELECT user_id, username, banned_by, banned_at, expires_at, reason FROM discord_bans WHERE user_id = %s"
            self.my_cursor.execute(sql, (str(user_id),))
            result = self.my_cursor.fetchone()

            if not result:
                return None

            db_user_id, username, banned_by, banned_at, expires_at, reason = result

            # Check if ban has expired
            if expires_at and datetime.now() > expires_at:
                # Ban expired, remove it
                self.remove_ban(db_user_id)
                return None

            return {
                'user_id': db_user_id,
                'username': username,
                'banned_by': banned_by,
                'banned_at': banned_at,
                'expires_at': expires_at,
                'reason': reason,
                'permanent': expires_at is None
            }

        return self._execute_with_reconnect(_do_check)

    def list_bans(self):
        """Returns a list of all current bans (excluding expired ones)"""
        def _do_list():
            # Clean up expired bans first
            cleanup_sql = "DELETE FROM discord_bans WHERE expires_at IS NOT NULL AND expires_at < %s"
            self.my_cursor.execute(cleanup_sql, (datetime.now(),))
            self.db.commit()

            # Get remaining bans
            sql = "SELECT user_id, username, banned_by, banned_at, expires_at, reason FROM discord_bans ORDER BY banned_at DESC"
            self.my_cursor.execute(sql)
            results = self.my_cursor.fetchall()

            bans = []
            for row in results:
                bans.append({
                    'user_id': row[0],
                    'username': row[1],
                    'banned_by': row[2],
                    'banned_at': row[3],
                    'expires_at': row[4],
                    'reason': row[5],
                    'permanent': row[4] is None
                })
            return bans

        return self._execute_with_reconnect(_do_list)


class VersionDBManager:
    """
    Manages version tracking for update notifications
    """
    def __init__(self, db_host, db_username, db_password, database_name):
        self.db = None
        self.my_cursor = None

        self.db_host = db_host
        self.db_username = db_username
        self.db_password = db_password
        self.database_name = database_name

        self.connect()
        self._create_table()

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
                logger.warning("Version DB: user name or password is bad")
            elif e.errno == errorcode.ER_BAD_DB_ERROR:
                logger.warning("Version DB: Database does not exist")
            else:
                logger.warning(f"Version DB: {e}")

    def _create_table(self):
        """Creates the version tracking table if it doesn't exist"""
        try:
            sql = """
                CREATE TABLE IF NOT EXISTS discord_version (
                    id INT PRIMARY KEY DEFAULT 1,
                    last_version VARCHAR(50),
                    last_updated DATETIME,
                    CONSTRAINT single_row CHECK (id = 1)
                )
            """
            self.my_cursor.execute(sql)
            self.db.commit()
            logger.info("Version table verified/created")
        except mysql.connector.Error as e:
            logger.error(f"Failed to create version table: {e}")

    def _execute_with_reconnect(self, operation, *args, **kwargs):
        """Helper to execute database operations with automatic reconnection"""
        try:
            return operation(*args, **kwargs)
        except mysql.connector.Error as e:
            if e.errno == errorcode.CR_SERVER_GONE_ERROR:
                logger.info("Version DB: server gone error, attempting recovery")
                self.connect()
                return operation(*args, **kwargs)
            else:
                raise

    def get_last_version(self):
        """Gets the last notified version from the database"""
        def _do_get():
            sql = "SELECT last_version FROM discord_version WHERE id = 1"
            self.my_cursor.execute(sql)
            result = self.my_cursor.fetchone()
            return result[0] if result else None

        return self._execute_with_reconnect(_do_get)

    def set_last_version(self, version: str):
        """Updates the last notified version in the database"""
        def _do_set():
            sql = """
                INSERT INTO discord_version (id, last_version, last_updated)
                VALUES (1, %s, %s)
                ON DUPLICATE KEY UPDATE
                    last_version = VALUES(last_version),
                    last_updated = VALUES(last_updated)
            """
            self.my_cursor.execute(sql, (version, datetime.now()))
            self.db.commit()
            logger.info(f"Version updated to {version}")

        return self._execute_with_reconnect(_do_set)

    def check_version_changed(self, current_version: str):
        """
        Checks if the version has changed since last notification.
        Returns True if this is a new version, False otherwise.
        """
        last_version = self.get_last_version()
        return last_version != current_version
