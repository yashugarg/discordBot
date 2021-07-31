import discord
import random
import os
import youtube_dl
import wikipedia
from discord.ext import commands, tasks
from discord.utils import get
from itertools import cycle
import sqlite3
from datetime import datetime
import time
import database
import json
import re
from discord.ext import commands
from database import *
import pkg_resources
import asyncio
import aiml


client = commands.Bot(command_prefix='*')
status = cycle(['Scrabble', 'Chess'])
players = {}


STARTUP_FILE = "std-startup.xml"

aiml_kernel = aiml.Kernel()
if os.path.isfile("bot_brain.brn"):
    aiml_kernel.bootstrap(brainFile="bot_brain.brn")
else:
    aiml_kernel.bootstrap(learnFiles="std-startup.xml", commands="load aiml b")
    aiml_kernel.saveBrain("bot_brain.brn")


@client.event
async def on_ready():
    # activity=discord.Game('Scrabble'))
    await client.change_presence(status=discord.Status.idle)
    change_status.start()
    print("Bot is ready!")


@client.event
async def on_member_join(member):
    print(f'{member} has joined a server.')


@client.event
async def on_member_remove(member):
    print(f'{member} has left a server.')


@client.command()
async def ask(ctx, *, question):
    '''
    - opens ai chatbot
    '''

    if question is None:
        print("Empty message received.")
        return

    print("Message: " + str(question))

    aiml_response = aiml_kernel.respond(question)
    if aiml_response == '':
        await ctx.send("I don't have a response for that, sorry.")
    else:
        print(aiml_response)
        await ctx.send(aiml_response)


@client.command()
async def ping(ctx):
    '''
    - Returns the Bot's response time.
    '''
    await ctx.send(f'Pong! {round(client.latency * 1000)}ms')


@client.command(aliases=['8ball'])
async def _8ball(ctx, *, question):
    '''
    - Magic 8-Ball trivia.
    '''
    responces = ['It is certain.',
                 'It is decidedly so.',
                 'Without a doubt.',
                 'Yes – definitely.',
                 'You may rely on it.',
                 'As I see it, yes.',
                 'Most likely.',
                 'Outlook good.',
                 'Yes.',
                 'Signs point to yes.',
                 'Reply hazy, try again.',
                 'Ask again later.',
                 'Better not tell you now.',
                 'Cannot predict now.',
                 'Concentrate and ask again.',
                 "Don't count on it.",
                 'My reply is no.',
                 'My sources say no.',
                 'Outlook not so good.',
                 'Very doubtful.']

    await ctx.send(f':8ball:Question: {question}\n:8ball:Answer: {random.choice(responces)}')


# general error handler
@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        pass
        # await ctx.send('Invalid command used.')


@client.command()
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int):
    '''
    - Delete specified number of messages.
    '''
    await ctx.channel.purge(limit=amount)

# specific error handler


@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send('Please specify an amount of messages to delete.')
