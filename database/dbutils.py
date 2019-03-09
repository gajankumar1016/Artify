import mysql.connector
import secrets

class DatabaseAPIResource():
    def __enter__(self):
        class ArtifyDatabaseAPI:
            def __init__(self):
                self.dbconn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    passwd=secrets.dbpassword,
                    database="artifydatabase"
                )

                self.cursor = self.dbconn.cursor()

            def insert_user(self, username):
                assert(username)

                sql = "INSERT INTO user (username) VALUES (%s)"
                val = (username,)

                self.cursor.execute(sql, val)
                self.dbconn.commit()

        self.database_api = ArtifyDatabaseAPI()
        return self.database_api



    def __exit__(self, exc_type, exc_val, exc_tb):
        self.database_api.cursor.close()



if __name__ == '__main__':
    # Example usage of the Artify Database API
    with DatabaseAPIResource() as artifyDbAPI:
        artifyDbAPI.insert_user(username="ballislife2")
