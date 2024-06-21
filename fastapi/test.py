import io
import os 
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./ocr_key.json"
from google.cloud import vision
client = vision.ImageAnnotatorClient()

file_name = "test.jpg"
with io.open(file_name, "rb") as image_file:
    content = image_file.read()

image = vision.Image(content=content)
response = client.text_detection(image=image)
texts = response.text_annotations
print(texts[0].description)
