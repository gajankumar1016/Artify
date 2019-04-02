"""Inspired by cs230-stanford build_dataset.py"""

import os
import shutil
import random

from PIL import Image
from tqdm import tqdm

SIZE = 64

def resize_and_save(filename, output_dir, size=SIZE):
    """Resize the image contained in `filename` and save it to the `output_dir`"""
    image = Image.open(filename)
    # Use bilinear interpolation instead of the default "nearest neighbor" method
    image = image.resize((size, size), Image.BILINEAR)
    image.save(os.path.join(output_dir, filename.split('/')[-1]))

def build_dataset(images_per_class=None):
    random.seed(230)
    WIKIART_PATH = "./wikiart"
    subdirs = next(os.walk(WIKIART_PATH))[1]
    print(subdirs)

    TRAIN_DIR = "./train"
    TEST_DIR = "./test"
    DEV_DIR = "./dev"

    shutil.rmtree(TRAIN_DIR, ignore_errors=True)
    shutil.rmtree(TEST_DIR, ignore_errors=True)
    shutil.rmtree(DEV_DIR, ignore_errors=True)

    os.mkdir(TRAIN_DIR)
    os.mkdir(TEST_DIR)
    os.mkdir(DEV_DIR)

    for subdir in subdirs:
        curr_dir = os.path.join(WIKIART_PATH, subdir)
        filenames = os.listdir(curr_dir)
        filenames = [os.path.join(curr_dir, f) for f in filenames if f.endswith('.jpg')]
        print("{}: {}".format(curr_dir, len(filenames))) 

        if images_per_class:
            if len(filenames) < images_per_class:
                print("Skipping {}".format(subdir))

        filenames.sort()
        random.shuffle(filenames)

        max_available = len(filenames)
        if images_per_class:
            max_available = images_per_class

        train_split = int(0.7 * max_available)
        dev_split = int(0.9 * max_available)
        train_filenames = filenames[:train_split]
        dev_filenames = filenames[train_split:dev_split]
        test_filenames = filenames[dev_split:max_available]

        filenames = {'train': train_filenames,
                'dev': dev_filenames,
                'test': test_filenames}

        dirs = {'train': os.path.join(TRAIN_DIR, subdir),
                'dev': os.path.join(DEV_DIR, subdir),
                'test': os.path.join(TEST_DIR, subdir)}

        for split in ['train', 'dev', 'test']:
            os.mkdir(dirs[split])
            for filename in tqdm(filenames[split]):
                resize_and_save(filename, dirs[split], size=SIZE)




if __name__ == '__main__':
    build_dataset(20)
    print("Done building dataset")





