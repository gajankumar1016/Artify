"""
REST API to serve art classification keras model

Inspired by https://www.geeksforgeeks.org/exposing-ml-dl-models-as-rest-apis/
"""
from keras.preprocessing.image import img_to_array
from keras.models import load_model
import tensorflow as tf
from PIL import Image
import numpy as np
import flask
from flask_cors import CORS
import io

# Create Flask application and initialize Keras model
app = flask.Flask(__name__)
CORS(app)
model = None

style_to_idx = {'Impressionism': 12, 'Romanticism': 23, 'Baroque': 4, 'Rococo': 22, 'Pop_Art': 19,
                'Early_Renaissance': 8, 'Color_Field_Painting': 5, 'Contemporary_Realism': 6, 'Pointillism': 18,
                'Abstract_Expressionism': 0, 'Minimalism': 14, 'Art_Nouveau_Modern': 3, 'Symbolism': 24,
                'Mannerism_Late_Renaissance': 13, 'Analytical_Cubism': 2, 'Expressionism': 9, 'Fauvism': 10,
                'Synthetic_Cubism': 25, 'Ukiyo_e': 26, 'New_Realism': 16, 'Northern_Renaissance': 17, 'Realism': 21,
                'Cubism': 7, 'Action_painting': 1, 'High_Renaissance': 11, 'Post_Impressionism': 20,
                'Naive_Art_Primitivism': 15}

idx_to_style = {v:k for k, v in style_to_idx.items()}

# Function to Load the model
def load_style_classification_model():
    # global variables, to be used in another function
    global model
    model = load_model("my_model2.h5")
    global graph
    graph = tf.get_default_graph()


# Every ML/DL model has a specific format
# of taking input. Before we can predict on
# the input image, we first need to preprocess it.
def prepare_image(image, target):
    if image.mode != "RGB":
        image = image.convert("RGB")

    # Resize the image to the target dimensions
    image = image.resize(target, Image.BILINEAR)

    # PIL Image to Numpy array
    image = img_to_array(image)

    # Expand the shape of an array,
    # as required by the Model
    image = np.expand_dims(image, axis=0)

    # return the processed image
    return image


# Now, we can predict the results.
@app.route("/predict", methods=["POST"])
def predict():
    data = {}  # dictionary to store result
    data["success"] = False

    # Check if image was properly sent to our endpoint
    if flask.request.method == "POST":
        if flask.request.files.get("image"):
            image = flask.request.files["image"].read()
            image = Image.open(io.BytesIO(image))

            # Resize it to 256x256 pixels
            # (required input dimensions for VGG model)
            image = prepare_image(image, target=(256, 256))

            # Predict ! global preds, results
            with graph.as_default():
                preds = model.predict(image)
                preds = np.squeeze(preds)
                print(preds)
                data["predictions"] = []

            for idx in range(len(preds)):
                prob = preds[idx]
                r = {"label": idx_to_style[idx], "probability": float(prob)}
                data["predictions"].append(r)

            data["success"] = True

    # return JSON response
    return flask.jsonify(data)


if __name__ == "__main__":
    print(("* Loading Keras model and Flask starting server..."
           "please wait until server has fully started"))
    load_style_classification_model()
    app.run()
