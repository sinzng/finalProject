import os
from langchain.chains.summarize import load_summarize_chain
from langchain.docstore.document import Document
from langchain.llms import OpenAI
import tiktoken

def split_text_into_chunks(text, tokenizer, chunk_size=2000, chunk_overlap=100):
    tokens = tokenizer.encode(text)
    chunks = []
    start = 0

    while start < len(tokens):
        end = min(start + chunk_size, len(tokens))
        chunks.append(tokenizer.decode(tokens[start:end]))
        start += chunk_size - chunk_overlap

    return chunks

# 텍스트 분할 및 요약 함수
def summarize_large_text(text, llm, chain, chunk_size=2000, chunk_overlap=100):
    # Tokenizer 설정
    tokenizer = tiktoken.get_encoding("cl100k_base")
    texts = split_text_into_chunks(text, tokenizer, chunk_size, chunk_overlap)
    print(text[:100])

    # 각 청크의 토큰 수 계산 및 출력
    for i, chunk in enumerate(texts):
        tokens = tokenizer.encode(chunk)
        print(f"Chunk {i+1} length: {len(tokens)} tokens")

    docs = [Document(page_content=text) for text in texts]
    
    summaries = []
    for doc in docs:
        summary = chain.run([doc])
        summaries.append(summary)
    
    combined_summary = "\n\n".join(summaries)
    return combined_summary

# 전체 텍스트 읽기
with open("./data/test1.txt") as f:
    text_all = f.read()

# LLM 모델 설정
llm = OpenAI(
    model="gpt-3.5-turbo-instruct",
    temperature=0,
    max_tokens=512
)

# 요약 체인 설정
chain = load_summarize_chain(llm=llm, chain_type="map_reduce")

# 1단계 요약
first_level_summary = summarize_large_text(text_all, llm, chain)

# 2단계 요약
second_level_summary = summarize_large_text(first_level_summary, llm, chain)

print("Final Summary:")
print(second_level_summary)
