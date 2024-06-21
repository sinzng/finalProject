from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader, ServiceContext
from llama_index import PromptHelper

documents = SimpleDirectoryReader('data').load_data()

prompt_helper = PromptHelper(
    max_input_size = 4096, 
    num_output = 256,
    max_chunk_overlap = 20,
)

service_context = ServiceContext.from_defaults(
    prompt_helper = prompt_helper
)

index = GPTVectorStoreIndex.from_documents(
    documents,
    service_context = service_context
)

print('index: ', index)