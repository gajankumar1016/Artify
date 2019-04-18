import mysql.connector
import pandas as pd

import sys
sys.path.insert(0, '..')
sys.path.insert(0, '../database')
from database.dbutils import DbApiInstance
from database.secrets import dbpassword

# Drop database and recreate
mydb = mysql.connector.connect(
        host="localhost",
        user="root",
        passwd=dbpassword,
    )

mycursor = mydb.cursor()

mycursor.execute("DROP DATABASE IF EXISTS artifydatabase")
mycursor.execute("CREATE DATABASE artifydatabase")
mycursor.close()
mydb.close()


# Create new connection for creating tables in the artifydatabase
mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd=dbpassword,
    database="artifydatabase"
)

mycursor = mydb.cursor()

mycursor.execute("SHOW DATABASES")

print("Current databases:")
for x in mycursor:
    print(x)

############################   USER  #################################
drop_table = """DROP TABLE IF EXISTS user;"""
mycursor.execute(drop_table)

create_user = \
"""CREATE TABLE user (
id INT AUTO_INCREMENT PRIMARY KEY,
username VARCHAR(64) NOT NULL UNIQUE,
password_hash VARCHAR(256) NOT NULL,
age INT,
gender VARCHAR(16),
location VARCHAR(64),
subject VARCHAR(64),
style VARCHAR(64)
);"""
mycursor.execute(create_user)
######################################################################


############################   ARTIST  ###############################
drop_table = """DROP TABLE IF EXISTS artist;"""
mycursor.execute(drop_table)

create_artist = \
"""CREATE TABLE artist (
id INT AUTO_INCREMENT PRIMARY KEY,
name VARCHAR(64) NOT NULL,
gender VARCHAR(16)
);"""
mycursor.execute(create_artist)
######################################################################


############################   ART   #################################
# TODO: May want to put some uniqueness constraints on this table

drop_table = """DROP TABLE IF EXISTS art;"""
mycursor.execute(drop_table)

create_art = \
"""CREATE TABLE art (
id INT AUTO_INCREMENT PRIMARY KEY,
title VARCHAR(128) NOT NULL,
description VARCHAR(512),
file_name VARCHAR(64) NOT NULL,
year VARCHAR(10),
price DOUBLE,
style VARCHAR(64),
artist_id INT,
owner_id INT,
FOREIGN KEY (artist_id) REFERENCES artist(id),
FOREIGN KEY (owner_id) REFERENCES user(id)
);"""
mycursor.execute(create_art)
######################################################################


############################   LIKES  ###########################################
# TODO: Think about desired update and delete behavior
# Possible extra fields: time of like

drop_table = """DROP TABLE IF EXISTS likes;"""
mycursor.execute(drop_table)

create_likes = \
"""CREATE TABLE likes (
user_id INTEGER,
art_id INTEGER,
FOREIGN KEY (user_id) REFERENCES user (id) ON DELETE RESTRICT ON UPDATE CASCADE,
FOREIGN KEY (art_id) REFERENCES art (id) ON DELETE RESTRICT ON UPDATE CASCADE,
CONSTRAINT PK_likes PRIMARY KEY (user_id, art_id)
);"""
mycursor.execute(create_likes)
#################################################################################


############################   TRANSACTION  ######################################
drop_table = """DROP TABLE IF EXISTS transaction;"""
mycursor.execute(drop_table)

create_transaction = \
"""CREATE TABLE transaction (
id INT AUTO_INCREMENT PRIMARY KEY,
seller_id INTEGER,
buyer_id INTEGER,
art_id INTEGER,
status VARCHAR(16),
FOREIGN KEY (seller_id) REFERENCES user (id) ON DELETE RESTRICT,
FOREIGN KEY (buyer_id) REFERENCES user (id) ON DELETE RESTRICT,
FOREIGN KEY (art_id) REFERENCES art (id) ON DELETE RESTRICT
);"""
mycursor.execute(create_transaction)
###################################################################################

############################   SIMILARITY   #######################################
drop_table = """DROP TABLE IF EXISTS similarity;"""
mycursor.execute(drop_table)

create_similarity = \
"""CREATE TABLE similarity (
base_art_id INTEGER,
target_art_id INTEGER,
cos_sim DOUBLE,
FOREIGN KEY (base_art_id) REFERENCES art(id) ON DELETE CASCADE,
FOREIGN KEY (target_art_id) REFERENCES art(id) ON DELETE CASCADE,
CONSTRAINT PK_similarity PRIMARY KEY (base_art_id, target_art_id)
);"""
mycursor.execute(create_similarity)
###################################################################################

mycursor.close()
mydb.close()

# Add starter artworks
df = pd.read_csv('./artinfo.csv', sep="|")

with DbApiInstance() as artifyDbAPI:
    for index, row in df.iterrows():
        artist = artifyDbAPI.get_artist_by_name(row["Artist"])
        if not artist:
            artist = artifyDbAPI.insert_artist(row["Artist"])

        artifyDbAPI.insert_art(IMAGES_DIR="../devimages", title=row["Title"], file_name=row["FileName"],
                               year=row["Year"], style=row["Style"], artist_id=artist.id)
