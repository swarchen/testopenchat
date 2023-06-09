import openai
from dotenv import load_dotenv
import os
import logging

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s:%(levelname)s:%(message)s')

openai.api_key = os.getenv("OPENAI_API_KEY")

def get_completion(prompt, model="gpt-3.5-turbo"):
    messages = [{"role": "user", "content": prompt}]
    logging.info(f"Getting completion from OpenAI with prompt: {prompt}")
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=0.8, # this is the degree of randomness of the model's output
    )
    logging.info(f"Received completion from OpenAI.")
    return response.choices[0].message["content"]

def get_completion_from_messages(messages, 
                                 model="gpt-3.5-turbo", 
                                 temperature=0, 
                                 max_tokens=500):
    logging.info(f"Getting completion from OpenAI with messages: {messages}")
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature, 
        max_tokens=max_tokens,
    )
    return response.choices[0].message["content"]

def copy_writer(filename):
    prompt = f"""
    You are an AI copywriter for a coloring page website.

    Your task is to craft an irresistible coloring page 'title' and 'description' that highlights the given image filename: '''{filename}'''

    Format your response as an array of JSON objects as the format like this(use double quotes):
    ```[{{"title": <Your creative title here>,"description": <Your joyful and friendly description here>}},...]```

    Please write 4 variations of the 'title' and 'description', each tailored to be SEO-friendly, and written in a friendly tone.
    Do not put 'coloring page', 'printable', 'coloring sheets' in the 'title'
    The 'title' should be adjective + filename. eg: if filename is butterfly, you should give me something like: 'Beautiful Butterfly', 'Flying Butterfly'
    The 'description' should be between 50-100 words.

    Let your creativity shine!
    """
    response = get_completion(prompt)
    logging.info(f"Generated copy using OpenAI. Response:\n {response}")
    return response


def categorization_assistant(filename, coloring_page_data, existing_categories):
    prompt = f"""
    As an AI categorizing assistant for a coloring page website, your task is to categorize the coloring page based on the 'coloring_page_data'. 

    Here is the coloring_page_data: '''{coloring_page_data}'''

    And these are the existing categories on the website:

    '''{existing_categories}'''

    Your goal is to identify at least 1 appropriate categories based on the given image filename.

    Format your response as an array of JSON objects. Each object must have 'id', 'name' keys.
    If no suitable category exists among the current ones, you just return empty array like this ```[]```. 

    Here is the expected format of your response:
    ```[{{"id": <Existed Category id here> or null,"name": <Category Name here>}}]```

    Only respond with the JSON object.
    """

    response = get_completion(prompt)
    logging.info(f"Categorized image using OpenAI. Response\n {response}")

    return response

def categorization_assistant_v2(categories, filename):
    delimiter = "####"
    system_message = f"""
    You will be provided with a filename delimited with {delimiter} characters.
    Classify the filename into all reasonable categories Must provide your output in an array of string format 
    ```["<Category here>", "<Category here>"]```

    Here are the reference categories: {categories}
    """
    messages =  [  
    {'role':'system', 
    'content': system_message},    
    {'role':'user', 
    'content': f"{delimiter}{filename}{delimiter}"},  
    ] 
    response = get_completion_from_messages(messages)
    logging.info(f"Categorized image using OpenAI. Response\n {response}")

    return response

def idea_generation(keyword_planner_report):
    prompt = f"""
    You are an creative AI assistant of a coloring page website.
    Your task is to craft the coloring page subjects for me to draw.
    Here are the keyword planner report from google ads is delimited with triple backticks

    keyword planner report: '''{keyword_planner_report}'''

    Now I need you give me 100 creative subjects that I can draw.
    The subjects should be a sentence and less than 15 words.
    Format your response as a csv format. 
    '''<subject 1>, <subject 2>, <subject 3> ...'''

    You don't need to put 'coloring page', 'printable', 'coloring sheets' text in the subjects
    Let your creative shine! 
    """
    response = get_completion(prompt)
    print(response)

def multilingual_translator(coloring_page):
    prompt = f"""
    You are an multilingual AI copywriter for a coloring page website.

    Your task is to craft irresistible coloring page 'title' and 'description' that highlights the given coloring_page: '''{coloring_page}'''
    in these languages Spanish - es, Russian - ru, German - de, French - fr, Japanese - ja, Portuguese - pt, Turkish - tr

    Format your response as an array of JSON objects as the format like this(use double quotes):
    ```[{{"language_code": <es | ru | de | fr | ja | pt | tr>, "title": <Your creative title here>,"description": <Your joyful and friendly description here>}},...]```

    The 'description' should be between 50-100 words.
    The 'title' should be short and clear.

    Let your creativity shine!
    """
    response = get_completion(prompt)
    logging.info(f"Generated copy using OpenAI. Response:\n {response}")
    return response

def multilingual_translator_category(category):
    prompt = f"""
    You are an multilingual AI copywriter for a coloring page website.

    Your task is to translate category 'name' and write 'description' that highlights the given english category name: '''{category}'''
    in these languages Spanish - es, Russian - ru, German - de, French - fr, Japanese - ja, Portuguese - pt, Turkish - tr

    Format your response as an array of JSON objects as the format like this(use double quotes):
    ```[{{"language_code": <es | ru | de | fr | ja | pt | tr>, "name": <Your translated category name>,"description": <Your joyful and friendly description here>}},...]```

    The 'name' should be short and clear.
    The 'description' should be between 50-100 words.
    """
    response = get_completion(prompt)
    logging.info(f"Generated copy using OpenAI. Response:\n {response}")
    return response
