import re
import numpy as np
from scipy.stats import mannwhitneyu, ttest_ind 
import pandas as pd
from scipy.stats import f_oneway
from statsmodels.stats.multicomp import pairwise_tukeyhsd 
 
# replace names in sentences with a placeholder
def replace_names(sentences, names):
    replaced_sentences = []
    for sentence in sentences:
        for name in names:
            sentence = re.sub(r'\b{}\b'.format(re.escape(name)), "", sentence)
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


def anova(similarity_matrix, num_groups=5, n=10):
    # 提取组内相似度
    intra_group_similarities = []
    for i in range(num_groups):
        start_index = i * n
        end_index = start_index + n
        group_matrix = similarity_matrix[start_index:end_index, start_index:end_index]
        intra_group_similarities.append(group_matrix[np.triu_indices(n, k=1)])  # 提取上三角部分，不包括对角线

    # 提取组间相似度
    inter_group_similarities = []
    for i in range(num_groups):
        for j in range(i + 1, num_groups):
            start_i = i * n
            end_i = start_i + n
            start_j = j * n
            end_j = start_j + n
            inter_group_similarities.append(similarity_matrix[start_i:end_i, start_j:end_j].flatten())

    # 合并所有数据为单一数组进行ANOVA
    all_similarities = np.concatenate(intra_group_similarities + inter_group_similarities)
    groups = []
    for i in range(num_groups):
        groups += [f'Group{i+1}_Intra'] * len(intra_group_similarities[i])
    for i in range(num_groups):
        for j in range(i + 1, num_groups):
            groups += [f'Group{i+1}_Group{j+1}_Inter'] * n * n

    # ANOVA
    f_val, p_val = f_oneway(*intra_group_similarities, *inter_group_similarities)
    print('ANOVA result: F =', f_val, ', p =', p_val)

    # Tukey's HSD
    df = pd.DataFrame({'value': all_similarities, 'group': groups})
    tukey = pairwise_tukeyhsd(endog=df['value'], groups=df['group'], alpha=0.05)
    print(tukey)
