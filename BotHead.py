import discord
from discord.ext import commands, tasks
from itertools import cycle
import json
import os
from tools.basicTools import readJson, readToken
testing = False
if testing == True:
    token = readToken("Testtoken.txt")
else:
    token = readToken("Livetoken.txt")
info = readJson("info.json")
client = commands.Bot(command_prefix='.')

for f in os.listdir('./cogs'):
    if f.endswith('.py'):
        # uses splicing "[:-3]" to cut off last part of file name
        client.load_extension(f'cogs.{f[:-3]}')


@client.command()
async def load(ctx, extention):
    client.add_cog(f'cogs.{extention}')
    print(f'cog:{extention} loaded')


@client.command()
async def unload(ctx, extention):
    client.remove_cog(f'cogs.{extention}')
    print(f'cog:{extention} unloaded')


@client.command()
async def reload(ctx, extention):
    client.remove_cog(f'cogs.{extention}')
    print(f'cog:{extention} unloaded')
    client.add_cog(f'cogs.{extention}')
    print(f'cog:{extention} loaded')


@client.event
async def on_ready():
    await client.change_presence(status=discord.Status.online, activity=discord.Game('listening'))


@client.event
async def on_disconnect():
    await client.change_presence(status=discord.Status.offline, activity=discord.Game('sleeping'))

@tasks.loop(seconds=10,minutes=0,hours=0)
async def change_status():
    if client.is_ready():
        await client.change_presence(status=discord.Status.online, activity=discord.Game('listening'))
    else:
        await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('working'))


client.run(token)
