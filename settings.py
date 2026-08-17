"""
Settings file for the bot, contains json data, databases and logging.
"""

VERSION = "0.0.3"

# Internal release codenames. The startup presence is set to the codename for the
# running VERSION so the devs can tell what is deployed at a glance without the
# version number being meaningful to anyone else. Add an entry per release.
VERSION_CODENAMES = {
    "0.0.1": "0.0.1",
    "0.0.2": "0.0.2",
    "0.0.3": "Finally fixed it",
}

# Presence used when VERSION has no codename entry yet (i.e. someone bumped
# VERSION and forgot to add a codename).
UNKNOWN_VERSION_CODENAME = "unreleased"

import argparse
import mysql.connector
from mysql.connector import errorcode
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional, Any, Callable, List, Dict
import re
import json
import logging
import os
import tempfile


# Module-level settings instance (initialized by init())
settings: Optional["Settings"] = None

# Mutable data the bot writes at runtime. Kept separate from info.json so that a
# runtime write can never touch the file holding the token and credentials.
RUNTIME_DATA_FILE = os.path.join("info", "runtime_data.json")


@dataclass
class Settings:
    """Container for all global settings and database connections"""
    info_json: dict
    token: str
    logger: logging.Logger
    soundboard_db: "SoundboardDBManager"
    ban_db: "BanDBManager"
    version_db: "VersionDBManager"
    assistant_db: "AssistantDBManager"


def _setup_logging() -> tuple[logging.Logger, logging.Logger]:
    """Sets up logging configuration and returns (bot_logger, discord_logger)"""
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(logging.INFO)

    file_handler = logging.FileHandler("bot.log")
    discord_file_handler = logging.FileHandler("discord.log")
    console_handler = logging.StreamHandler()

    bot_logger = logging.getLogger("Logger")
    bot_logger.setLevel(logging.DEBUG)
    file_handler.setLevel(logging.DEBUG)
    console_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)
    discord_file_handler.setFormatter(formatter)

    bot_logger.addHandler(file_handler)
    bot_logger.addHandler(console_handler)
    discord_logger.addHandler(discord_file_handler)
    discord_logger.addHandler(console_handler)

    return bot_logger, discord_logger


def _load_config(json_path: str) -> tuple[dict, str]:
    """Loads configuration from JSON file and returns (config_dict, token)"""
    with open(json_path, 'r') as f:
        info_json = json.load(f)
    token = info_json["token"]
    return info_json, token


def _get_db_config(args: argparse.Namespace, info_json: dict) -> dict:
    """Extracts database configuration from args or info_json"""
    return {
        'host': args.db_host or info_json['soundboard_database']['server_address'],
        'username': args.db_username or info_json['soundboard_database']['username'],
        'password': args.db_password or info_json['soundboard_database']['password'],
        'database': args.db_name or info_json['soundboard_database']['database'],
    }


def _init_databases(
    db_config: dict,
    logger: logging.Logger
) -> tuple["SoundboardDBManager", "BanDBManager", "VersionDBManager", "AssistantDBManager"]:
    """Initializes all database managers"""
    soundboard_db = SoundboardDBManager(
        db_host=db_config['host'],
        db_username=db_config['username'],
        db_password=db_config['password'],
        database_name=db_config['database'],
        logger=logger
    )
    ban_db = BanDBManager(
        db_host=db_config['host'],
        db_username=db_config['username'],
        db_password=db_config['password'],
        database_name=db_config['database'],
        logger=logger
    )
    version_db = VersionDBManager(
        db_host=db_config['host'],
        db_username=db_config['username'],
        db_password=db_config['password'],
        database_name=db_config['database'],
        logger=logger
    )
    assistant_db = AssistantDBManager(
        db_host=db_config['host'],
        db_username=db_config['username'],
        db_password=db_config['password'],
        database_name=db_config['database'],
        logger=logger
    )
    return soundboard_db, ban_db, version_db, assistant_db


def _migrate_runtime_data(info_json: dict, logger: logging.Logger) -> None:
    """
    Seeds the runtime data file from the config file the first time it is needed.

    Scribble words used to be appended to info.json itself; this carries any
    existing words over so they are not lost. The config file is left untouched.
    """
    if os.path.exists(RUNTIME_DATA_FILE):
        return

    legacy_scribbles = info_json.get("scribble", [])
    if not legacy_scribbles:
        return

    try:
        _write_json_atomic(RUNTIME_DATA_FILE, {"scribble": list(legacy_scribbles)})
        logger.info(f"Migrated {len(legacy_scribbles)} scribble words to {RUNTIME_DATA_FILE}")
    except OSError as e:
        logger.error(f"Could not migrate scribble words to {RUNTIME_DATA_FILE}: {e}")


