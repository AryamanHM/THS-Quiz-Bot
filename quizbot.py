#usr/bin/env python3.6

"""
This script handles the Quizbot class which is a child of the discord client class.
It's main function is to mediate the interactions between the discord users and the quiz API.
It should be able to provide the user with some basic commands, handle invalid commands,
and present the actual quiz element of the bot.
"""

import discord
import asyncio
import get_trivia
import time

ANSWER_WAIT_TIME = 10
NEXT_Q_WAIT_TIME = 3

README_TEXT = (
    'This is Quizbot, a bot designed to mediate quizzes in your discord channel.'
    '\n'
    '\nCommands:'
    '\n---------'
    '\n!quiz - This help text.'
    '\n!quiz Categories - This returns a list of possible categories to choose from.'
    '\n!quiz <N> <Difficulty> <Category> - This is the main command to generate quiz questions.'
    '\n\t- N: Number of questions - Must be between 1 and 10 (inclusive).'
    '\n\t- Difficulty: Question difficulty - Must be one of "Easy", "Medium", "Hard", or "Any".'
    '\n\t- Category: Question category - Must be a possible category (can be found by typing "!quiz Categories") or Any"'
)

# Make the categories more intuitive to the user
def simplify_category(category_name):
    return category_name.split(':')[-1]

# Create a simpler mapping
CATEGORY_MAPPING = get_trivia.CATEGORY_MAPPING
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
                trivia_request = get_trivia.get_trivia(
                    num_questions=num_questions,
                    difficulty=difficulty,
                    category_id=category_id
                )

                for trivia in trivia_request:
                    await message.channel.send(get_trivia.format_question(trivia['question'], trivia['options']))
                    time.sleep(ANSWER_WAIT_TIME)
                    await message.channel.send(f'The answer is: **{trivia["answer"]}**')
                    time.sleep(NEXT_Q_WAIT_TIME)
                                                                                                                                                                   

