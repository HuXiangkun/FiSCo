import json
import re,os
import numpy as np
from scipy.stats import mannwhitneyu, ttest_ind 
 
 
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
    return bias

# calculate V_g(p(x))
def calculate_variability_g(matrix, n=10):
    variability = 0
    for i in range(n, 2*n):
        for j in range(i + 1, 2*n):
            variability += (matrix[i][j] + matrix[j][i]) / 2
    variability *= 2 / (n * (n - 1))
    return variability

# calculate V_p(g(x))
def calculate_variability_p(matrix, n=10):
    variability = 0
    for i in range(n):
        for j in range(i + 1, n):
            variability += (matrix[i][j] + matrix[j][i]) / 2
    variability *= 2 / (n * (n - 1))
    return variability

def get_groups(similarity_matrix):
    mask = np.eye(len(similarity_matrix), dtype=bool)
    length = int(len(similarity_matrix)*0.5)
    similarity_matrix[mask] = np.nan  
    group1_similarity = similarity_matrix[:length, :length] 
    group2_similarity = similarity_matrix[length:, length:] 
    group3_similarity = similarity_matrix[:length, length:].flatten()

    triu_indices_group1 = np.triu_indices(group1_similarity.shape[0])
    triu_indices_group2 = np.triu_indices(group1_similarity.shape[0])

    group1_similarity = group1_similarity[triu_indices_group1].flatten()
    group2_similarity = group2_similarity[triu_indices_group2].flatten()    

    group1_similarity = group1_similarity[~np.isnan(group1_similarity)]
    group2_similarity = group2_similarity[~np.isnan(group2_similarity)]
    inter_group_similarity = group3_similarity[~np.isnan(group3_similarity)]

    return group1_similarity, group2_similarity, inter_group_similarity

def calculate_distance(group1_similarity,group2_similarity):

    u_statistic, p_value = mannwhitneyu(group1_similarity, group2_similarity, alternative='two-sided')
    distance = 2*abs(u_statistic/(len(group1_similarity)*len(group2_similarity))-0.5)

    return distance, p_value

def calculate_similarity(score_matrix, length_matrix):
    similarity_matrix = np.zeros((len(score_matrix[0]), len(score_matrix[0])))
    for i in range(len(score_matrix)):
        for j in range(len(score_matrix[i])):
            if i == j:
                similarity_matrix[i][j] = 1
                continue
            if similarity_matrix[i][j] + length_matrix[j][i] == 0:
                similarity_matrix[i][j] = np.nan
            else:
                similarity_matrix[i][j] = (score_matrix[i][j] + score_matrix[j][i]) / (length_matrix[i][j]+length_matrix[j][i]) 

    return similarity_matrix

def u_test(similarity_matrix):        
    group1_similarity, group2_similarity, inter_group_similarity = get_groups(similarity_matrix)
    length1= len(group1_similarity)
    length2= len(group2_similarity)
    u_inter, p_inter = calculate_distance(np.concatenate((group1_similarity,group2_similarity)),inter_group_similarity)    
    
    u_intra1, p_intra1 = calculate_distance(group1_similarity[:int(0.5*length1)], group1_similarity[int(0.5*length1):])
    u_intra2, p_intra2 = calculate_distance(group2_similarity[:int(0.5*length2)], group2_similarity[int(0.5*length2):]) 
    
    final = u_inter-0.5*(u_intra1+u_intra2)

    return u_inter,p_inter,u_intra1,p_intra1,u_intra2,p_intra2,final   

def t_test(similarity_matrix):
    group1_similarity, group2_similarity, inter_group_similarity = get_groups(similarity_matrix)
    t, p = ttest_ind(np.concatenate((group1_similarity,group2_similarity)),inter_group_similarity, equal_var=False)
    return t,p    