def init(args: argparse.Namespace) -> None:
    """Initializes global settings"""
    global settings

    # Setup logging
    bot_logger, _ = _setup_logging()

    # Load configuration
    info_json, token = _load_config(args.json)

    # Move any mutable data out of the config file and into the runtime data file
    _migrate_runtime_data(info_json, bot_logger)

    # Get database configuration
    db_config = _get_db_config(args, info_json)

    # Initialize databases
    soundboard_db, ban_db, version_db, assistant_db = _init_databases(db_config, bot_logger)

    # Create settings instance
    settings = Settings(
        info_json=info_json,
        token=token,
        logger=bot_logger,
        soundboard_db=soundboard_db,
        ban_db=ban_db,
        version_db=version_db,
        assistant_db=assistant_db
    )


class DatabaseUnavailableError(Exception):
    """
    Raised when an operation cannot be completed because the database is unreachable.

    Callers get this instead of an AttributeError on a None cursor, so they can decide
    whether to degrade or report the failure.
    """


class BaseDBManager:
    """
    Base class for database managers with shared connection and reconnection logic
    """
    # Error codes for connection lost
    CR_SERVER_GONE_ERROR = 2006
    CR_SERVER_LOST = 2013

    def __init__(
        self,
        db_host: str,
        db_username: str,
        db_password: str,
        database_name: str,
        logger: logging.Logger,
        name: str = "DB"
    ):
        self.db: Optional[mysql.connector.MySQLConnection] = None
        self.my_cursor: Optional[mysql.connector.cursor.MySQLCursor] = None

        self.db_host = db_host
        self.db_username = db_username
        self.db_password = db_password
        self.database_name = database_name
        self._logger = logger
        self._name = name

        # A database that is down at startup must not stop the bot from running; the
        # connection is retried on first use instead.
        try:
            self.connect()
        except DatabaseUnavailableError as e:
            self._logger.error(f"{self._name}: starting without a connection ({e}), will retry on first use")

    @property
    def connected(self) -> bool:
        """True if this manager currently holds a usable cursor"""
        return self.my_cursor is not None

    def connect(self) -> None:
        """
        Connects to the database and prepares its schema.

        Raises:
            DatabaseUnavailableError: if the connection could not be established
        """
        try:
            self.db = mysql.connector.connect(
                host=self.db_host,
                user=self.db_username,
                password=self.db_password,
                database=self.database_name
            )
            self.my_cursor = self.db.cursor()
        except mysql.connector.Error as e:
            self.db = None
            self.my_cursor = None

            if e.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                reason = "username or password is bad"
            elif e.errno == errorcode.ER_BAD_DB_ERROR:
                reason = "database does not exist"
            else:
                reason = str(e)

            self._logger.warning(f"{self._name}: {reason}")
            raise DatabaseUnavailableError(f"{self._name}: {reason}") from e

        # Runs on every successful connect, so a table missed while the server was
        # down still gets created once it comes back
        self._create_table()

    def _create_table(self) -> None:
        """Creates the tables this manager needs. No-op unless a subclass needs one."""

    def _ensure_connection(self) -> None:
        """
        Makes sure a cursor is available, reconnecting if needed.

        Raises:
            DatabaseUnavailableError: if the database still cannot be reached
        """
        if not self.connected:
            self._logger.info(f"{self._name}: no connection, attempting to reconnect")
            self.connect()

    def _execute_with_reconnect(self, operation: Callable[[], Any], *args, **kwargs) -> Any:
        """
        Helper to execute database operations with automatic reconnection

        Raises:
            DatabaseUnavailableError: if the database is unreachable
        """
        self._ensure_connection()

        try:
            return operation(*args, **kwargs)
        except mysql.connector.Error as e:
            # Handle both CR_SERVER_GONE_ERROR (2006) and CR_SERVER_LOST (2013)
            if e.errno == errorcode.CR_SERVER_GONE_ERROR or e.errno == self.CR_SERVER_LOST:
                self._logger.info(f"{self._name}: connection lost (error {e.errno}), attempting recovery")
                self.my_cursor = None
                self.connect()
                return operation(*args, **kwargs)
            else:
                raise


