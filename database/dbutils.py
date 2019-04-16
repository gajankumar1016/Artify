import sys
import os
sys.path.insert(0, "..")
sys.path.insert(0, "../similarity_model")
import mysql.connector
from .secrets import dbpassword
# import subprocess
# from similarity_model import cos_sim


class ArtDetail:
    fields = ('id', 'title', 'description', 'file_name', 'year', 'price', 'style', 'artist', 'is_liked')

    def __init__(self, **kwargs):
        for field in self.fields:
            setattr(self, field, kwargs.get(field, None))

    def __repr__(self):
        repr_str = "<"
        for field in self.fields:
            repr_str += " |{}: {}| ".format(field, str(getattr(self, field)))
        return repr_str + ">"


def art_tuple_to_art_detail_obj(art_tuple, art_join_like_join_artist=False, art_join_artist=False):
    if art_join_like_join_artist:
        return ArtDetail(id=art_tuple[0], title=art_tuple[1], file_name=art_tuple[3], year=art_tuple[4],
                         style=art_tuple[6], is_liked=bool(art_tuple[9]), artist=art_tuple[12])
    elif art_join_artist:
        foo = ArtDetail(id=art_tuple[0], title=art_tuple[1], file_name=art_tuple[3], year=art_tuple[4],
                         style=art_tuple[6], artist=art_tuple[9])
        print(foo)
        return foo

    return ArtDetail(id=art_tuple[0], title=art_tuple[1], file_name=art_tuple[3], year=art_tuple[4], style=art_tuple[6])


class ArtistDetail:
    def __init__(self, **kwargs):
        for field in ('id', 'name', 'gender'):
            setattr(self, field, kwargs.get(field, None))


def artist_tuple_to_artist_detail_obj(artist_tuple):
    return ArtistDetail(id=artist_tuple[0], name=artist_tuple[1], gender=artist_tuple[2])


class UserDetail:
    def __init__(self, **kwargs):
        for field in ('username', 'age', 'gender', 'location', 'subject', 'style'):
            setattr(self, field, kwargs.get(field, None))

