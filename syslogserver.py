import socketserver
from datetime import datetime
import time

import mysql.connector as mariadb

#https://dev.mysql.com/doc/connector-python/en/connector-python-example-cursor-transaction.html
def write_to_db(sql_statement, cursor, debug = False, variables = None):

    try:
        if debug == True:
            print('SQL statement: {}'.format(sql_statement))
            print('Variables: {}'.format(variables))
        #https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-execute.html
        #this prevents SQL injections!!!
        #http://bobby-tables.com/python
        cursor.execute(operation = sql_statement, params = variables)

        if debug == True:
            print('The last inserted id was: {}'.format(cursor.lastrowid))
        #https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlcursor-close.html
        cursor.close()
    except mariadb.Error as error:
        print('Error: {}'.format(error))

    return None

def create_db(db_name, cursor, debug = False):

    sql_statement = 'CREATE DATABASE IF NOT EXISTS {}'.format(db_name)

    write_to_db(sql_statement, cursor, debug)

    return None

def create_table(db_name, table_name, cursor, debug = False):

    #a separate id column as primary key is used to allow same timestamp values
    #https://docs.python.org/3/reference/lexical_analysis.html#string-literal-concatenation
    #be aware of https://mariadb.com/kb/en/library/reserved-words, therefore column is not
    #named "timestamp"
    sql_statement = (
        'CREATE TABLE IF NOT EXISTS {}.{}('
        'id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,'
        'inserted_utc DATETIME,'
        'message VARCHAR(256))').format(db_name, table_name)

    write_to_db(sql_statement, cursor, debug)

    return None

def insert_data(db_name, table_name, cursor, data, debug=False):

    #https://docs.python.org/3/reference/lexical_analysis.html#string-literal-concatenation
    sql_statement = (
        'INSERT INTO {}.{} SET '
        'inserted_utc = %s,'
        'message = %s').format(db_name, table_name)
    variables = (datetime.now(), data)

    write_to_db(sql_statement, cursor, variables=variables)

    return None

#https://docs.python.org/3/library/socketserver.html
class SyslogUDPHandler(socketserver.BaseRequestHandler):
    """
    Decodes syslog data and add timestamp.

    This class takes the recieved syslog entries and writes them to the database.
    """

    def handle(self):

        #open mariadb connection for creating database and table
        try:
            #https://dev.mysql.com/doc/connector-python/en/connector-python-example-connecting.html
            mariadb_connection = mariadb.connect(user = self.server.db_user, password = self.server.db_password, host = self.server.db_host, port = self.server.db_port)
        except mariadb.Error as error:
            print('Error: {}'.format(error))

        data = bytes.decode(self.request[0].strip(), encoding="utf-8")

        cursor = mariadb_connection.cursor()
        insert_data(self.server.db_name, self.server.table_name, cursor, data)

        #https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlconnection-commit.html
        mariadb_connection.commit()

        #https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlconnection-close.html
        mariadb_connection.close()

        print('At {} recieved following message: {}'.format(time.time(), data))

if __name__ == "__main__":

    HOST, PORT = "0.0.0.0", 12312

    db_name = 'logging'
    table_name = 'logs'
    db_user = 'example_user'
    db_password = 'example_password'
    db_host = '192.168.312.312'
    #default MariaDB port
    db_port = 3306

    #open mariadb connection for creating database and table
    try:
        #https://dev.mysql.com/doc/connector-python/en/connector-python-example-connecting.html
        mariadb_connection = mariadb.connect(user = db_user, password = db_password, host = db_host, port = db_port)
    except mariadb.Error as error:
        print('Error: {}'.format(error))

    #every time a new cursor is created because the old one gets closed 
    #in the called write_to_db function
    cursor = mariadb_connection.cursor()
    create_db(db_name, cursor)

    cursor = mariadb_connection.cursor()
    create_table(db_name, table_name, cursor)

    #https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlconnection-commit.html
    mariadb_connection.commit()

    #https://dev.mysql.com/doc/connector-python/en/connector-python-api-mysqlconnection-close.html
    mariadb_connection.close()

    server = socketserver.UDPServer((HOST, PORT), SyslogUDPHandler)
    #self defined variables which are needed in handle()
    #https://stackoverflow.com/questions/6875599/with-python-socketserver-how-can-i-pass-a-variable-to-the-constructor-of-the-han
    server.db_name = db_name
    server.table_name = table_name
    server.db_user = db_user
    server.db_password = db_password
    server.db_host = db_host
    server.db_port = db_port

    #handle requests until explicit shutdown(), see python docs
    server.serve_forever()
