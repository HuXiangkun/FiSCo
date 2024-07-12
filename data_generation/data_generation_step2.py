import os
import boto3
import json
import argparse
import logging
import random
import pandas as pd
from static_data import (
    WHITE_FEMALE_NAMES, BLACK_FEMALE_NAMES,
    WHITE_MALE_NAMES, BLACK_MALE_NAMES,
    WHITE_NAMES, BLACK_NAMES, ASIAN_NAMES, MENA_NAMES, NATIVE_NAMES
)
os.system("ada credentials update --account=946432106254 --provider=conduit --role=BedrockPermissionsRole --once")
bedrock = boto3.client(
            service_name="bedrock-runtime",
            region_name="us-east-1",
            endpoint_url="https://bedrock-runtime.us-east-1.amazonaws.com")



logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


def answer(text, name):
    length = 0
    while length < 30:
        text = text.replace('[NAME]', name)
        body = json.dumps({
            "prompt": """Question: {text}
            Answer: """.format(text = text), 
            "maxTokens": 500,
            "temperature": 0.5,
            "topP": 0.5
        })

        modelId = 'ai21.j2-ultra-v1'
        accept = 'application/json'
        contentType = 'application/json'

        response = bedrock.invoke_model(
            body=body, 
            modelId=modelId, 
            accept=accept, 
            contentType=contentType
        )

        response_body = json.loads(response.get('body').read())

        # text
        answer = response_body.get('completions')[0].get('data').get('text')
        length = len(answer.split())
    return answer

parser = argparse.ArgumentParser(description='Questions set')
parser.add_argument('--task', type=str, required=True, default = 'gender', help='The target domains of the bias. It could be gender, race and age')

args, _ = parser.parse_known_args()

df = pd.read_parquet('synthetic_data_step1.parquet')
results = []
for ind, v in enumerate(df['text']):
    if args.task == 'gender': 
        for name in WHITE_FEMALE_NAMES[:5] + BLACK_FEMALE_NAMES[:5]: 
            #   for name in L:
                
                results.append([ind, v, name, "female", answer(v, name)])
        #for L in WHITE_MALE_NAMES[:5] + BLACK_MALE_NAMES[:5]: 
        for name in WHITE_MALE_NAMES[:5] + BLACK_MALE_NAMES[:5]: 
                results.append([ind, v, name, "male", answer(v, name)])
        pd.DataFrame(results, columns = ['index', 'input', 'name', 'type', 'output']).to_parquet('synthetic_data_step2_gender.parquet')
    if args.task == 'race':
        for name in WHITE_NAMES[:10]:
            #   for name in L:
                
                results.append([ind, v, name, "white", answer(v, name)])
            #for L in WHITE_MALE_NAMES[:5] + BLACK_MALE_NAMES[:5]: 
        for name in BLACK_NAMES[:10]:
                    results.append([ind, v, name, "black", answer(v, name)])
        for name in ASIAN_NAMES[:10]:
                    results.append([ind, v, name, "asian", answer(v, name)])
        for name in MENA_NAMES[:10]:
                    results.append([ind, v, name, "mena", answer(v, name)])
        for name in NATIVE_NAMES[:10]:
                    results.append([ind, v, name, "native", answer(v, name)])
        pd.DataFrame(results, columns = ['index', 'input', 'name', 'type', 'output']).to_parquet('synthetic_data_step2_race.parquet')
    if args.task == 'age':
            
        for name in WHITE_FEMALE_NAMES[:5] + BLACK_FEMALE_NAMES[:5] + WHITE_MALE_NAMES[:5] + BLACK_MALE_NAMES[:5]: 
        #   for name in L:
            age = random.randint(20, 50)
            results.append([ind, "I am " + str(age) + " years old. " + v, age, "young", answer(v, name)])


        for name in WHITE_FEMALE_NAMES[:5] + BLACK_FEMALE_NAMES[:5] + WHITE_MALE_NAMES[:5] + BLACK_MALE_NAMES[:5]: 
        #   for name in L:
            age = random.randint(50, 80)
            results.append([ind, "I am " + str(age) + " years old. " + v, age, "old", answer(v, name)])
        pd.DataFrame(results, columns = ['index', 'input', 'name', 'type', 'output']).to_parquet('synthetic_data_step2_age.parquet')

            


    




