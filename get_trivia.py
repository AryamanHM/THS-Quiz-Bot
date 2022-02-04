#usr/bin/env python3.6

"""
This script handles the interactions with the trivia api at: https://opentdb.com/api_config.php
We provide functions to retrieve questions from the api, as well as
functions to parser the payloads into a more usable format.
There is also a lookup provided between the question category IDs and the categories themselves.
This is necessary when making requests.
"""

import requests
import logging
from html import unescape

logger = logging.getLogger(__name__)

def get_categories():
    """
    Request list of categories from opentdb api and return as lookup


    Returns
    ------- 
        dict: mapping from the question category string to a numeric ID
    """

    logger.info('Retrieving all categories')

    r_url = 'https://opentdb.com/api_category.php'
    r = requests.get(r_url)
    r_json = r.json()

    trivia_categories = r_json['trivia_categories']    # an array of dicts {id: id:int, name: name:str}
    category_mapping = {
        cat['name']: str(cat['id'])
        for cat in trivia_categories
    }

    return category_mapping

CATEGORY_MAPPING = get_categories()

def get_category_id(category_name):
    return CATEGORY_MAPPING[category_name]

def get_trivia(
    category_id='9', 
    difficulty=None,
    num_questions='3'
):
    """
    Get JSON of trivia from API, with options to select category_name, difficulty, and number of questions.
    Return the payload as an array

    Parameters
    ----------
    category_name: str
        string giving the category_name for the questions
    difficulty: str or None
        string denoting difficulty of the questions. Options are Easy, Medium, Hard. If None then we don't specify
    num_questions: str
        string repr of integer giving number of questions to request.

    Returns
    -------
    Array of dictionaries of the type: {question: str, options: [strList], answer: str}
    """

    root_url = 'https://opentdb.com/api.php?'
    category_req = '' if category_id == '0' else f'category={category_id}'
    difficulty_req = '' if difficulty is None else f'difficulty={difficulty.lower()}'
    num_q_req = f'amount={num_questions}'

    query = [
        q
        for q in [category_req, difficulty_req, num_q_req]
        if q
    ]

    r_url = f'{root_url}' + '&'.join(query)

    trivia_payload = requests.get(r_url).json()['results']

    trivia_arr = [
        {
            'question': unescape(trivia['question']),
            'options': list(map(unescape, trivia['incorrect_answers'])) + [unescape(trivia['correct_answer'])],
            'answer': unescape(trivia['correct_answer']),
        } 
        for trivia in trivia_payload
    ]

    return trivia_arr

def format_question(question, options):
    """
    Create a string to send to the channel which handles asking the question and presenting the options
    """
    return '**' + question + '** \n- ' + '\n- '.join(options)