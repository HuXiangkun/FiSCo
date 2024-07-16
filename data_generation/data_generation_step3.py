import pandas as pd
import json
import argparse

parser = argparse.ArgumentParser(description='Questions set')
parser.add_argument('--name', type=str, required=True, default = 'synthetic_data_step2_age', help='The name of the file you want to convert to json')

args, _ = parser.parse_known_args()
name = args.name

df = pd.read_parquet(name + '.parquet')

if 'age' in name:
    d = {}
    for i in df.values:
        if i[0] not in d:
            d[i[0]] = {}
            d[i[0]]["base_question"] = i[1]
            d[i[0]]["other_attributes"] = [{'name': i[3], 'age': i[2], "outputs": i[-1]}]
            if i[2] <= 50:
                d[i[0]]["other_attributes"][-1]['type'] = 'young'
            else:
                d[i[0]]["other_attributes"][-1]['type'] = 'old'

        else:
            d[i[0]]["other_attributes"].append({'name': i[3], 'age': i[2], "outputs": i[-1]})
            if i[2] <= 50:
                d[i[0]]["other_attributes"][-1]['type'] = 'young'
            else:
                d[i[0]]["other_attributes"][-1]['type'] = 'old'

    
else:
    d = {}
    for i in df.values:
        if i[0] not in d:
            d[i[0]] = {}
            d[i[0]]["base_question"] = i[1]
            d[i[0]]["other_attributes"] = [{"gender": i[3], "name": i[2], "outputs": i[-1]}]

        else:
            d[i[0]]["other_attributes"].append([{"gender": i[3], "name": i[2], "outputs": i[-1]}])

with open(name + '.json', 'w') as f:
    json.dump(d, f, indent=2)