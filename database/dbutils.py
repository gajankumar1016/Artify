import sys
import os
sys.path.insert(0, "..")
sys.path.insert(0, "../similarity_model")
import mysql.connector
from .secrets import dbpassword
# import subprocess
# from similarity_model import cos_sim
import numpy as np


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
                         style=art_tuple[6], artist=art_tuple[10])
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

class MF():

    def __init__(self, R, K, alpha, beta, iterations):
        #based on https://www.analyticsvidhya.com/blog/2018/06/comprehensive-guide-recommendation-engine-python/

        #Perform matrix factorization to predict empty
        #entries in a matrix.

        #Arguments
        #- R (ndarray)   : user-item rating matrix
        #- K (int)       : number of latent dimensions
        #- alpha (float) : learning rate
        #- beta (float)  : regularization parameter


        self.R = R
        self.num_users, self.num_items = R.shape
        self.K = K
        self.alpha = alpha
        self.beta = beta
        self.iterations = iterations

    def train(self):
        # Initialize user and item latent feature matrice
        self.P = np.random.normal(scale=1./self.K, size=(self.num_users, self.K))
        self.Q = np.random.normal(scale=1./self.K, size=(self.num_items, self.K))

        # Initialize the biases
        self.b_u = np.zeros(self.num_users)
        self.b_i = np.zeros(self.num_items)
        self.b = np.mean(self.R[np.where(self.R != 0)])

        # Create a list of training samples
        self.samples = [
            (i, j, self.R[i, j])
            for i in range(self.num_users)
            for j in range(self.num_items)
            if self.R[i, j] > 0
        ]

        # Perform stochastic gradient descent for number of iterations
        training_process = []
        for i in range(self.iterations):
            np.random.shuffle(self.samples)
            self.sgd()
            mse = self.mse()
            training_process.append((i, mse))
            if (i+1) % 10 == 0:
                print("Iteration: %d ; error = %.4f" % (i+1, mse))

        return training_process

    def mse(self):

        #A function to compute the total mean square error

        xs, ys = self.R.nonzero()
        predicted = self.full_matrix()
        error = 0
        for x, y in zip(xs, ys):
            error += pow(self.R[x, y] - predicted[x, y], 2)
        return np.sqrt(error)

    def sgd(self):

        #Perform stochastic gradient descent

        for i, j, r in self.samples:
            # Computer prediction and error
            prediction = self.get_rating(i, j)
            e = (r - prediction)

            # Update biases
            self.b_u[i] += self.alpha * (e - self.beta * self.b_u[i])
            self.b_i[j] += self.alpha * (e - self.beta * self.b_i[j])

            # Create copy of row of P since we need to update it but use older values for update on Q
            P_i = self.P[i, :][:]

            # Update user and item latent feature matrices
            self.P[i, :] += self.alpha * (e * self.Q[j, :] - self.beta * self.P[i,:])
            self.Q[j, :] += self.alpha * (e * P_i - self.beta * self.Q[j,:])

    def get_rating(self, i, j):

        #Get the predicted rating of user i and item j

        prediction = self.b + self.b_u[i] + self.b_i[j] + self.P[i, :].dot(self.Q[j, :].T)
        return prediction

    def full_matrix(self):

        #Compute the full matrix using the resultant biases, P and Q

        return self.b + self.b_u[:,np.newaxis] + self.b_i[np.newaxis:,] + self.P.dot(self.Q.T)




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


            def get_recommended_art(self, user_id, limit=300):

                #art user likes retrieved
                sql = "SELECT * FROM likes WHERE user_id = %s"
                self.cursor.execute(sql, (user_id,))
                likes = self.cursor.fetchall()


                sql = "SELECT * FROM likes"
                self.cursor.execute(sql)
                all_likes = self.cursor.fetchall()


                sql = "SELECT COUNT(DISTINCT id) FROM user"
                self.cursor.execute(sql)
                unique_users = self.cursor.fetchall()
                for u in unique_users:
                    user_count = int(u[0])

                sql = "SELECT COUNT(id) FROM art"
                self.cursor.execute(sql)
                num_art = self.cursor.fetchall()
                for n in num_art:
                    art_count = int(n[0])


                user_liked = []
                liked_art = []
                matrix = [[0 for x in range(art_count)] for y in range(user_count)]

                for a in all_likes:
                    #build matrix
                    user, liked = a
                    matrix[user-1][liked-1] = 1;

                    user_liked.append(user)
                    liked_art.append(liked)


                R = np.array(matrix)

                mf = MF(R, K=20, alpha=0.001, beta=0.01, iterations=100)
                training_process = mf.train()
                predictions = np.array(mf.full_matrix())
                final = []
                for i in range(user_count):
                    for j in range(art_count):
                        if((predictions[i][j] >= 1) and (j+1 not in final) and (i+1 == user_id)):
                            final.append(j+1)



                #print(R)
                #print()
                #print("P x Q:")
                #print(mf.full_matrix())
                string_final = ", ".join(str(x) for x in final)
                #print(string_final)
                #sql = "SELECT * FROM art WHERE id IN " + "(" + string_final + ")"
                sql = "SELECT * FROM (SELECT * FROM art WHERE id IN " + "(" + string_final + ")) AS temp" + " LEFT JOIN(likes, artist) ON (temp.id = likes.art_id AND temp.artist_id = artist.id AND likes.user_id =" + str(user_id) + ")"
                #print(sql)
                self.cursor.execute(sql)
                recommended_art = self.cursor.fetchall()
                #print(recommended_art)

                return [art_tuple_to_art_detail_obj(a, art_join_like_join_artist= True) for a in recommended_art]


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
                sql = "SELECT * FROM art LEFT JOIN artist ON art.artist_id = artist.id WHERE "
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
                    sql = "SELECT * FROM art LEFT JOIN artist ON art.artist_id = artist.id;"
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
