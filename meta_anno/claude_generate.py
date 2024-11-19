from refchecker.utils import get_model_batch_response
import os
import json
import random
import re
from tqdm import tqdm

# 设置API Key
os.environ['OPENAI_API_KEY'] = 'sk-proj-nkBZbCF2Y8sTEEVVme17T3BlbkFJkcxNNHrd95qcHIj76iMj'

result = []
change = []
# 模板
prompt_template = """ 
I would like you to help me measure the semantic similarity between two pieces of text. 
I will provide you with 3 texts: reference, text1 and text2. 
You will need to compare text1 and text2 to the reference text and decide which one is more similar to the reference text. Give me a label and a reason for your choice. Label "0" means that text1 is more similar to the reference text, while label "1" means that text2 is more similar to the reference text.

Use the following format for your output:

### Label:
[label]
### Reason:
[Reason]

Now please give your assessment of the semantic similarity between the following texts:

### reference:
[reference]

### text1:
[text1]

### text2:
[text2]

"""


check_template = """
I would like you to help me check the correctness of someone's judgment on the semantic similarity between two pieces of text.
I will provide you with 3 texts: reference, text1 and text2, and the label and reason given by someone else. Label "0" means that text1 is more similar to the reference text, while label "1" means that text2 is more similar to the reference text.
Your task is to decide whether the label and reason are correct or not.
Give me your judgment and a reason for your checking. "True" means that the label are correct, while "False" means that the label are incorrect.

Use the following format for your output:

### Judgment:
True / False

### Reason:

Now please check the correctness of the following judgment:

### reference:
[reference]

### text1:
[text1]

### text2:
[text2]

### Somesone's judgment:
[judgment]

"""

# 加载数据
data_path = 'data/raw.json'
with open(data_path, 'r') as f:
    data = json.load(f)

for i, d in tqdm(enumerate(data)):
    reference = d['reference']  
    text1 = d['text1']
    text2 = d['text2']
    
# 0 -> normal
    if random.random() < 0.5:
        prompt1 = prompt_template.replace('[text1]', text1).replace('[text2]', text2).replace('[reference]', reference)
        prompt2 = check_template.replace('[text1]', text1).replace('[text2]', text2).replace('[reference]', reference)
        change.append(0)
# 1 -> inverse
    else:
        prompt1 = prompt_template.replace('[text1]', text2).replace('[text2]', text1).replace('[reference]', reference)
        prompt2 = check_template.replace('[text1]', text2).replace('[text2]', text1).replace('[reference]', reference)
        change.append(1)    

    # 获取第一个文本对的响应
    responses = get_model_batch_response(
        prompts=[prompt1],
        model='bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0',
        temperature=0,
        max_new_tokens=500
    )
    response_label = responses[0]
    label_match = re.search(r"### Label:\n(\d+)", response_label)

    if label_match:
        label_gpt = label_match.group(1)
        result.append(label_gpt)
    else:
        print(i)
        with open('data/claude_check.json', 'w') as f:
            json.dump(result, f, indent=2)
        with open('data/claude_change.json', 'w') as f:
            json.dump(change, f, indent=2)
        assert 0
    prompt2 = prompt2.replace('[judgment]', response_label) 
    # 获取第二个文本对的响应    
    responses_check = get_model_batch_response(
        prompts=[prompt2],
        model='bedrock/anthropic.claude-3-5-sonnet-20240620-v1:0',
        temperature=0,
        max_new_tokens=500
    )
    response_check = responses_check[0] 
    label_match = re.search(r"### Judgment:\n(\d+)", response_check)
    if label_match:
        check_gpt = label_match.group(1)
        if not check_gpt:
            result[-1]="2"  

# 保存结果到json文件
with open('data/claude_check.json', 'w') as f:
    json.dump(result, f, indent=2)
with open('data/claude_change.json', 'w') as f:
    json.dump(change, f, indent=2)