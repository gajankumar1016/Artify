import sys
import os
sys.path.insert(0, "..")
sys.path.insert(0, "../similarity_model")
from similarity_model import cos_sim
import mysql.connector
from .secrets import dbpassword

class ArtDetail:
    def __init__(self, **kwargs):
        for field in ('id', 'title', 'description', 'file_name', 'year', 'price', 'style', 'artist', 'is_liked'):
            setattr(self, field, kwargs.get(field, None))

def art_tuple_to_art_detail_obj(art_tuple, includes_like_status=False):
    if includes_like_status:
        return ArtDetail(id=art_tuple[0], title=art_tuple[1], file_name=art_tuple[3], year=art_tuple[4],
                         style=art_tuple[6], is_liked=bool(art_tuple[9]))

    return ArtDetail(id=art_tuple[0], title=art_tuple[1], file_name=art_tuple[3], year=art_tuple[4], style=art_tuple[6])


class UserDetail:
    def __init__(self, **kwargs):
        for field in ('username', 'age', 'gender', 'location', 'subject', 'style'):
            setattr(self, field, kwargs.get(field, None))

def profile_tuple_to_profile_detail_obj(user_tuple):
    return UserDetail(username=user_tuple[1], age=user_tuple[3], gender=user_tuple[4],
                          location=user_tuple[5])



class DbApiInstance():
    def __enter__(self):
        class ArtifyDatabaseAPI:
            def __init__(self):
                self.dbconn = mysql.connector.connect(
                    host="localhost",
                    user="root",
                    passwd=dbpassword,
                    database="artifydatabase"
                )

                self.cursor = self.dbconn.cursor(buffered=True)


            def insert_user(self, username: str, password_hash: str, age=None, gender=None, location=None, subject=None, style=None):
                assert(username)
                assert(password_hash)

                fields = ['username', 'password_hash', 'location', 'subject', 'style']
                vals = [username, password_hash, location, subject, style]
                if age:
                    fields.append('age')
                    vals.append(age)
                if gender:
                    fields.append('gender')
                    vals.append(gender)

                sql = "INSERT INTO user (" + ','.join(fields) +") VALUES (" + ','.join(["%s"] * len(fields)) + ");"

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


            def get_user_by_user_id(self, user_id):
                assert(user_id)
                sql = "SELECT * FROM user WHERE id=%s;"
                self.cursor.execute(sql, (user_id,))
                result = self.cursor.fetchone()
                return profile_tuple_to_profile_detail_obj(result)


            def get_recommended_art(self, user_id, limit=20):
                sql = "SELECT * FROM likes WHERE user_id = %s"
                self.cursor.execute(sql, (user_id,))
                likes = self.cursor.fetchall()
                # TODO: Do a bunch of joins instead and actually make a useful query

                sql = """
                SELECT *
                FROM art LEFT JOIN likes ON art.id = likes.art_id AND likes.user_id = %s
                LIMIT %s;
                """
                self.cursor.execute(sql, (user_id, limit))
                art_tuples = self.cursor.fetchall()
                return [art_tuple_to_art_detail_obj(a, includes_like_status=True) for a in art_tuples]


            def get_user_art(self, user_id):
                sql = "SELECT * FROM art WHERE owner_id = %s"
                self.cursor.execute(sql, (user_id,))
                art_tuples = self.cursor.fetchall()
                return [art_tuple_to_art_detail_obj(a) for a in art_tuples]


            def get_art_by_id(self, artid):
                sql = "SELECT * FROM art LEFT JOIN likes ON art.id = likes.art_id WHERE art.id = %s;"
                self.cursor.execute(sql, (artid,))
                art = self.cursor.fetchone()
                return art_tuple_to_art_detail_obj(art, includes_like_status=True)


            def delete_art(self, art_id):
                sql = "DELETE FROM art WHERE id = %s;"
                self.cursor.execute(sql, (art_id, ))
                self.dbconn.commit()


            def insert_like(self, user_id, art_id):
                sql = "INSERT INTO likes (user_id, art_id) VALUES (%s, %s);"
                self.cursor.execute(sql, (user_id, art_id))
                self.dbconn.commit()


            def does_like_exist(self, user_id, art_id):
                sql = "SELECT * FROM likes WHERE user_id = %s AND art_id = %s;"
                self.cursor.execute(sql, (user_id, art_id))
                like_exists = bool(self.cursor.fetchone())
                return like_exists


            def delete_like(self, user_id, art_id):
                sql = "DELETE FROM likes WHERE user_id = %s AND art_id = %s"
                self.cursor.execute(sql, (user_id, art_id))
                self.dbconn.commit()


            def insert_art(self, IMAGES_DIR, title: str, file_name: str, year=None, style=None, owner_id=None):
                assert(IMAGES_DIR)
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
                if owner_id:
                    fields.append('owner_id')
                    vals.append(owner_id)

                sql = "INSERT INTO art (" + ','.join(fields) +") VALUES (" + ','.join(["%s"] * len(fields)) + ");"

                self.cursor.execute(sql, vals)
                self.dbconn.commit()

                # May want to create separate processes to handle similarity computation
                self._compute_similarities(IMAGES_DIR=IMAGES_DIR, base_id=self.cursor.lastrowid, base_img_fname=file_name)


            def _compute_similarities(self, IMAGES_DIR, base_id, base_img_fname):
                base_img_path = os.path.join(IMAGES_DIR, base_img_fname)
                sql = "SELECT id, file_name FROM art WHERE id <> {}".format(base_id)
                self.cursor.execute(sql)
                arts = self.cursor.fetchall()
                print("Comparing art # {} with: ".format(base_id), arts)
                for art in arts:
                    target_art_id = art[0]
                    target_image_path = os.path.join(IMAGES_DIR, art[1])

                    sql = "INSERT INTO similarity (base_art_id, target_art_id, cos_sim) VALUES ({}, {}, {});"\
                        .format(base_id, target_art_id, cos_sim(base_img_path, target_image_path))
                    self.cursor.execute(sql)

                self.dbconn.commit()


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


        self.database_api = ArtifyDatabaseAPI()
        return self.database_api


    def __exit__(self, exc_type, exc_val, exc_tb):
        self.database_api.cursor.close()
        self.database_api.dbconn.close()



if __name__ == '__main__':
    # Example usage of the Artify Database API
    with DbApiInstance() as artifyDbAPI:
        # TODO: set the demo up smarter so don't have to keep changeing username; could use random usernames
        # artifyDbAPI.insert_user(username="ballislife15", password_hash="abcd123", gender="F", age=80)

        # user_exists = artifyDbAPI.user_exists(username="ballislife50")
        # print("User exists? ", user_exists)

        # valid_login = artifyDbAPI.verify_username_and_password(username="ballislife3", password_hash="abcd123")
        # print("Valid login? ", valid_login)
        user_id = 1

        sql = "SELECT * FROM user WHERE id=%s;"
        artifyDbAPI.cursor.execute(sql, (user_id,))
        result = artifyDbAPI.cursor.fetchone()

        # result = artifyDbAPI.execute_sql("SELECT * FROM user WHERE id=1", return_type="fetchall")
        print(result[0])
