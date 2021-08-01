import discord
from discord.ext import commands


class Test(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.command(aliases=['hi', 'Hello', 'hello', 'Hey', 'hey'])
    async def Hi(self, ctx):
        '''
        - Selfie-ish says Hi.
        '''
        await ctx.send('Selfie-ish says Hi! :smile_cat:')


def setup(client):
    client.add_cog(Test(client))
