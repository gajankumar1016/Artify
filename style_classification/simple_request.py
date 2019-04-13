"""
Python script to get style prediction from our api

Inspired by https://www.geeksforgeeks.org/exposing-ml-dl-models-as-rest-apis/
"""

import requests
import sys

URL = "http://localhost:5000/predict"

# provide image name as command line argument
IMAGE_PATH = sys.argv[1]

image = open(IMAGE_PATH, "rb").read()
payload = {"image": image}

# make request to the API
request = requests.post(URL, files = payload).json()

if request["success"]:
	# Print formatted Result
	print("% s % 15s % s"%("Rank", "Label", "Probability"))
	for (i, result) in enumerate(request["predictions"]):
		print("% d. % 17s %.4f"%(i + 1, result["label"],
			result["probability"]))

