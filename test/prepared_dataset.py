import json
import os

def convert_to_new_format(data):
    new_data = []
    
    for utterance in data["utterances"]:
        if utterance["role"] == "speaker":
            prompt_message = {
                "role": "user",
                "content": utterance["text"]
            }
            new_data.append({"messages": [prompt_message]})
        elif utterance["role"] == "listener":
            if new_data:  # 이전에 speaker가 있어야 completion을 추가할 수 있음
                completion_message = {
                    "role": "assistant",
                    "content": utterance["text"]
                }
                new_data[-1]["messages"].append(completion_message)
    
    return new_data

base_dir = './data'
json_data_list = []

# Step 1: Traverse through each subdirectory in base_dir
for dirpath, dirnames, filenames in os.walk(base_dir):
    for filename in filenames:
        if filename.endswith('.json'):
            file_path = os.path.join(dirpath, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    json_data = json.load(f)
                    new_data = convert_to_new_format(json_data)
                    json_data_list.append(new_data)
                except json.JSONDecodeError as e:
                    print(f"Error decoding JSON in file {file_path}: {e}")

# Step 2: Write converted data to a JSON Lines file
output_file = 'dataset.jsonl'
with open(output_file, 'w', encoding='utf-8') as f:
    for data in json_data_list:
        try:
            f.write(json.dumps(data, ensure_ascii=False) + '\n')
        except Exception as e:
            print(f"Error writing data to {output_file}: {e}")

print(f"Conversion and writing to '{output_file}' complete.")
