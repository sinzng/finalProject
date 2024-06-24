import time
import torch
import json
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from multiprocessing import Pool, cpu_count

# 1. 텍스트 분할 설정
with open("./uploaded_files/test.json", 'r', encoding='utf-8') as f:
    data = json.load(f)

text_all = data.get("texts", "")

text_splitter = CharacterTextSplitter(
    separator="\\n\\n",
    chunk_size=2000,
    chunk_overlap=100
)
texts = text_splitter.split_text(text_all)
print(f"Total chunks: {len(texts)}")

docs = [Document(page_content=text) for text in texts]

# 2. Hugging Face 요약 모델 설정
model_name = "facebook/bart-large-cnn"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)

def summarize_text(text, max_length=512, min_length=30):
    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True).to(device)
    summary_ids = model.generate(inputs["input_ids"], max_length=max_length, min_length=min_length, length_penalty=2.0, num_beams=4, early_stopping=True)
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# 3. 텍스트 요약 함수 병렬 처리
def parallel_summarize(doc):
    return summarize_text(doc.page_content)

if __name__ == "__main__":
    start_time = time.time()

    # 병렬 처리를 위한 Pool 설정
    with Pool(processes=cpu_count()) as pool:
        chunk_summaries = pool.map(parallel_summarize, docs)

    chunk_summary_docs = [Document(page_content=summary) for summary in chunk_summaries]

    end_time = time.time()
    print(f"Chunk summaries completed in {end_time - start_time:.2f} seconds")

    # 최종 요약 (필요 시)
    final_summary = "\n\n".join(chunk_summaries)
    print("Final summary:")
    print(final_summary)

    total_time = time.time() - start_time
    print(f"Total processing time: {total_time:.2f} seconds")