def profile_tuple_to_profile_detail_obj(user_tuple):
    return UserDetail(username=user_tuple[1], age=user_tuple[3], gender="M" if user_tuple[4] else "F",
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


            def edit_user(self, id, age, gender, location):
                assert(id)

                fields = ['age', 'gender', 'location']
                vals = [age, gender, location]

                sql = "UPDATE user SET "

                for i in range(len(fields)):
                    sql += fields[i] + "=%s,"

                sql = sql[:len(sql) - 1]
                sql += " WHERE id=" + str(id)

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
                JOIN artist ON art.artist_id = artist.id
                LIMIT %s;
                """
                self.cursor.execute(sql, (user_id, limit))
                art_tuples = self.cursor.fetchall()
                return [art_tuple_to_art_detail_obj(a, art_join_like_join_artist=True) for a in art_tuples]


            def get_user_art(self, user_id):
                sql = "SELECT * FROM art WHERE owner_id = %s"
                sql = """
                SELECT *
                FROM art LEFT JOIN likes ON art.id = likes.art_id AND likes.user_id = %s
                JOIN artist ON art.artist_id = artist.id
                WHERE owner_id = %s"""

                self.cursor.execute(sql, (user_id, user_id))
                art_tuples = self.cursor.fetchall()
                return [art_tuple_to_art_detail_obj(a, art_join_like_join_artist=True) for a in art_tuples]


            def get_art_by_id(self, artid):
                sql = """
                SELECT * 
                FROM art 
                LEFT JOIN likes ON art.id = likes.art_id 
                JOIN artist ON art.artist_id = artist.id 
                WHERE art.id = %s;"""
                self.cursor.execute(sql, (artid,))
                art = self.cursor.fetchone()
                return art_tuple_to_art_detail_obj(art, art_join_like_join_artist=True)

            #Pass in a list of conditions (eg:["condA", "condB"])
            #Note: Natural join for now
            def get_art_by_cond(self, conds):
                sql = "SELECT * FROM art NATURAL JOIN artist WHERE "
                for i in range(len(conds)):
                    if len(conds)>1:
                        sql += '('
                    sql += conds[i]
                    if len(conds)>1:
                        sql += ')'
                    if i < len(conds) - 1:
                        sql += ' AND '
                sql += ';'
                if len(conds) == 0:
                    sql = "SELECT * FROM art NATURAL JOIN artist;"
                self.cursor.execute(sql)
                art_tuples = self.cursor.fetchall()
                return [art_tuple_to_art_detail_obj(a, art_join_artist=True) for a in art_tuples]

            #Gets unique styles for search options
            def get_unique_styles(self):
                sql = "SELECT DISTINCT style FROM art;"
                self.cursor.execute(sql)
                styles_tuples = self.cursor.fetchall()
                if not styles_tuples:
                    return None
                return styles_tuples

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


            def insert_artist(self, name:str, gender = None):
                fields = ['name', 'gender']
                vals = [name, gender]
                sql = "INSERT INTO artist (" + ','.join(fields) + ") VALUES (" + ','.join(["%s"] * len(fields)) + ");"
                self.cursor.execute(sql, vals)
                self.dbconn.commit()
                return self.get_artist_by_id(self.cursor.lastrowid)

            def get_artist_by_id(self, id):
                sql = "SELECT * FROM artist WHERE id = %s;"
                self.cursor.execute(sql, (id,))
                artist = self.cursor.fetchone()
                if not artist:
                    return None
                return artist_tuple_to_artist_detail_obj(artist)

            #Get all artists for search options 
            def get_all_artists(self):
                sql = "SELECT * FROM artist ORDER BY name;"
                self.cursor.execute(sql)
                artists = self.cursor.fetchall()
                if not artists:
                    return None
                return [artist_tuple_to_artist_detail_obj(artist) for artist in artists]


            def get_artist_by_name(self, name):
                sql = "SELECT * FROM artist WHERE name = %s;"
                self.cursor.execute(sql, (name,))
                artist = self.cursor.fetchone()
                if not artist:
                    return None
                return artist_tuple_to_artist_detail_obj(artist)


            def insert_art(self, IMAGES_DIR, title: str, file_name: str, year=None, style=None, artist_id = None, owner_id=None):
                assert(IMAGES_DIR)
                assert(title)
                assert(file_name)

                fields = ['title', 'file_name', 'year', 'style', 'artist_id', 'owner_id']
                vals = [title, file_name, year, style, artist_id, owner_id]

                sql = "INSERT INTO art (" + ','.join(fields) +") VALUES (" + ','.join(["%s"] * len(fields)) + ");"

                self.cursor.execute(sql, vals)
                self.dbconn.commit()

                # May want to create separate processes to handle similarity computation
                #self.compute_similarities(IMAGES_DIR=IMAGES_DIR, base_id=self.cursor.lastrowid, base_img_fname=file_name)

                # path = os.path.abspath(__file__)
                # dirname = os.path.dirname(path)
                # script_path = os.path.join(dirname, 'compute_simscore.py')
                # cmd_str = "python {} {} {} {}".format(script_path, IMAGES_DIR, self.cursor.lastrowid, str(file_name))
                #
                # proc = subprocess.Popen([cmd_str], shell=True, stdin=None, stdout=None, stderr=None, close_fds=True)


            # def compute_similarities(self, IMAGES_DIR, base_id, base_img_fname):
            #     base_img_path = os.path.join(IMAGES_DIR, base_img_fname)
            #     sql = "SELECT id, file_name FROM art WHERE id <> {}".format(base_id)
            #     self.cursor.execute(sql)
            #     arts = self.cursor.fetchall()
            #     print("Comparing art # {} with: ".format(base_id), arts)
            #     for art in arts:
            #         target_art_id = art[0]
            #         target_image_path = os.path.join(IMAGES_DIR, art[1])
            #
            #         sql = "INSERT INTO similarity (base_art_id, target_art_id, cos_sim) VALUES ({}, {}, {});"\
            #             .format(base_id, target_art_id, cos_sim(base_img_path, target_image_path))
            #         self.cursor.execute(sql)
            #
            #     self.dbconn.commit()


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
