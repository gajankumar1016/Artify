import sys
sys.path.append('..')
sys.path.append('../database')
from database.dbutils import DbApiInstance
import sys

if __name__ == '__main__':
    print("Argv: ", sys.argv)
    assert(len(sys.argv) == 4)
    with DbApiInstance() as dbapi:
        dbapi.compute_similarities(IMAGES_DIR=sys.argv[1], base_id=sys.argv[2], base_img_fname=sys.argv[3])