class SoundboardDBManager(BaseDBManager):
    """
    Manages the soundboard database
    """
    def __init__(
        self,
        db_host: str,
        db_username: str,
        db_password: str,
        database_name: str,
        logger: logging.Logger
    ):
        super().__init__(db_host, db_username, db_password, database_name, logger, "Soundboard DB")

    def add_db_entry(self, filename: str, name: str) -> None:
        """Adds given filename to database with the given name"""
        def _do_add() -> None:
            sql = "INSERT INTO discord_soundboard (filename, name, date_added) VALUES (%s, %s, %s)"
            val = (filename, name, datetime.now())
            self.my_cursor.execute(sql, val)
            self.db.commit()
            self._logger.info(f"adding sound to db filename:{filename}  name:{name}")

        try:
            self._execute_with_reconnect(_do_add)
        except mysql.connector.errors.IntegrityError:
            raise ValueError(f"Sound '{name}' already exists in database")

    def remove_db_entry(self, filename: str) -> None:
        """Removes database entry for the given filename"""
        def _do_remove() -> None:
            if filename is not None:
                sql = "DELETE FROM discord_soundboard WHERE name = %s"
                self.my_cursor.execute(sql, (filename,))
                self.db.commit()
                self._logger.info(f"removed sound from db filename:{filename}")

        self._execute_with_reconnect(_do_remove)

    def list_db_files(self) -> List[tuple]:
        """Returns a list of database entries"""
        def _do_list() -> List[tuple]:
            sql = "SELECT * FROM discord_soundboard"
            self.my_cursor.execute(sql)
            my_result = self.my_cursor.fetchall()
            self._logger.info("list database files")
            return my_result

        return self._execute_with_reconnect(_do_list)

    def verify_db(self) -> None:
        """
        Checks database against files on server and manages database accordingly.
        Syncs filesystem soundboard files with database entries.
        """
        self._logger.info("verifying soundboard db!")

        try:
            db_files = self.list_db_files()
        except (mysql.connector.Error, DatabaseUnavailableError) as e:
            self._logger.error(f"Database error while verifying: {e}")
            return

        try:
            # Get list of mp3 files on disk
            disk_files = set()
            for file in os.listdir("./soundboard"):
                if file.endswith(".mp3"):
                    disk_files.add(file)

            # Find db entries not on disk and remove them
            db_file_set = {entry[0] for entry in db_files}  # filenames from db
            for entry in db_files:
                if entry[0] not in disk_files:
                    self.remove_db_entry(entry[1])

            # Find disk files not in db and add them
            db_names = {entry[1] for entry in db_files}  # names from db
            for file in disk_files:
                name = file.replace(".mp3", "").lower()
                if name not in db_names:
                    try:
                        self.add_db_entry(file.lower(), name)
                    except ValueError:
                        continue

        except OSError as e:
            self._logger.error(f"File system error while verifying db: {e}")
        except (mysql.connector.Error, DatabaseUnavailableError) as e:
            self._logger.error(f"Database error while verifying db: {e}")


