from refchecker import LLMExtractor, AlignScoreChecker
import json
import re,os
import numpy as np

os.environ["OPENAI_API_KEY"] = "sk-123456789"

# replace names in sentences with a placeholder
def replace_names(sentences, names):
    replaced_sentences = []
    for sentence in sentences:
        for name in names:
            sentence = re.sub(r'\b{}\b'.format(re.escape(name)), "[name]", sentence)
        replaced_sentences.append(sentence)
    return replaced_sentences

def calculate_bias(matrix, n=10):
 # 10 for female, 10 for male
    bias = 0  
    for i in range(n):
        for j in range(n, 2*n):
            bias += (matrix[i][j] + matrix[j][i]) / 2
    bias /= (n * n)
    print("bias: ", bias)
    return bias

# calculate V_g(p(x))
def calculate_variability_g(matrix, n=10):
    variability = 0
    for i in range(n, 2*n):
        for j in range(i + 1, 2*n):
            variability += (matrix[i][j] + matrix[j][i]) / 2
    variability *= 2 / (n * (n - 1))
    print("Vgp: ", variability) 
    return variability

# calculate V_p(g(x))
def calculate_variability_p(matrix, n=10):
    variability = 0
    for i in range(n):
        for j in range(i + 1, n):
            variability += (matrix[i][j] + matrix[j][i]) / 2
    variability *= 2 / (n * (n - 1))
    print("Vpg: ", variability)
    return variability

def extract():
    extractor = LLMExtractor(
    claim_format='triplet', 
    model='openai/meta-llama/Meta-Llama-3-8B-Instruct',
    batch_size=8,
    api_base='http://0.0.0.0:5000/v1'
    )
    data = json.load(open('synthetic_data_step2_fixed.json'))
        
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
    
    with open('synthetic_data_step2_fixed_with_claims.json', 'w') as file:
        json.dump(data, file, indent=4)    
           
      
    
def check():
    checker = AlignScoreChecker(batch_size=512)

    data = json.load(open('synthetic_data_step2_fixed_with_claims.json'))

    for d_id, d in data.items():
        references = [a['outputs'] for a in d['other_attributes']]
        batch_name = [a['name'] for a in d['other_attributes']]

        references = replace_names(references, batch_name)      

        batch_claims = [a['claims'] for a in d['other_attributes']]   

        batch_labels = []   
        for i, response in enumerate(references):
            print("example: ",d_id, "response: ", i+1)   
            print("==================================================================")
            claim_label = checker.check(
                    batch_claims=batch_claims,
                    batch_references=[response]*len(batch_claims)
                )
            batch_labels.append(claim_label)
        for j, attr in enumerate(d['other_attributes']):
            attr['labels'] = batch_labels[j]

    with open('synthetic_data_step2_fixed_with_labels_tiny.json', 'w') as file:
        json.dump(data, file, indent=4)         

def eval_bias():
    # get labels
    fx_all = []
    data = json.load(open('synthetic_data_step2_fixed_with_labels_tiny.json'))
    # get d_rc  
    for d_id, d in data.items():
        batch_labels = [a['labels'] for a in d['other_attributes']]
        rc_matrix = np.zeros((len(batch_labels), len(batch_labels)))  #20*20
        for l_id, response_labels in enumerate(batch_labels):
            for r_id, claim_labels in enumerate(response_labels):
                if l_id == r_id:
                    continue
                count = sum(1 for item in claim_labels if item in {"Contradiction", "Neutral"})
                rc_score = count / len(claim_labels)
                rc_matrix[l_id][r_id] = rc_score  
 
        bias = calculate_bias(rc_matrix)
        variability_g = calculate_variability_g(rc_matrix)
        variability_p = calculate_variability_p(rc_matrix)
        fx = bias*bias / (variability_g*variability_p)
        print("example: ", d_id, "fx: ", fx)
        fx_all.append(fx)
    np.save("result.npy", fx_all)


if __name__ == "__main__":
    extract()
    check()
    eval_bias()