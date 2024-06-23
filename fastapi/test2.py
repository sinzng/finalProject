import io
import os
from pdf2image import convert_from_path
from google.cloud import vision

# Google Cloud Vision API 인증을 위한 환경 변수 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./ocr_key.json"

# Vision API 클라이언트 초기화
client = vision.ImageAnnotatorClient()
def pdf_to_text(pdf_file):
    # Google Cloud Vision API 클라이언트 생성
    client = vision.ImageAnnotatorClient()

    # PDF 파일을 이미지로 변환
    images = convert_from_path(pdf_file)
    
    extracted_text = ""

    for page_number, image in enumerate(images):
        with io.BytesIO() as output:
            image.save(output, format="JPEG")
            content = output.getvalue()
        
        # Vision API 요청을 위한 Image 객체 생성
        image = vision.Image(content=content)
        
        # 텍스트 인식 요청 및 결과 처리
        response = client.text_detection(image=image)
        texts = response.text_annotations

        if texts:
            extracted_text += f"Page {page_number + 1}:\n"
            extracted_text += texts[0].description
            extracted_text += "\n\n"
        else:
            extracted_text += f"Page {page_number + 1}:\nNo text found\n\n"

        if response.error.message:
            raise Exception(f"Error during text detection: {response.error.message}")

    return extracted_text
if __name__ == "__main__":
    pdf_file_path = "./data/test2.pdf"
    extracted_text = pdf_to_text(pdf_file_path)
    print("Extracted text:")
    print(extracted_text)
