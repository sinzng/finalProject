from fastapi import FastAPI, UploadFile, File, HTTPException, Form, Body
from fastapi import Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from test2 import pdf_to_text
from google.cloud import vision
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
from PIL import Image
import io, json, os, uuid, requests
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from search import search_query
from fastapi.templating import Jinja2Templates
from authlib.integrations.starlette_client import OAuth

app = FastAPI()
load_dotenv()

oauth = OAuth()
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    authorize_params=None,
    access_token_url='https://accounts.google.com/o/oauth2/token',
    access_token_params=None,
    refresh_token_url=None,
    redirect_uri='http://<your_ec2_domain>/auth/callback',
    client_kwargs={'scope': 'openid profile email'},
)

@app.get('/auth')
async def auth(request: Request):
    redirect_uri = 'http://<your_ec2_domain>/auth/callback'
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get('/auth/callback')
async def auth_callback(request: Request):
    token = await oauth.google.authorize_access_token(request)
    user = await oauth.google.parse_id_token(request, token)
    # 여기에 세션 설정 또는 토큰 반환 로직을 추가할 수 있습니다.
    return {"user": user}


YJ_IP = os.getenv("YJ_IP")
CY_IP = os.getenv("CY_IP")
# 전역 변수로 파일 경로 저장
global uploaded_file_path



@app.post("/search", response_class=HTMLResponse)
async def search(query: str = Form(...)):
    return await search_query(query)


# 디렉토리가 없으면 생성하는 함수
def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

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
        combined_text = ""

        for img_data in image_data:
            # Vision API 요청을 위한 Image 객체 생성
            vision_image = vision.Image(content=img_data)
            
            # 텍스트 인식 요청 및 결과 처리
            response = client.document_text_detection(image=vision_image)
            full_text = ""

            if response.full_text_annotation:
                for page in response.full_text_annotation.pages:
                    for block in page.blocks:
                        for paragraph in block.paragraphs:
                            paragraph_text = ''
                            for word in paragraph.words:
                                word_text = ''.join([symbol.text for symbol in word.symbols])
                                paragraph_text += word_text + ' '  # 단어 간 공백 추가
                            full_text += paragraph_text.strip() + "\\n\\n"  # 단락 구분을 위해 두 개의 개행 문자를 추가하고 앞뒤 공백 제거
            else:
                full_text = "No text found"
            
            # 텍스트를 바로 결합
            combined_text += full_text

        print(f"Combined text length: {len(combined_text)}")
        # 텍스트 분할 및 필터링
        document = Document(page_content=combined_text)
        text_splitter = CharacterTextSplitter(separator="\\n\\n", chunk_size=2000, chunk_overlap=100)
        split_docs = text_splitter.split_documents([document])
        
        filtered_docs = []
        for doc in split_docs:
            if "References" in doc.page_content:
                doc.page_content = doc.page_content.split("References")[0]
                filtered_docs.append(doc.page_content)
                break
            filtered_docs.append(doc.page_content)
        
        filtered_text = "\\n\\n".join(filtered_docs)
        
        # Create a dictionary in the required format
        output_data = {
            "result": 200,
            "texts": filtered_text
        }
        return output_data
    except Exception as e:
        print(f"Error processing image for OCR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/ocr/ocrPdf")
