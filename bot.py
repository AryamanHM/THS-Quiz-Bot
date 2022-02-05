import os
import discord
import requests
import json
import random
from replit import db
from keep_alive import keep_alive
from dotenv import load_dotenv
from discord.ext import commands
import time
import asyncio
import requests
import logging
from html import unescape
load_dotenv()

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

ANSWER_WAIT_TIME = 10
NEXT_Q_WAIT_TIME = 3

README_TEXT = (
    'This is Kerwhizz, a bot designed to mediate quizzes in your discord channel.'
    '\n'
    '\nCommands:'
    '\n---------'
    '\n!quiz - This help text.'
    '\n!quiz Categories - This returns a list of possible categories to choose from.'
    '\n!quiz <N> <Difficulty> <Category> - This is the main command to generate quiz questions.Add double spaces before Category.'
    '\n\t- N: Number of questions - Must be between 1 and 10 (inclusive).'
    '\n\t- Difficulty: Question difficulty - Must be one of "Easy", "Medium", "Hard", or "Any".'
    '\n\t- Category: Question category - Must be a possible category (can be found by typing "!quiz Categories") or Any"'
)

# Make the categories more intuitive to the user
def simplify_category(category_name):
    return category_name.split(':')[-1]

# Create a simpler mapping
CATEGORY_MAPPING = CATEGORY_MAPPING
SIMPLIFIED_CAT_MAPPING = {}
for key in CATEGORY_MAPPING.keys():
    SIMPLIFIED_CAT_MAPPING[simplify_category(key)] = CATEGORY_MAPPING[key]

categories_arr = list(SIMPLIFIED_CAT_MAPPING.keys())
categories_str = ';\t'.join(categories_arr)


difficulty_arr = ['Easy', 'Medium', 'Hard', 'Any']
class Quizbot(discord.Client):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        # We do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        # Our flag to interact with our bot is !quiz  
        if message.content.startswith('!quiz'):

            commands = message.content.lstrip('!quiz')
            commands = commands.strip(' ')

            # If this is the only call then we return the README text
            if commands == '':
                await message.channel.send(README_TEXT)

            elif commands == 'Categories':
                await message.channel.send(categories_str)

            else:
                try:
                    num_questions, difficulty, category = commands.split(' ', 2)
                except ValueError:
                    await message.channel.send('Please enter your request as !quiz <num_questions> <difficulty> <category>.')

                # Check that number of questions are valid
                try:
                    assert int(num_questions) <= 10
                except AssertionError:
                    await message.channel.send('Please enter a number between 1 and 10.')
                except ValueError:
                    await message.channel.send('Please enter a number as the first argument.')

                # Check difficult is valid
                if difficulty not in difficulty_arr:
                    await message.channel.send('Please enter a difficulty from the following: ' + ', '.join(difficulty_arr) + '.')
                difficulty = None if difficulty == 'Any' else difficulty

                # Check category is valid
                if category not in categories_arr + ['Any']:
                    await message.channel.send('Please enter a valid category. See "!quiz Categories" for a list of available choices.')
                category_id = '0' if category == 'Any' else SIMPLIFIED_CAT_MAPPING[category]

                # Retrieve the questions from the server
                trivia_request = get_trivia(
                    num_questions=num_questions,
                    difficulty=difficulty,
                    category_id=category_id
                )

                for trivia in trivia_request:
                    await message.channel.send(format_question(trivia['question'], trivia['options']))
                    time.sleep(ANSWER_WAIT_TIME)
                    await message.channel.send(f'The answer is: **{trivia["answer"]}**')

                    time.sleep(NEXT_Q_WAIT_TIME)   
client=Quizbot()
keep_alive()
client.run(os.getenv('TOKEN'))                     
