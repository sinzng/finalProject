import io
import os
from pdf2image import convert_from_path
from google.cloud import vision

# Google Cloud Vision API 인증을 위한 환경 변수 설정
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./ocr_key.json"

# Vision API 클라이언트 초기화
client = vision.ImageAnnotatorClient()

def pdf_to_text(pdf_file):
    # PDF 파일을 이미지로 변환
    images = convert_from_path(pdf_file)
    
    # 이미지 데이터를 Vision API에 전송하여 텍스트 인식 요청
    image = images[0]  # 첫 번째 페이지의 이미지 사용
    with io.BytesIO() as output:
        image.save(output, format="JPEG")
        content = output.getvalue()
    
    # Vision API 요청을 위한 Image 객체 생성
    image = vision.Image(content=content)
    
    # 텍스트 인식 요청 및 결과 처리
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        return texts[0].description
    else:
        return "No text found"

if __name__ == "__main__":
    pdf_file_path = "test.pdf"
    extracted_text = pdf_to_text(pdf_file_path)
    print("Extracted text:")
    print(extracted_text)
