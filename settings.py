from utility.tools import readJson
import mysql.connector
import sys

global json
global db
global my_cursor
global token


def init(json_filename="info.json", db_host="127.0.0.1", db_username="admin", db_password="password",
         db_database="discord"):
    testing = True

    if len(sys.argv) == 2:
        if "false" in sys.argv[1] or "False" in sys.argv[1]:
            testing = False

    global json
    json = readJson(json_filename)

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
