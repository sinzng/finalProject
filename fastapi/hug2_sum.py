import time
import torch
from concurrent.futures import ProcessPoolExecutor, as_completed
from langchain.text_splitter import CharacterTextSplitter
from langchain.docstore.document import Document
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from langchain.chains.summarize import load_summarize_chain
from langchain.llms.base import LLM

# 1. 텍스트 분할 설정
with open("./data/test.txt") as f:
    text_all = f.read()

# 텍스트 분할 설정
text_splitter = CharacterTextSplitter(
    separator="\\n\\n",  # 문단 단위로 분할
    chunk_size=1000,  # 청크 크기를 1000으로 설정
    chunk_overlap=100  # 중첩을 100으로 설정
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

# 3. LangChain의 MapReduce 체인에 통합
class HuggingFaceLLM(LLM):
    def _call(self, prompt: str, stop=None):
        return summarize_text(prompt)
    
    def _identifying_params(self):
        return {"model_name": model_name}
    
    @property
    def _llm_type(self) -> str:
        return "huggingface"

    def dict(self):
        return dict(self._identifying_params())

llm = HuggingFaceLLM()
chain = load_summarize_chain(
    llm=llm,
    chain_type="map_reduce",
)

# 병렬 처리로 각 청크 요약
def process_chunk(doc):
    return summarize_text(doc.page_content)

if __name__ == "__main__":
    start_time = time.time()

    chunk_summaries = []
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(process_chunk, doc): i for i, doc in enumerate(docs)}
        for future in as_completed(futures):
            i = futures[future]
            try:
                chunk_summary = future.result()
                print(f"Chunk {i+1} summary completed")
                chunk_summaries.append(Document(page_content=chunk_summary))
            except Exception as exc:
                print(f"Chunk {i+1} generated an exception: {exc}")

    end_time = time.time()
    print(f"Chunk summaries completed in {end_time - start_time:.2f} seconds")
    print(chunk_summaries[:100])

    # 문서 요약 실행
    summary_start_time = time.time()
    summary = chain.run(chunk_summaries)  # 요약된 청크들을 다시 사용하여 최종 요약 생성
    summary_end_time = time.time()
    print(f"Final summary completed in {summary_end_time - summary_start_time:.2f} seconds")
    print("Final summary:")
    print(summary)

    total_time = summary_end_time - start_time
    print(f"Total processing time: {total_time:.2f} seconds")
