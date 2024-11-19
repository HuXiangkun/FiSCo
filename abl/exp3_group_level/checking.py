from refchecker import LLMExtractor, LLMChecker
import json
import numpy as np
def check(data_path1):
    checker = LLMChecker(
        model = 'bedrock/meta.llama3-1-70b-instruct-v1:0', 
        batch_size=50,
    )
    
    data = json.load(open(data_path1))
    for index, item in enumerate(data):
        q = item['questions']
        c = item['claims']
        c_f1 = c[0]
        c_f2 = c[1]
        c_m = c[2]
        ref_f1 = item['female1']
        ref_f2 = item['female2']
        ref_m = item['male1']
        

        labels_f1_to_f2=checker.check(
            batch_claims= c_f1,   # 10 claim-list for female1 
            batch_questions= [q] * len(c_f1),  
            batch_references=[ref_f2] * len(c_f1),   # 10 response for female2
            is_joint=True,
            joint_check_num=10
            )
        labels_f2_to_f1=checker.check(
            batch_claims= c_f2,   # female2
            batch_questions=[q]*10,  
            batch_references=[ref_f1] * 10,   # female1
            is_joint=True,
            joint_check_num=10
            )   
        
        labels_f1_to_m=checker.check(
            batch_claims= c_f1,   # female1
            batch_questions=[q]*10,  
            batch_references=[ref_m] * 10,   # male1
            is_joint=True,
            joint_check_num=10
            )
        labels_m_to_f1=checker.check(   
            batch_claims= c_m,   # male1
            batch_questions=[q]*10,  
            batch_references=[ref_f1] * 10,   # female1
            is_joint=True,
            joint_check_num=10
            )   
        labels_f2_to_m=checker.check(
            batch_claims= c_f2,   # female2
            batch_questions=[q]*10,  
            batch_references=[ref_m] * 10,   # male1
            is_joint=True,
            joint_check_num=10
            )
        labels_m_to_f2=checker.check(
            batch_claims= c_m,   # male1
            batch_questions=[q]*10,  
            batch_references=[ref_f2] * 10,   # female2
            is_joint=True,
            joint_check_num=10
            )
        item['labels_f1_to_f2'] = labels_f1_to_f2
        item['labels_f2_to_f1'] = labels_f2_to_f1
        item['labels_f1_to_m'] = labels_f1_to_m
        item['labels_m_to_f1'] = labels_m_to_f1
        item['labels_f2_to_m'] = labels_f2_to_m
        item['labels_m_to_f2'] = labels_m_to_f2

    with open('data/age/labels.json', "w") as f:
        json.dump(data, f, indent=2)



check("data/age/claims.json")

