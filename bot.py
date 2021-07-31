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


@client.command()
# @commands.check(is_it_me)
async def user(ctx):
    '''
    - Returns the username.
    '''
    await ctx.send(f'Hi! I am {ctx.author}')


@client.command()
async def kick(ctx, member: discord.Member, *, reason=None):
    '''
    - Kick members from the server.
    '''
    await member.kick(reason=reason)
    await ctx.send(f'Kicked {member.mention}')


@client.command()
async def ban(ctx, member: discord.Member, *, reason=None):
    '''
    - Ban members from the server.
    '''
    await member.ban(reason=reason)
    await ctx.send(f'Banned {member.mention}')


@client.command()
async def unban(ctx, *, member):
    '''
    - Unban banned members from the server.
    '''
    banned_users = await ctx.guild.bans()
    member_name, member_discriminator = member.split('#')

    for ban_entry in banned_users:
        user = ban_entry.user

        if (user.name, user.discriminator) == (member_name, member_discriminator):
            await ctx.guild.unban(user)

            await ctx.send(f'Unbanned {user.name}#{user.discriminator}')
            # same as ctx.send(f'Banned {user.mention}')
            return


@client.command()
async def load(ctx, extension):
    '''
    - Load the mentioned cogs file.
    '''
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f'{extension} Loaded')


@client.command()
async def unload(ctx, extension):
    '''
    - Unload the mentioned cogs file.
    '''
    client.unload_extension(f'cogs.{extension}')
    await ctx.send(f'{extension} Unloaded')


@client.command()
async def reload(ctx, extension):
    '''
    - Reload the mentioned cogs file.
    '''
    client.unload_extension(f'cogs.{extension}')
    client.load_extension(f'cogs.{extension}')
    await ctx.send(f'{extension} Reloaded')


@client.command(name='join', help='- Join the voice channel.')
async def join(ctx):

    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return

    else:
        channel = ctx.message.author.voice.channel
        print(f"The bot has connected to {channel}\n")

    await channel.connect()


@client.command(pass_context=True)
async def leave(ctx):
    '''
    - Disconnect from the voice channel.
    '''

    channel = ctx.message.author.voice.channel
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice and voice.is_connected():
        await voice.disconnect()
        print(f"The bot has left {channel}")
        await ctx.send(f"Left {channel}")
    else:
        print("Bot was told to leave voice channel, but was not in one")
        await ctx.send("Don't think I am in a voice channel")


@client.command(pass_context=True)
async def play(ctx, url):
    '''
    - Play YouTube audio using URL.
    '''

    song_there = os.path.isfile("song.mp3")
    try:
        if song_there:
            os.remove("song.mp3")
            print("Removed old song file")
    except PermissionError:
        print("Trying to delete song file, but it's being played")
        await ctx.send("ERROR: Music playing")
        return

    await ctx.send("Getting everything ready now")

    voice = get(client.voice_clients, guild=ctx.guild)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        print("Downloading audio now\n")
        ydl.download([url])

    for file in os.listdir("./"):
        if file.endswith(".mp3"):
            name = file
            print(f"Renamed File: {file}\n")
            os.rename(file, "song.mp3")

    voice.play(discord.FFmpegPCMAudio("song.mp3"),
               after=lambda e: print("Song done!"))
    voice.source = discord.PCMVolumeTransformer(voice.source)
    voice.source.volume = 0.1

    nname = name.rsplit("-", 2)
    await ctx.send(f"Playing: {nname[0]}")
    print("playing\n")


@client.command(pass_context=True)
async def pause(ctx):
    '''
    - Pause the playing audio.
    '''

    voice = get(client.voice_clients, guild=ctx.guild)

    if voice and voice.is_playing():
        print("Music paused")
        voice.pause()
        await ctx.send("Music paused")
    else:
        print("Music not playing failed pause")
        await ctx.send("Music not playing failed pause")

for filename in os.listdir('./cogs'):
    if filename.endswith('.py'):
        client.load_extension(f'cogs.{filename[:-3]}')


@client.command(pass_context=True)
async def resume(ctx):
    '''
    - Resume the paused audio.
    '''
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice and voice.is_paused():
        print("Resumed music")
        voice.resume()
        await ctx.send("Resumed music")
    else:
        print("Music is not paused")
        await ctx.send("Music is not paused")


@client.command(pass_context=True)
async def stop(ctx):
    '''
    - Stop the playing audio.
    '''
    voice = get(client.voice_clients, guild=ctx.guild)

    if voice and voice.is_playing():
        print("Music stopped")
        voice.stop()
        await ctx.send("Music stopped")
    else:
        print("No music playing failed to stop")
        await ctx.send("No music playing failed to stop")
