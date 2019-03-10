import mysql.connector
import secrets

# HAVE TO RUN createdb.py FIRST (and just once)!

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

############################   ARTIST  ###############################
drop_table = """DROP TABLE IF EXISTS artist;"""
mycursor.execute(drop_table)

create_artist = \
"""CREATE TABLE artist (
id INT AUTO_INCREMENT PRIMARY KEY,
name VARCHAR(64) NOT NULL
);"""
mycursor.execute(create_artist)
######################################################################


############################   ART   #################################
drop_table = """DROP TABLE IF EXISTS art;"""
mycursor.execute(drop_table)

create_art = \
"""CREATE TABLE art (
id INT AUTO_INCREMENT PRIMARY KEY,
title VARCHAR(128) NOT NULL,
file_name VARCHAR(20) NOT NULL,
year VARCHAR(10),
price DOUBLE,
style VARCHAR(20),
artistID INT,
FOREIGN KEY (artistID) REFERENCES artist(id)
);"""
mycursor.execute(create_art)
####################################################################


############################   USER  ###############################
drop_table = """DROP TABLE IF EXISTS user;"""
mycursor.execute(drop_table)

create_user = \
"""CREATE TABLE user (
id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(64) NOT NULL UNIQUE
);"""
mycursor.execute(create_user)
####################################################################


############################   LIKES  ###########################################
# TODO: Think about desired update and delete behavior
# Possible extra fields: time of like

drop_table = """DROP TABLE IF EXISTS likes;"""
mycursor.execute(drop_table)

create_likes = \
"""CREATE TABLE likes (
user_id INTEGER NOT NULL,
art_id INTEGER NOT NULL,
FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE RESTRICT ON UPDATE CASCADE,
FOREIGN KEY (art_id) REFERENCES art (id) ON DELETE RESTRICT ON UPDATE CASCADE
);"""
mycursor.execute(create_likes)
#################################################################################


mydb.close()