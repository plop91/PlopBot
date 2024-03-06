import mysql.connector
from mysql.connector import errorcode
from datetime import datetime

import logging


class OpenAIDatabaseManager:
    """
    This class is for managing the openai database
    """

    def __init__(self, db_host: str, db_username: str, db_password: str, database_name: str):
        """
        Constructor for the openai database manager
        :param db_host: Database host
        :param db_username: Database username
        :param db_password: Database password
        :param database_name: Database name
        """
        self.db = None
        self.my_cursor = None

        self.db_host = db_host
        self.db_username = db_username
        self.db_password = db_password
        self.database_name = database_name

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
                # settings.logger.warning("Soundboard username or password is Bad")
                print("Soundboard user name or password is Bad")
            elif e.errno == errorcode.ER_BAD_DB_ERROR:
                # settings.logger.warning("Database does not exist")
                print("Database does not exist")
            else:
                # settings.logger.warning(e)
                print(e)

    def disconnect(self):
        """Disconnects from the database"""
        self.my_cursor.close()
        self.db.close()

    # user
    def add_user(self, user):
        """
        Adds a new user to the database
        :param user: User to add
        :return: None
        :raises: ValueError if the user already exists
        :raises: ConnectionError if the user cannot be added because the database is not connected
        :raises: Exception if the user cannot be added for any other reason
        """
        # TODO: add error handling
        sql = "INSERT INTO usernames (username, date_created) VALUES (%s, %s)"
        val = (user, datetime.now())
        self.my_cursor.execute(sql, val)
        self.db.commit()

    def get_users(self):
        """
        Gets the users from the database
        :return: List of users
        :raises: ConnectionError if the user cannot be added because the database is not connected
        :raises: Exception if the list of users cannot be retrieved for any other reason
        """
        # TODO: add error handling
        sql = "SELECT username FROM usernames"
        self.my_cursor.execute(sql)
        result = self.my_cursor.fetchall()
        return result

    def remove_user(self, user):
        """
        Removes a user from the database
        :param user: User to remove
        :return: None
        :raises: ValueError if the user does not exist
        :raises: ConnectionError if the user cannot be added because the database is not connected
        :raises: Exception if the user cannot be removed for any other reason
        """
        # TODO: add error handling
        sql = "DELETE FROM usernames WHERE username = %s"
        adr = (user,)
        self.my_cursor.execute(sql, adr)
        self.db.commit()


    # blacklist
    def add_blacklist(self, blacklist):
        """
        Adds a new blacklist to the database
        :param blacklist: Blacklist to add
        :return: None
        :raises: ValueError if the blacklist already exists
        :raises: ConnectionError if the blacklist cannot be added because the database is not connected
        :raises: Exception if the blacklist cannot be added for any other reason
        """
        # TODO: add error handling
        sql = "INSERT INTO blacklists (blacklist, date_created) VALUES (%s, %s)"
        val = (blacklist, datetime.now())
        self.my_cursor.execute(sql, val)
        self.db.commit()

    def blacklisted(self, user):
        """
        Checks if a user is blacklisted
        :param user: User to check
        :return: True if the user is blacklisted, False otherwise
        :raises: ConnectionError if the blacklist cannot be added because the database is not connected
        :raises: Exception if the blacklist cannot be added for any other reason
        """
        # TODO: add error handling
        try:
            blacklist = self.get_blacklists()
            if user in blacklist:
                return True
            return False
        except Exception as e:
            raise e

    def get_blacklists(self):
        """
        Gets the blacklists from the database
        :return: List of blacklisted users
        :raises: ConnectionError if the blacklist cannot be added because the database is not connected
        :raises: Exception if the list of blacklists cannot be retrieved for any other reason
        """
        # TODO: add error handling
        pass

    def remove_blacklist(self, blacklist):
        """
        Removes a blacklist from the database
        :param blacklist: Blacklist to remove
        :return: None
        :raises: ValueError if the blacklist does not exist
        :raises: ConnectionError if the blacklist cannot be added because the database is not connected
        :raises: Exception if the blacklist cannot be removed for any other reason
        """
        # TODO: add error handling
        pass

    # assistants
    def add_assistant(self, assistant):
        """
        Adds an assistant to the database
        :param assistant: Assistant to add
        :return: None
        :raises: ValueError if the assistant already exists
        :raises: ConnectionError if the assistant cannot be added because the database is not connected
        :raises: Exception if the assistant cannot be added for any other reason
        """
        # TODO: add error handling
        pass

    def get_assistants(self):
        """
        Gets the assistants from the database
        :return: List of assistants
        :raises: ConnectionError if the assistant cannot be added because the database is not connected
        :raises: Exception if the list of assistants cannot be retrieved for any other reason
        """
        # TODO: add error handling
        pass

    def remove_assistant(self, assistant):
        """
        Removes an assistant from the database
        :param assistant: Assistant to remove
        :return: None
        :raises: ValueError if the assistant does not exist
        :raises: ConnectionError if the assistant cannot be added because the database is not connected
        :raises: Exception if the assistant cannot be removed for any other reason
        """
        # TODO: add error handling
        pass

    # threads
    def add_thread(self, thread):
        """
        Adds a thread to the database
        :param thread: Thread to add
        :return: None
        :raises: ValueError if the thread already exists
        :raises: ConnectionError if the thread cannot be added because the database is not connected
        :raises: Exception if the thread cannot be added for any other reason
        """
        # TODO: add error handling
        pass

    def get_threads(self):
        """
        Gets the threads from the database
        :return: List of threads
        :raises: ConnectionError if the thread cannot be added because the database is not connected
        :raises: Exception if the list of threads cannot be retrieved for any other reason
        """
        # TODO: add error handling
        pass

    def remove_thread(self, thread):
        """
        Removes a thread from the database
        :param thread: Thread to remove
        :return: None
        :raises: ValueError if the thread does not exist
        :raises: ConnectionError if the thread cannot be added because the database is not connected
        :raises: Exception if the thread cannot be removed for any other reason
        """
        # TODO: add error handling
        pass

    def update_usage(self, username, function, count=1, month=None, year=None):
        """
        Updates the usage of a user for a function, adding 1 to the count for the current month and year or the given
        year, if the user has not used the function that month and year before it will be added to the database.
        :param: username: Username to update
        :param: function: Function to update
        :param: count: Count to add
        :param: month: Month to update
        :param: year: Year to update
        :return: None
        :raises: ValueError if the assistant or thread does not exist
        :raises: ConnectionError if the thread cannot be added because the database is not connected
        :raises: Exception if the thread cannot be removed for any other reason
        """
        # TODO: add error handling
        pass

    def get_usage(self, username, function, month=None, year=None):
        """
        Gets the usage of a user for a function for the current month and year or the given month and year
        :param: username: Username to get
        :param: function: Function to get
        :param: month: Month to get Default: Current month
        :param: year: Year to get Default: Current year
        :return: Int number of times the user has used the function
        :raises: ValueError if the assistant or thread does not exist
        :raises: ConnectionError if the thread cannot be added because the database is not connected
        :raises: Exception if the thread cannot be removed for any other reason
        """
        # TODO: add error handling
        pass

    def get_user_functions(self, username, month=None, year=None):
        """
        Gets the functions a user has used for the current month and year or the given month and year
        :param: username: Username to get
        :param: month: Month to get Default: Current month
        :param: year: Year to get Default: Current year
        :return: None
        :raises: ValueError if the assistant or thread does not exist
        :raises: ConnectionError if the thread cannot be added because the database is not connected
        :raises: Exception if the thread cannot be removed for any other reason
        """
        # TODO: add error handling
        pass

    def get_function_users(self, function, month=None, year=None):
        """
        Gets the users that have used a function for the current month and year or the given month and year
        :param: function: Function to get
        :param: month: Month to get Default: Current month
        :param: year: Year to get Default: Current year
        :return: None
        :raises: ValueError if the assistant or thread does not exist
        :raises: ConnectionError if the thread cannot be added because the database is not connected
        :raises: Exception if the thread cannot be removed for any other reason
        """
        # TODO: add error handling
        pass
