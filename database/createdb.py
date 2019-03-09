"""
Only need to run this file once.
"""

import mysql.connector
import secrets


if __name__ == '__main__':
    mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd=secrets.dbpassword,
    )

    mycursor = mydb.cursor()

    mycursor.execute("CREATE DATABASE artifydatabase")

