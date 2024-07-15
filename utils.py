import time

from openai.types import Completion as OpenAICompletion
from openai import RateLimitError as OpenAIRateLimitError
from openai import APIError as OpenAIAPIError
from openai import Timeout as OpenAITimeout

from litellm import batch_completion
from litellm.types.utils import ModelResponse

# Setup spaCy NLP
nlp = None

# Setup OpenAI API
openai_client = None

# Setup Claude 2 API
bedrock = None
anthropic_client = None


def get_model_batch_response(
        prompts,
        model='bedrock/anthropic.claude-3-sonnet-20240229-v1:0',
        temperature=0,
        n_choices=1,
        max_new_tokens=500,
        api_base=None
):
    """
    Get batch generation results with given prompts.

    Parameters
    ----------
    prompts : List[str]
        List of prompts for generation.
    temperature : float, optional
        The generation temperature, use greedy decoding when setting
        temperature=0, defaults to 0.
    model : str, optional
        The model for generation, defaults to 'bedrock/anthropic.claude-3-sonnet-20240229-v1:0'.
    n_choices : int, optional
        How many samples to return for each prompt input, defaults to 1.
    max_new_tokens : int, optional
        Maximum number of newly generated tokens, defaults to 500.

    Returns
    -------
    response_list : List[str]
        List of generated text.
    """
    if not prompts or len(prompts) == 0:
        raise ValueError("Invalid input.")

    message_list = []
    for prompt in prompts:
        if len(prompt) == 0:
            raise ValueError("Invalid prompt.")
        if isinstance(prompt, str):
            messages = [{
                'role': 'user',
                'content': prompt
            }]
        elif isinstance(prompt, list):
            messages = prompt
        else:
            raise ValueError("Invalid prompt type.")
        message_list.append(messages)
    import litellm
    litellm.suppress_debug_info = True
    # litellm.drop_params=True
    while True:
        responses = batch_completion(
            model=model,
            messages=message_list,
            temperature=temperature,
            n=n_choices,
            max_tokens=max_new_tokens,
            api_base=api_base
        )
        if all([isinstance(r, ModelResponse) for r in responses]):
            if n_choices == 1:
                response_list = [r.choices[0].message.content for r in responses]
            else:
                response_list = [[res.message.content for res in r.choices] for r in responses]
            # for r in response_list:
            #     if not r or len(r) == 0:
            #         raise ValueError(f'{model} API returns None or empty string')
            return response_list
        else:
            exception = None
            for e in responses:
                if isinstance(e, ModelResponse):
                    continue
                elif isinstance(e, OpenAIRateLimitError) or isinstance(e, OpenAIAPIError) or isinstance(e, OpenAITimeout):
                    exception = e
                    break
                else:
                    print('Exit with the following error:')
                    print(e)
                    return None
            
            print(f"{exception} [sleep 10 seconds]")
            time.sleep(10)
            continue