async def upload_stream(request: Request):
    try:
        # 요청 헤더에서 title 가져오기
        title = request.headers.get("titles")
        if not title:
            raise HTTPException(status_code=400, detail="Title header is missing.")

        # 팀원의 getFullText API 호출하여 full_text 존재 여부 확인
        response = requests.get(f"{YJ_IP}:3500/getFullText", params={"title": title})
        
        print(response.json())
        
        if response.json().get("resultCode") == 200 and response.json().get("data"):
            # title이 이미 존재하고, full_text 데이터를 가져옴
            print(f"Full text already exists for title: {title}")
            text_value = response.json().get("data")
            return JSONResponse(content={"resultCode": 200,  "data": {"titles": title, "texts": text_value}})
        else:
            # PDF 스트림 데이터 읽기
            pdf_stream_data = await request.body()
        
            print(f"Received title: {title}")
        
            # PDF 스트림 데이터를 JPEG 이미지로 변환
            jpg_image_data = pdf_stream_to_jpg(pdf_stream_data)
        
            # 이미지 데이터를 텍스트로 변환
            extracted_data = image_to_text(jpg_image_data)
        

            # # title을 포함한 새로운 데이터 생성
            # output_data = {
            #     "title": title,
            #     "result": extracted_data.get("result"),
            #     "texts": extracted_data.get("texts") 
            # }
            
            # # 고유한 파일 이름 생성
            # unique_filename = str(uuid.uuid4())
        
            # # 추출된 텍스트와 title을 JSON 파일로 저장
            # upload_dir = "./uploaded_files"
            # ensure_dir(upload_dir)
        
            # json_file_location = os.path.join(upload_dir, f"{unique_filename}.json")
            # with open(json_file_location, 'w', encoding='utf-8') as json_file:
            #     json.dump(output_data, json_file, ensure_ascii=False, indent=4)
        
            # print(f"Extracted text and title saved at: {json_file_location}")
            print(f"Extracted text and title saved")

            #존재하지 않으면 store_full_text API 호출하여 저장
            payload = {
                "title": title,
                "result": extracted_data.get("result"),
                "text": extracted_data.get("texts")
            }
            headers = {"Content-Type": "application/json"}
            response = requests.post(f"{YJ_IP}:3500/store_full_text", data=json.dumps(payload), headers=headers)
            
            if response.json().get("resultCode") == 200: 
                # result = response.json()
                # text_value = result.get("text", "")
                print(f"Data stored successfully")
            else:
                print(f"Failed to store data: {response.status_code} - {response.text}")
                text_value = "Failed to store data"
                
            return JSONResponse(content={"resultCode": 200, "data": {"titles": payload.get("title"), "texts": payload.get("text")}}) 

    except Exception as e:
        print(f"Error in /upload: {str(e)}")
    
@app.post("/keyword")
async def getKeyword(data: dict = Body(...)):
    try:
        title = data.get("title")
        if not title:
            raise HTTPException(status_code=400, detail="Title is required.")

        # 팀원의 getFullText API 호출하여 full_text 존재 여부 확인
        response = requests.get(f"{YJ_IP}:3500/getFullText", params={"title": title})
        
        response_data = response.json()
        
        if response_data.get("resultCode") == 200 and response_data.get("data"):
            # title이 이미 존재하고, full_text 데이터를 가져옴
            print(f"Full text already exists for title: {title}")
            text_value = response_data.get("data")
            # Bert_Keyword API 호출하여 키워드 추출
            bert_keyword_response = requests.post(
                f"{CY_IP}:8000/Bert_Keyword",  # Bert_Keyword API의 실제 URL로 변경
                json={"text": text_value}
            )
            bert_keyword_data = bert_keyword_response.json()
            
            return JSONResponse(content={"titles": title, "keywords": bert_keyword_data})
        else:
            print("저장된 텍스트 파일이 없습니다.")
            return JSONResponse(content={"detail": "저장된 텍스트 파일이 없습니다."}, status_code=404)
        
    except Exception as e:
        print(f"Error in /keyword: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/getSum1")
async def getsum(title: str):
    try:
        response = requests.get(f"{YJ_IP}:3500/getSummary1", params={"title": title})
        response.raise_for_status()  
        return response.json()
    except requests.RequestException as e:
        print(f"Error in /getSum: {str(e)}")
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
    
@app.get("/getTime")
async def get_time(title:str):
    try :
        time1_response1 = requests.get(f"{YJ_IP}:3500/getTime1?title={title}")
        time1 = time1_response1.json()
        time2_response1 = requests.get(f"{YJ_IP}:3500/getTime2?title={title}")
        time2 = time2_response1.json()
        time3_response1 = requests.get(f"{YJ_IP}:3500/getTime3?title={title}")
        time3 = time3_response1.json()
    except Exception as e:
        print(f"Error in /getTime: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    return time1, time2, time3

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3000)