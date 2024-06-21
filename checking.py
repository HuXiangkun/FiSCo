from refchecker import LLMExtractor, LLMChecker
import json


def extract():
    extractor = LLMExtractor(
        model='bedrock/anthropic.claude-3-sonnet-20240229-v1:0',
        batch_size=8
    )
    data = json.load(open('synthetic_data_step2_fixed.json'))
    
    # TODO: replace names with placeholder
    
    for d_id, d in data.items():
        batch_responses = [a['outputs'] for a in d['other_attributes']]
        response_extract_results = extractor.extract(
            batch_responses=batch_responses
        )
        response_claims = [[c.content for c in res.claims] for res in response_extract_results]
        print(response_claims)
        break
    
    # TODO: save claims to file

def check():
    checker = LLMChecker(
        model='bedrock/anthropic.claude-3-sonnet-20240229-v1:0',
        batch_size=8
    )
    for d_id, d in data.items():
        checker.check(
            batch_claims=
            batch_references=
        )

    # TODO: save labels


def eval_bias():
    # TODO


if __name__ == "__main__":
    extract()
    check()
    eval_bias()