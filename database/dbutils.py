import mysql.connector
import secrets

class DbApiInstance():
    def __enter__(self):
        class ArtifyDatabaseAPI:
            def __init__(self):
                self.dbconn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    passwd=secrets.dbpassword,
                    database="artifydatabase"
                )

                self.cursor = self.dbconn.cursor(buffered=True)

            def insert_user(self, username: str, password_hash: str, age=None, gender=None):
                assert(username)
                assert(password_hash)

                fields = ['username', 'password_hash']
                vals = [username, password_hash]
                if age:
                    fields.append('age')
                    vals.append(age)
                if gender:
                    fields.append('gender')
                    vals.append(gender)

                sql = "INSERT INTO user (" + ','.join(fields) +") VALUES (" + ','.join(["%s"] * len(fields)) + ")"

                self.cursor.execute(sql, vals)
                self.dbconn.commit()


            def user_exists(self, username):
                sql = "SELECT * FROM user WHERE username=%s"
                self.cursor.execute(sql, (username, ))
                result = self.cursor.fetchone()
                if result:
                    return True
                return False


            def verify_username_and_password(self, username, password_hash):
                sql = "SELECT * FROM user WHERE username=%s AND password_hash=%s"
                self.cursor.execute(sql, (username, password_hash))
                result = self.cursor.fetchone()
                if result:
                    return True
                return False


            def get_user(self, username, fields):
                assert(username)
                pass


            def execute_sql(self, raw_sql, vals=None, return_type=None):
                if vals:
                    self.cursor.execute(raw_sql, vals)
                else:
                    self.cursor.execute(raw_sql)

                if return_type == 'fetchall':
                    result = self.cursor.fetchall()
                    return result
                elif return_type == 'fetchone':
                    result = self.cursor.fetchone()
                    return result


            def insert_art(self, title: str, file_name: str, year=None, style=None):
                assert(title)
                assert(file_name)

                fields = ['title', 'file_name']
                vals = [title, file_name]
                if year:
                    fields.append('year')
                    vals.append(year)
                if style:
                    fields.append('style')
                    vals.append(style)

                sql = "INSERT INTO art (" + ','.join(fields) +") VALUES (" + ','.join(["%s"] * len(fields)) + ")"

                self.cursor.execute(sql, vals)
                self.dbconn.commit()


        self.database_api = ArtifyDatabaseAPI()
        return self.database_api



    def __exit__(self, exc_type, exc_val, exc_tb):
        self.database_api.cursor.close()
        self.database_api.dbconn.close()



if __name__ == '__main__':
    # Example usage of the Artify Database API
    with DbApiInstance() as artifyDbAPI:
        # TODO: set the demo up smarter so don't have to keep changeing username; could use random usernames
        artifyDbAPI.insert_user(username="ballislife15", password_hash="abcd123", gender="F", age=80)

        user_exists = artifyDbAPI.user_exists(username="ballislife50")
        print("User exists? ", user_exists)

        valid_login = artifyDbAPI.verify_username_and_password(username="ballislife3", password_hash="abcd123")
        print("Valid login? ", valid_login)

        print(artifyDbAPI.execute_sql("SELECT * FROM user", return_type="fetchall"))

