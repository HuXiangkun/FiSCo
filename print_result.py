import json

path = '/home/ubuntu/wyw/refchecker_fairness/results/Jurassic_Ultra/age/ttest.json'

results = json.load(open(path))
for _, r in results.items():
    print(r['p-value']) 
