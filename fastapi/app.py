from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi import Request
from fastapi.responses import JSONResponse
from test2 import pdf_to_text
from google.cloud import vision
from pdf2image import convert_from_bytes
from PIL import Image
import io
import json
import os
import uuid

app = FastAPI()

# 전역 변수로 파일 경로 저장
global uploaded_file_path

@app.get("/")
def read_root():
    return {"Hello" : "World"}
# 디렉토리가 없으면 생성하는 함수
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
# ---- pdf로 변환 ----
# @app.post("/upload")
# async def upload_stream(request: Request):
#     try:
#         # 파일 저장 경로 설정
#         upload_dir = "./uploaded_files"
#         ensure_dir(upload_dir)
#         pdf_file_location = os.path.join(upload_dir, "uploaded_file.pdf")
        
#         # 스트림 데이터 읽기
#         body = await request.body()
#         print(f"Received body: {body[:100]}...")  # 앞의 100바이트만 출력하여 데이터가 수신되었는지 확인
        
#         # 바이트 데이터를 PDF로 변환
#         byte_pdf = bytes(body)
        
#         # PDF 파일로 저장
#         with open(pdf_file_location, 'wb') as outfile:
#             outfile.write(byte_pdf)
        
#         # 저장된 파일 경로를 전역 변수에 저장
#         uploaded_file_path = pdf_file_location
#         print(f"PDF created at: {uploaded_file_path}")
#         res = await get_ocrtext(uploaded_file_path)
        
#         return res
#     except Exception as e:
#         print(f"Error in /upload: {str(e)}")
#         raise HTTPException(status_code=500, detail=str(e))
def pdf_stream_to_jpg(pdf_stream):
    try:
        # PDF 스트림 데이터를 이미지로 변환
        images = convert_from_bytes(pdf_stream)
        
        if not images:
            raise HTTPException(status_code=400, detail="No images found in PDF")

        image_datas = []
        for image in images:
            with io.BytesIO() as output:
                image.convert("RGB").save(output, format="JPEG")
                image_data = output.getvalue()
                image_datas.append(image_data)
                
        return image_datas
    except Exception as e:
        print(f"Error converting PDF to image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


def image_to_text(image_data):
    try:
        client = vision.ImageAnnotatorClient()
        full_texts = []

        for img_data in image_data:
            # Vision API 요청을 위한 Image 객체 생성
            vision_image = vision.Image(content=img_data)
            
            # 텍스트 인식 요청 및 결과 처리
            response = client.text_detection(image=vision_image)
            texts = response.text_annotations
            if texts:
                full_text = texts[0].description
            else:
                full_text = "No text found"
            
            full_texts.append(full_text)

        # Create a dictionary in the required format
        output_data = {
            "result": 200,
            "texts": full_texts
        }
        return output_data
    except Exception as e:
        print(f"Error processing image for OCR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/upload")
async def upload_stream(request: Request):
    try:
        # 스트림 데이터 읽기
        body = await request.body()
        print(f"Received body: {body[:100]}...")  # 앞의 100바이트만 출력하여 데이터가 수신되었는지 확인
        
        # 스트림 데이터를 JPEG 이미지로 변환
        jpg_image_data = pdf_stream_to_jpg(body)
        
        # 이미지 데이터를 텍스트로 변환
        extracted_data = image_to_text(jpg_image_data)
        # 고유한 파일 이름 생성
        unique_filename = str(uuid.uuid4())
        
        # 추출된 텍스트를 JSON 파일로 저장
        upload_dir = "./uploaded_files"
        ensure_dir(upload_dir)
        
        json_file_location = os.path.join(upload_dir, f"{unique_filename}.json")
        with open(json_file_location, 'w', encoding='utf-8') as json_file:
            json.dump(extracted_data, json_file, ensure_ascii=False, indent=4)
        
        print(f"Extracted text saved at: {json_file_location}")
        
        # text 키의 값만 추출하여 반환
        text_value = extracted_data.get("text", "")

        return JSONResponse(content={"text": text_value})
    except Exception as e:
        print(f"Error in /upload: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    
@app.get("/ocrtext")
async def get_ocrtext(uploaded_file_path):
    try:
        print(f"Uploaded file path: {uploaded_file_path}")


        if not uploaded_file_path:
            raise HTTPException(status_code=400, detail="No file uploaded")

        # Google Cloud Vision API 인증을 위한 환경 변수 설정
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./ocr_key.json"
        
        # PDF 파일에서 텍스트 추출
        extracted_text = pdf_to_text(uploaded_file_path)

        # JSON 파일로 저장
        json_file_location = os.path.splitext(uploaded_file_path)[0] + ".json"
        with open(json_file_location, 'w', encoding='utf-8') as json_file:
            json.dump({"extracted_text": extracted_text}, json_file, ensure_ascii=False, indent=4)
        
        return JSONResponse(content={"result": 200, "file_location": json_file_location})
    except Exception as e:
        print(f"Error in /ocrtext: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)