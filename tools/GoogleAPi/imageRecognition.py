import io
import os
# Imports the Google Cloud client library
from google.cloud import vision
from google.cloud.vision import types

class imageclassifier:

    def __init__(self):
        # Instantiates a client
        self.client = vision.ImageAnnotatorClient()

    async def classify(self, filepath):

        # The name of the image file to annotate
        file_name = os.path.abspath(filepath)

        # Loads the image into memory
        with io.open(file_name, 'rb') as image_file:
            content = image_file.read()

        image = types.Image(content=content)

        # Performs label detection on the image file
        response = self.client.label_detection(image=image)
        labels = response.label_annotations

        print('Labels:')
        for label in labels:
            print(label.description)

        return labels
