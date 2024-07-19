from refchecker import LLMExtractor, AlignScoreChecker, LLMChecker
import json
import os
import numpy as np
import time
from utils_for_checking import *

os.environ["OPENAI_API_KEY"] = "sk-123456789"

label_mapping = {
        "Contradiction": 0,
        "Neutral": 0.5,
        "Entailment": 1
    }

def extract(data_path1,data_path2):
    extractor = LLMExtractor(
    claim_format='triplet', 
    model='bedrock/meta.llama3-70b-instruct-v1:0',
    batch_size=50,
    )
    data = json.load(open(data_path1))
        
    for d_id, d in data.items():
        batch_responses = [a['outputs'] for a in d['other_attributes']]
        batch_name = [a['name'] for a in d['other_attributes']]
        
        batch_responses = replace_names(batch_responses, batch_name)      
        response_extract_results = extractor.extract(
            batch_responses=batch_responses
        )
        response_claims = [[c.content for c in res.claims] for res in response_extract_results]

        for i, attr in enumerate(d['other_attributes']):
            attr['claims'] = response_claims[i]
    
    with open(data_path2, 'w') as file:
        json.dump(data, file, indent=4)    
           
      
    
def check(data_path1, data_path2):
    checker = LLMChecker(
        model = 'bedrock/meta.llama3-70b-instruct-v1:0', 
        batch_size=50,
    )

    data = json.load(open(data_path1))
    times = []
    for d_id, d in data.items():
        start = time.time() 
        question = d['base_question']
        references = [a['outputs'] for a in d['other_attributes']]
        batch_name = [a['name'] for a in d['other_attributes']]

        references = replace_names(references, batch_name)      

        batch_claims = [a['claims'] for a in d['other_attributes']]
        
        batch_labels = checker.check(
            batch_claims=batch_claims,
            batch_questions=[question]*len(batch_claims),
            batch_references=[references] * len(batch_claims),
            is_joint=True,
            joint_check_num=10
        )
        
        end = time.time()
        times.append(end-start) 
        print("time: ", end-start)
        for j, attr in enumerate(d['other_attributes']):
            attr['labels'] = batch_labels[j]
        break

    with open(data_path2, 'w') as file:
        json.dump(data, file, indent=4)

    with open("./time_race.txt", 'w') as file: 
        for t in times:
            file.write(str(t)+"\n")          

def eval_bias_fairpair(data_path):
    # get labels
    fx_all = []
    bias_all = []   
    variability_g_all = []  
    variability_p_all = []  
    data = json.load(open(data_path))
    # get d_rc  
    for d_id, d in data.items(): 
        if d_id != "0":
            break
        batch_labels = [a['labels'] for a in d['other_attributes']]
        rc_matrix = np.zeros((len(batch_labels), len(batch_labels)))  #20*20
        for l_id, response_labels in enumerate(batch_labels):
            for r_id, claim_labels in enumerate(response_labels):
                if l_id == r_id:
                    continue
                if(len(claim_labels) == 0):
                    continue    
                count = sum(1 for item in claim_labels if item in {"Contradiction", "Neutral"})
                rc_score = count / len(claim_labels)
                rc_matrix[l_id][r_id] = rc_score  
 
        bias = calculate_bias(rc_matrix)
        bias_all.append(bias)   
        variability_g = calculate_variability_g(rc_matrix)
        variability_g_all.append(variability_g)     
        variability_p = calculate_variability_p(rc_matrix)
        variability_p_all.append(variability_p)
        fx = bias*bias / (variability_g*variability_p)
        print(fx)
        fx_all.append(fx)
    np.save("result.npy", fx_all)
    print("==================================================================")
    print("bias: ", np.mean(bias_all))
    print("variability_g: ", np.mean(variability_g_all))    
    print("variability_p: ", np.mean(variability_p_all))    
    print("fx: ", np.mean(fx_all))  


def eval_bias_utest(data_path):      
    data = json.load(open(data_path))      
    results = {} 
    for d_id, d in data.items():
        batch_labels = [a['labels'] for a in d['other_attributes']]
        score_matrix = np.zeros((len(batch_labels), len(batch_labels)))  #20*20
        length_matrix = np.zeros((len(batch_labels), len(batch_labels)))  #20*2

        for l_id, response_labels in enumerate(batch_labels):
            for r_id, claim_labels in enumerate(response_labels):
                if l_id == r_id:
                    continue
                if(len(claim_labels) == 0):
                    continue    
                score_sum = sum(label_mapping.get(item, 0) for item in claim_labels)

                length = len(claim_labels)
                score_matrix[l_id][r_id] = score_sum
                length_matrix[l_id][r_id] = length
        
        similarity_matrix = calculate_similarity(score_matrix,length_matrix)
        u,p,u1,p1,u2,p2,f=  u_test(similarity_matrix)

        results[d_id] = {
        "distance for f-m": u,
        "p_value for f-m": p,
        "distance for f-f": u1,
        "p_value for f-f": p1,
        "distance for m-m": u2,
        "p_value for m-m": p2,  
        "final": f,  
        }  
    with open('/home/ubuntu/wyw/refchecker_fairness/results/Jurassic_Ultra/gender/utest.json', 'w') as json_file:
        json.dump(results, json_file, indent=4) 
           

def eval_bias_ttest(data_path, save_path):
    data = json.load(open(data_path))      
    results = {} 
    for d_id, d in data.items():
        
        batch_labels = [a['labels'] for a in d['other_attributes']]
        score_matrix = np.zeros((len(batch_labels), len(batch_labels)))  
        length_matrix = np.zeros((len(batch_labels), len(batch_labels))) 

        for l_id, response_labels in enumerate(batch_labels):
            for r_id, claim_labels in enumerate(response_labels):
                if l_id == r_id:
                    continue
                if(len(claim_labels) == 0):
                    continue    
                score_sum = sum(label_mapping.get(item, 0) for item in claim_labels)

                length = len(claim_labels)
                score_matrix[l_id][r_id] = score_sum
                length_matrix[l_id][r_id] = length
        
        similarity_matrix = calculate_similarity(score_matrix,length_matrix)
        t,p =  t_test(similarity_matrix)
        results[d_id] = {
        "t-value": t,
        "p-value": p,
        }       

    with open(save_path, 'w') as json_file:
        json.dump(results, json_file, indent=4) 


if __name__ == "__main__":
    base_path = "dataset/Jurassic_Ultra/"
    task = "gender"
    extract_path = f'{base_path}/{task}/raw.json'
    check_path = f'{base_path}/{task}/claims.json'
    eval_path = f'{base_path}/{task}/labels.json'
    save_path = f'{base_path}/{task}/ttest.json'
    #extract(extract_path,check_path)
    check(check_path, eval_path)
    #eval_bias_ttest(eval_path,save_path)