class BanDBManager(BaseDBManager):
    """
    Manages the bot ban database
    """
    def __init__(
        self,
        db_host: str,
        db_username: str,
        db_password: str,
        database_name: str,
        logger: logging.Logger
    ):
        super().__init__(db_host, db_username, db_password, database_name, logger, "Ban DB")

    def _create_table(self) -> None:
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
            self._logger.info("Ban table verified/created")
        except mysql.connector.Error as e:
            self._logger.error(f"Failed to create ban table: {e}")

    def add_ban(
        self,
        user_id: str,
        username: str,
        banned_by: str,
        duration: Optional[timedelta] = None,
        reason: Optional[str] = None
    ) -> Optional[datetime]:
        """
        Adds a ban to the database.

        Args:
            user_id: Discord user ID
            username: Discord username (for display purposes)
            banned_by: Admin who issued the ban
            duration: timedelta for ban length, or None for permanent
            reason: Optional reason for the ban

        Returns:
            The expiration datetime, or None for permanent bans
        """
        def _do_add() -> Optional[datetime]:
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
            self._logger.info(f"Added ban for user {username} (ID: {user_id}), expires: {expires_at}")
            return expires_at

        return self._execute_with_reconnect(_do_add)

    def remove_ban(self, user_id: str) -> bool:
        """Removes a ban from the database. Returns True if a ban was removed."""
        def _do_remove() -> bool:
            sql = "DELETE FROM discord_bans WHERE user_id = %s"
            self.my_cursor.execute(sql, (str(user_id),))
            self.db.commit()
            affected = self.my_cursor.rowcount
            self._logger.info(f"Removed ban for user ID: {user_id}, rows affected: {affected}")
            return affected > 0

        return self._execute_with_reconnect(_do_remove)

    def is_banned(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Checks if a user is currently banned.
        Returns ban info dict if banned, None if not banned.
        Automatically cleans up expired bans.
        """
        def _do_check() -> Optional[Dict[str, Any]]:
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

    def list_bans(self) -> List[Dict[str, Any]]:
        """Returns a list of all current bans (excluding expired ones)"""
        def _do_list() -> List[Dict[str, Any]]:
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


class VersionDBManager(BaseDBManager):
    """
    Manages version tracking for update notifications
    """
    def __init__(
        self,
        db_host: str,
        db_username: str,
        db_password: str,
        database_name: str,
        logger: logging.Logger
    ):
        super().__init__(db_host, db_username, db_password, database_name, logger, "Version DB")

    def _create_table(self) -> None:
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
            self._logger.info("Version table verified/created")
        except mysql.connector.Error as e:
            self._logger.error(f"Failed to create version table: {e}")

    def get_last_version(self) -> Optional[str]:
        """Gets the last notified version from the database"""
        def _do_get() -> Optional[str]:
            sql = "SELECT last_version FROM discord_version WHERE id = 1"
            self.my_cursor.execute(sql)
            result = self.my_cursor.fetchone()
            return result[0] if result else None

        return self._execute_with_reconnect(_do_get)

    def set_last_version(self, version: str) -> None:
        """Updates the last notified version in the database"""
        def _do_set() -> None:
            sql = """
                INSERT INTO discord_version (id, last_version, last_updated)
                VALUES (1, %s, %s)
                ON DUPLICATE KEY UPDATE
                    last_version = VALUES(last_version),
                    last_updated = VALUES(last_updated)
            """
            self.my_cursor.execute(sql, (version, datetime.now()))
            self.db.commit()
            self._logger.info(f"Version updated to {version}")

        return self._execute_with_reconnect(_do_set)

    def check_version_changed(self, current_version: str) -> bool:
        """
        Checks if the version has changed since last notification.
        Returns True if this is a new version, False otherwise.
        """
        last_version = self.get_last_version()
        return last_version != current_version


class AssistantDBManager(BaseDBManager):
    """
    Manages assistant personalities and the OpenAI conversation attached to each.

    Personalities used to live on OpenAI's servers as Assistant objects. The
    Assistants API is removed on 2026-08-26, so they are stored here instead and
    the instructions are passed on every request. Only the conversation id is
    held remotely.
    """
    def __init__(
        self,
        db_host: str,
        db_username: str,
        db_password: str,
        database_name: str,
        logger: logging.Logger
    ):
        super().__init__(db_host, db_username, db_password, database_name, logger, "Assistant DB")

    def _create_table(self) -> None:
        """Creates the assistant table if it doesn't exist"""
        try:
            sql = """
                CREATE TABLE IF NOT EXISTS discord_assistants (
                    guild_id VARCHAR(255) NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    instructions TEXT,
                    created_by VARCHAR(255),
                    created_at DATETIME,
                    conversation_id VARCHAR(255) NULL,
                    PRIMARY KEY (guild_id, name)
                )
            """
            self.my_cursor.execute(sql)
            self.db.commit()
            self._logger.info("Assistant table verified/created")
        except mysql.connector.Error as e:
            self._logger.error(f"Failed to create assistant table: {e}")

    def add_assistant(self, guild_id: str, name: str, instructions: str, created_by: str) -> bool:
        """
        Stores a new assistant personality.

        Returns:
            True if it was created, False if one with that name already exists
        """
        def _do_add() -> bool:
            sql = """
                INSERT INTO discord_assistants (guild_id, name, instructions, created_by, created_at)
                VALUES (%s, %s, %s, %s, %s)
            """
            val = (str(guild_id), name, instructions, created_by, datetime.now())
            self.my_cursor.execute(sql, val)
            self.db.commit()
            self._logger.info(f"Created assistant '{name}' in guild {guild_id} for {created_by}")
            return True

        try:
            return self._execute_with_reconnect(_do_add)
        except mysql.connector.errors.IntegrityError:
            return False

    def get_assistant(self, guild_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Returns the assistant with the given name, or None if it does not exist"""
        def _do_get() -> Optional[Dict[str, Any]]:
            sql = """
                SELECT guild_id, name, instructions, created_by, created_at, conversation_id
                FROM discord_assistants WHERE guild_id = %s AND name = %s
            """
            self.my_cursor.execute(sql, (str(guild_id), name))
            result = self.my_cursor.fetchone()

            if not result:
                return None

            return {
                'guild_id': result[0],
                'name': result[1],
                'instructions': result[2],
                'created_by': result[3],
                'created_at': result[4],
                'conversation_id': result[5],
            }

        return self._execute_with_reconnect(_do_get)

    def list_assistants(self, guild_id: str) -> List[str]:
        """Returns the names of every assistant in the given guild"""
        def _do_list() -> List[str]:
            sql = "SELECT name FROM discord_assistants WHERE guild_id = %s ORDER BY created_at"
            self.my_cursor.execute(sql, (str(guild_id),))
            return [row[0] for row in self.my_cursor.fetchall()]

        return self._execute_with_reconnect(_do_list)

    def remove_assistant(self, guild_id: str, name: str) -> bool:
        """Deletes an assistant. Returns True if one was deleted."""
        def _do_remove() -> bool:
            sql = "DELETE FROM discord_assistants WHERE guild_id = %s AND name = %s"
            self.my_cursor.execute(sql, (str(guild_id), name))
            self.db.commit()
            affected = self.my_cursor.rowcount
            self._logger.info(f"Removed assistant '{name}' from guild {guild_id}, rows affected: {affected}")
            return affected > 0

        return self._execute_with_reconnect(_do_remove)

    def set_conversation_id(self, guild_id: str, name: str, conversation_id: Optional[str]) -> None:
        """Stores the OpenAI conversation id an assistant is currently using"""
        def _do_set() -> None:
            sql = "UPDATE discord_assistants SET conversation_id = %s WHERE guild_id = %s AND name = %s"
            self.my_cursor.execute(sql, (conversation_id, str(guild_id), name))
            self.db.commit()

        self._execute_with_reconnect(_do_set)


def get_version_codename(version: Optional[str] = None) -> str:
    """Returns the release codename for the given version (defaults to the running one)"""
    return VERSION_CODENAMES.get(version or VERSION, UNKNOWN_VERSION_CODENAME)


def _write_json_atomic(filename: str, payload: dict) -> None:
    """
    Writes json to a file atomically.

    The payload is serialized to a temporary file in the same directory and then
    moved into place, so an interrupted or failed write can never leave the
    destination truncated or half-written.
    """
    directory = os.path.dirname(filename) or "."
    os.makedirs(directory, exist_ok=True)

    handle, temp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(handle, "w") as file:
            json.dump(payload, file, indent=4)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp_path, filename)
    except BaseException:
        try:
            os.remove(temp_path)
        except OSError:
            pass
        raise


def load_runtime_data(filename: str = RUNTIME_DATA_FILE) -> dict:
    """
    Loads the runtime data file.

    Returns an empty dict if the file does not exist yet. A corrupt file raises
    rather than being silently overwritten, so the existing data is not lost.
    """
    if not os.path.exists(filename):
        return {}

    with open(filename, "r") as file:
        return json.load(file)


def append_runtime_data(tag: str, data: Any, filename: str = RUNTIME_DATA_FILE) -> bool:
    """
    Appends an entry to a list in the runtime data file.

    Args:
        tag: The key of the list to append to, created if it does not exist
        data: The entry to append
        filename: Runtime data file to write to

    Returns:
        True if the entry was added, False if it was already present
    """
    runtime_data = load_runtime_data(filename)
    entries = runtime_data.setdefault(tag, [])

    if data in entries:
        return False

    entries.append(data)
    _write_json_atomic(filename, runtime_data)
    return True


def parse_ban_duration(duration_str: str) -> Optional[timedelta]:
    """
    Parses a duration string into a timedelta.
    Supports: Xm (minutes), Xh (hours), Xd (days), or 'x'/'permanent' for permanent bans.

    Args:
        duration_str: Duration string like "30m", "2h", "7d", or "permanent"

    Returns:
        timedelta for timed bans, None for permanent bans

    Raises:
        ValueError: For invalid formats
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


# Backward compatibility: expose settings attributes at module level
def __getattr__(name: str) -> Any:
    """Module-level attribute access for backward compatibility"""
    if settings is None:
        raise AttributeError(f"Settings not initialized. Call init() first.")

    if name in ('info_json', 'token', 'logger', 'soundboard_db', 'ban_db', 'version_db', 'assistant_db'):
        return getattr(settings, name)

    raise AttributeError(f"module 'settings' has no attribute '{name}'")
