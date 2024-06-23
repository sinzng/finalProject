import os
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

# 모델과 토크나이저 불러오기
model_name = "facebook/bart-large-cnn"  # 원하는 모델 이름
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForSeq2SeqLM.from_pretrained(model_name)

def summarize_text(text, max_length=512, min_length=30):
    # 입력 텍스트를 토큰화
    inputs = tokenizer(text, return_tensors="pt", max_length=1024, truncation=True)

    # 요약 생성
    summary_ids = model.generate(inputs["input_ids"], max_length=max_length, min_length=min_length, length_penalty=2.0, num_beams=4, early_stopping=True)

    # 토큰을 텍스트로 변환
    summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
    return summary

# 전체 텍스트 읽기
with open("./data/test.txt") as f:
    text_all = f.read()

# 텍스트가 너무 길 경우 나누기
def split_text(text, max_chunk_size=1024):
    tokens = tokenizer.tokenize(text)
    chunks = [' '.join(tokens[i:i + max_chunk_size]) for i in range(0, len(tokens), max_chunk_size)]
    return chunks

# 텍스트를 청크로 나누기
chunks = split_text(text_all, max_chunk_size=1024)

# 각 청크 요약
summaries = [summarize_text(chunk) for chunk in chunks]

# 전체 요약 합치기
final_summary = "\n\n".join(summaries)

print("Final Summary:")
print(final_summary)
