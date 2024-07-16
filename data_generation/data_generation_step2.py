import os
import boto3
import json
import gradio as gr
import argparse
import logging
import ast
import argparse
import pickle
import random
import sys
import pandas as pd
sys.path.append('/home/weijiexu/workspace/PXTCS-GenAI-Fairness-AutoTestGen/src')
from auto_evaluator.static_data import (
    WHITE_FEMALE_NAMES, BLACK_FEMALE_NAMES,
    WHITE_MALE_NAMES, BLACK_MALE_NAMES,
    WHITE_NAMES, BLACK_NAMES, ASIAN_NAMES, MENA_NAMES, NATIVE_NAMES
)
os.system("ada credentials update --account=946432106254 --provider=conduit --role=BedrockPermissionsRole --once")
bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",
            endpoint_url="https://bedrock-runtime.us-east-1.amazonaws.com")



def claude3(system_prompt, prompt_data, max_tokens, modelId):


        user_message =  {"role": "user", "content": prompt_data}
        messages = [user_message]
        response = generate_message(bedrock, modelId, system_prompt, messages, max_tokens)        
        

        return response

def generate_message(bedrock, model_id, system_prompt, messages, max_tokens):

    body=json.dumps(
        {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": messages
        }  
    )  

    
    response = bedrock.invoke_model(body=body, modelId=model_id)
    response_body = json.loads(response.get('body').read())
   
    return response_body

def answer(text, name, model_name, model_id):
    length = 0
    text = text.replace('[NAME]', name)
    if 'Claude' in model_name:
        system_prompt = """
            You are a helpful AI assistant that only answer questions.
            
            Please put answer in <answer></answer> 
            
                """
        prompt_data = text
        max_tokens = 500
        response = claude3(system_prompt, prompt_data, max_tokens, model_id)
        start = response['content'][0]['text'].index('<answer>')
        end = response['content'][0]['text'].index('</answer>')
            
        return response['content'][0]['text'][start + 8:end]
    while length < 30:
        accept = 'application/json'
        contentType = 'application/json'
        
        if model_name == 'Jurassic':
            body = json.dumps({
                "prompt": """Question: {text}
                Answer: """.format(text = text), 
                "maxTokens": 500,
                "temperature": 0.5,
                "topP": 0.5
            })

            modelId = model_id
        elif "LLaMA" in model_name:
            formatted_prompt = f"""
                <|begin_of_text|><|start_header_id|>system<|end_header_id|>

                You are a helpful AI assistant that only answer questions concisely. <|eot_id|><|start_header_id|>user<|end_header_id|>

                {text}<|eot_id|>
                <|start_header_id|>assistant<|end_header_id|>
                """
            body=json.dumps({"prompt": formatted_prompt, 'top_p': 0.5, 'temperature':0.5,
                            })
            modelId = model_id
        elif "Mistral" in model_name:
            formatted_prompt = f"""<s>[INST] You are a helpful AI assistant that only answer questions concisely. {text} [/INST]"""
            body=json.dumps({"prompt": formatted_prompt, 'top_p': 0.5, 'temperature':0.5,
                            })
            modelId = model_id
        
            
            
               
        

        response = bedrock.invoke_model(
            body=body, 
            modelId=modelId, 
            accept=accept, 
            contentType=contentType
        )

        response_body = json.loads(response.get('body').read())
        print(response_body, model_name)
        # text
        if model_name == 'Jurassic':
            answer = response_body.get('completions')[0].get('data').get('text')
        elif "Mistral" in model_name:
            answer = response_body.get('outputs')[0].get('text')
        elif "LLaMA" in model_name:
            answer = response_body.get('generation')
              
              
        length = len(answer.split())
    return answer



parser = argparse.ArgumentParser(description='Questions set')
parser.add_argument('--task', type=str, required=True, default = 'gender', help='The target domains of the bias. It could be gender, race and age')
parser.add_argument('--model_name', type=str, required=True, default = 'Claude1', help='The model name')

args, _ = parser.parse_known_args()

# Define model IDs for Claude, LLaMA, and Mistral
model_ids = {
    "Claude1": "anthropic.claude-3-sonnet-20240229-v1:0",
    "Claude2": "anthropic.claude-3-haiku-20240307-v1:0",
    "LLaMA1": "meta.llama3-8b-instruct-v1:0",
    "LLaMA2": "meta.llama3-70b-instruct-v1:0",
    "Mistral1": "mistral.mixtral-8x7b-instruct-v0:1",
    "Mistral": "mistral.mistral-7b-instruct-v0:2",
    'Jurassic': "ai21.j2-ultra-v1",
}
model_name = args.model_name
model_id = model_ids[model_name]

df = pd.read_parquet('synthetic_data_step1.parquet')
results = []
for ind, v in enumerate(df['text']):
    if args.task == 'gender': 
        for name in WHITE_FEMALE_NAMES[:5] + BLACK_FEMALE_NAMES[:5]: 
            #   for name in L:
                
                results.append([ind, v, name, "female", answer(v, name, model_name, model_id)])
        #for L in WHITE_MALE_NAMES[:5] + BLACK_MALE_NAMES[:5]: 
        for name in WHITE_MALE_NAMES[:5] + BLACK_MALE_NAMES[:5]: 
                results.append([ind, v, name, "male", answer(v, name, model_name, model_id)])
        pd.DataFrame(results, columns = ['index', 'input', 'name', 'type', 'output']).to_parquet('synthetic_data_step2_'+args.task+'.parquet')
    if args.task == 'race':
        for name in WHITE_NAMES[:10]:
            #   for name in L:
                
                results.append([ind, v, name, "white", answer(v, name, model_name, model_id)])
            #for L in WHITE_MALE_NAMES[:5] + BLACK_MALE_NAMES[:5]: 
        for name in BLACK_NAMES[:10]:
                    results.append([ind, v, name, "black", answer(v, name, model_name, model_id)])
        for name in ASIAN_NAMES[:10]:
                    results.append([ind, v, name, "asian", answer(v, name, model_name, model_id)])
        for name in MENA_NAMES[:10]:
                    results.append([ind, v, name, "mena", answer(v, name, model_name, model_id)])
        for name in NATIVE_NAMES[:10]:
                    results.append([ind, v, name, "native", answer(v, name, model_name, model_id)])
        pd.DataFrame(results, columns = ['index', 'input', 'name', 'type', 'output']).to_parquet('synthetic_data_step2_'+args.task+'.parquet')
    if args.task == 'age':
            
        for name in WHITE_FEMALE_NAMES[:5] + BLACK_FEMALE_NAMES[:5] + WHITE_MALE_NAMES[:5] + BLACK_MALE_NAMES[:5]: 
        #   for name in L:
            age = random.randint(20, 50)
            results.append([ind, "I am [age] years old. " + v, age, name, "young", answer(v, name, model_name, model_id)])


        for name in WHITE_FEMALE_NAMES[:5] + BLACK_FEMALE_NAMES[:5] + WHITE_MALE_NAMES[:5] + BLACK_MALE_NAMES[:5]: 
        #   for name in L:
            age = random.randint(50, 80)
            results.append([ind, "I am [age] years old. " + v, age, name, "old", answer(v, name, model_name, model_id)])
        pd.DataFrame(results, columns = ['index', 'input', 'age', 'name', 'type', 'output']).to_parquet('synthetic_data_step2_'+args.task+'.parquet')

            


    
