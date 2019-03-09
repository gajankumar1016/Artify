import mysql.connector
import secrets


# Have to run following command to create database first
# mycursor.execute("CREATE DATABASE mydatabase")


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd=secrets.dbpassword,
    database="artifydatabase"
)


mycursor = mydb.cursor()

mycursor.execute("SHOW DATABASES")

for x in mycursor:
    print(x)

############################   ART   #################################
drop_table = """DROP TABLE IF EXISTS art;"""
mycursor.execute(drop_table)

create_art = \
"""CREATE TABLE art (
ID INT,
FILE_NAME VARCHAR(20) NOT NULL,
YEAR VARCHAR(10),
PRICE DOUBLE,
STYLE VARCHAR(20));"""
mycursor.execute(create_art)

############################   ARTIST  ###############################
drop_table = """DROP TABLE IF EXISTS artist;"""
mycursor.execute(drop_table)

create_artist = \
"""CREATE TABLE artist (
ID INT,
NAME VARCHAR(64));"""
mycursor.execute(create_artist)

mydb.close()