from google.cloud import storage
import io
import os
from pdf2image import convert_from_path, convert_from_bytes
from google.cloud import vision

# Google Cloud Vision API 인증을 위한 환경 변수 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./ocr_key.json"

# Initialize the Google Cloud Vision client
client = vision.ImageAnnotatorClient()


def pdf_stream_to_text(pdf_stream):
    # PDF 스트림 데이터를 이미지로 변환
    images = convert_from_bytes(pdf_stream)
    
    # 첫 번째 페이지를 이미지로 변환
    if images:
        image = images[0]
        with io.BytesIO() as output:
            image.convert("RGB").save(output, format="JPEG")
            image_data = output.getvalue()
        
        # Vision API 요청을 위한 Image 객체 생성
        vision_image = vision.Image(content=image_data)
        
        # 텍스트 인식 요청 및 결과 처리
        response = client.text_detection(image=vision_image)
        texts = response.text_annotations
        if texts:
            return texts[0].description
        else:
            return "No text found"
    else:
        return "No images found in PDF"

def upload_to_gcs(bucket_name, source_file_name, destination_blob_name):
    """Uploads a file to the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(f"File {source_file_name} uploaded to {destination_blob_name}.")

def download_from_gcs(bucket_name, source_blob_name, destination_file_name):
    """Downloads a file from the bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)
    
    blob.download_to_filename(destination_file_name)
    
    print(f"File {source_blob_name} downloaded to {destination_file_name}.")

def async_detect_document_to_text(gcs_source_uri, gcs_destination_uri, output_text_file):
    """OCR with PDF/TIFF as source files on GCS and save the extracted text to a file"""
    import json
    import re
    from google.cloud import vision
    from google.cloud import storage

    # Supported mime_types are: 'application/pdf' and 'image/tiff'
    mime_type = "application/pdf"

    # How many pages should be grouped into each json output file.
    batch_size = 2

    client = vision.ImageAnnotatorClient()

    feature = vision.Feature(type_=vision.Feature.Type.DOCUMENT_TEXT_DETECTION)

    gcs_source = vision.GcsSource(uri=gcs_source_uri)
    input_config = vision.InputConfig(gcs_source=gcs_source, mime_type=mime_type)

    gcs_destination = vision.GcsDestination(uri=gcs_destination_uri)
    output_config = vision.OutputConfig(
        gcs_destination=gcs_destination, batch_size=batch_size
    )

    async_request = vision.AsyncAnnotateFileRequest(
        features=[feature], input_config=input_config, output_config=output_config
    )

    operation = client.async_batch_annotate_files(requests=[async_request])

    print("Waiting for the operation to finish.")
    operation.result(timeout=420)

    # Once the request has completed and the output has been
    # written to GCS, we can list all the output files.
    storage_client = storage.Client()

    match = re.match(r"gs://([^/]+)/(.+)", gcs_destination_uri)
    bucket_name = match.group(1)
    prefix = match.group(2)

    bucket = storage_client.bucket(bucket_name)

    # List objects with the given prefix, filtering out folders.
    blob_list = [
        blob
        for blob in bucket.list_blobs(prefix=prefix)
        if not blob.name.endswith("/")
    ]
    print("Output files:")
    for blob in blob_list:
        print(blob.name)

    # Initialize an empty string to hold the full text
    full_text = ""

    # Process each output file from GCS.
    for blob in blob_list:
        json_string = blob.download_as_bytes().decode("utf-8")
        response = json.loads(json_string)

        for resp in response["responses"]:
            annotation = resp.get("fullTextAnnotation", {})
            full_text += annotation.get("text", "")

    print(f"Extracted text saved to {output_text_file}")
    
    try:
        # Create a dictionary in the required format
        output_data = {
            "result": 200,
            "data": full_text
        }
    
    # Write the dictionary to the output text file as JSON
        with open(output_text_file, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)
        print(f"Extracted text saved to {output_text_file}")
    except IOError as e:
        print(f"An IOError occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")


bucket_name = "ocr_dataa"
file_name = "test2.pdf"
file_path = f"./data/{file_name}"
destination_blob_name = f"ocr_data/{file_name}"



# 1. Upload the PDF file to GCS
upload_to_gcs(bucket_name, file_path, destination_blob_name)

# 2. Download the PDF file from GCS
downloaded_file_name = "downloaded_test.pdf"
download_from_gcs(bucket_name, destination_blob_name, downloaded_file_name)

# Example usage:
gcs_source_uri = "gs://ocr_dataa/ocr_data/test2.pdf"
gcs_destination_uri = "gs://ocr_dataa/ocr_data/output/"
output_text_file = f"./txt_data/{file_name}.json"
async_detect_document_to_text(gcs_source_uri, gcs_destination_uri, output_text_file)


