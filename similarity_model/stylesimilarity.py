import numpy as np
import scipy.ndimage
import skimage.transform

def _load_raw_image(path):
    img = np.array(scipy.ndimage.imread(path, flatten=False))
    # np_image = scipy.misc.imresize(img, size=(512, 512)) / 255
    np_image = skimage.transform.resize(img, output_shape=(224, 224))
    return np_image

def _l2_image_error(base_img, target_img):
    return np.linalg.norm(base_img - target_img) / np.linalg.norm(base_img)

def _cos_sim(img1, img2):
    dot_product = np.sum(np.multiply(img1, img2))
    norm_1 = np.linalg.norm(img1)
    norm_2 = np.linalg.norm(img2)
    return dot_product / (norm_1 * norm_2)

def cos_sim(img1, img2):
    img1 = _load_raw_image(img1)
    img2 = _load_raw_image(img2)
    # return _l2_image_error(base_img=img1, target_img=img2)
    return _cos_sim(img1, img2)
