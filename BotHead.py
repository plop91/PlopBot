import discord
from discord.ext import commands, tasks
import os
from tools.basicTools import readJson, addToJson
import sys
import random
import mysql.connector

# !/usr/bin/env python3

testing = True

if len(sys.argv) == 2:
    if "false" in sys.argv[1] or "False" in sys.argv[1]:
        testing = False

db = mysql.connector.connect(
    host="192.168.1.250",
    user="discord",
    password="plop9100",
    database="discord"
)

my_cursor = db.cursor()
token = None

if testing:
    sql = "SELECT * FROM tokens WHERE name ='Test'"
    my_cursor.execute(sql)
    my_result = my_cursor.fetchall()
    for x in my_result:
        token = x[1]
else:
    sql = "SELECT * FROM tokens WHERE name ='Live'"
    my_cursor.execute(sql)
    my_result = my_cursor.fetchall()
    for x in my_result:
        token = x[1]

json_name = "info.json"
json = readJson(json_name)
client = commands.Bot(command_prefix='.')

for f in os.listdir('./cogs'):
    if f.endswith('.py'):
        # uses splicing "[:-3]" to cut off last part of file name
        client.load_extension(f'cogs.{f[:-3]}')


@client.command()
async def load(ctx, extension):
    client.add_cog(f'cogs.{extension}')
    print(f'cog:{extension} loaded')
    await ctx.message.delete()


@client.command()
async def unload(ctx, extension):
    client.remove_cog(f'cogs.{extension}')
    print(f'cog:{extension} unloaded')
    await ctx.message.delete()


@client.command()
async def reload(ctx, extension):
    client.remove_cog(f'cogs.{extension}')
    print(f'cog:{extension} unloaded')
    client.add_cog(f'cogs.{extension}')
    print(f'cog:{extension} loaded')
    await ctx.message.delete()


@client.command()
async def echo(ctx, tag):
    if tag:
        await client.change_presence(status=discord.Status.online, activity=discord.Game(tag))
        addToJson(json_name, "status", tag)
        await ctx.message.delete()


@client.event
async def on_ready():
    print(f"""Logged on as {client.user}!""")
    await client.change_presence(status=discord.Status.online, activity=discord.Game('listening'))


@client.event
async def on_disconnect():
    await client.change_presence(status=discord.Status.offline, activity=discord.Game('sleeping'))


@tasks.loop(seconds=10, minutes=0, hours=0)
async def change_status():
    u_json = readJson(json_name)
    await client.change_presence(status=discord.Status.online, activity=discord.Game(
        u_json["status"][random.randint(0, len(u_json["status"]))]))


# @.loop(seconds=10, minutes=1, hours=0)
# async def change_status():
#    if client.is_ready():
#        await client.change_presence(status=discord.Status.online, activity=discord.Game('listening'))
#    else:
#        await client.change_presence(status=discord.Status.do_not_disturb, activity=discord.Game('working'))

if token:
    client.run(token)
