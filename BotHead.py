import discord
from discord.ext import commands, tasks
import os
from tools.basicTools import readJson, readToken, readURLToken
import sys

#!/usr/bin/env python3

testing = True
networkd = False


if len(sys.argv) == 3:
    networkd = True
    ip = str(sys.argv[2])
    if "false" in sys.argv[1] or "False" in sys.argv[1]:
        testing = False
elif len(sys.argv) == 2:
    if "false" in sys.argv[1] or "False" in sys.argv[1]:
        testing = False

if (networkd):
    if testing:
        token = readURLToken(f"http://{ip}/Testtoken.txt")
    else:
        token = readURLToken(f"http://{ip}/Livetoken.txt")
else:
    if testing:
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


#@tasks.loop(seconds=10, minutes=1, hours=0)
#async def change_status():
#    if client.is_ready():
#        await client.change_presence(status=discord.Status.online, activity=discord.Game('listening'))
#    else:
#        await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('working'))


client.run(token)
