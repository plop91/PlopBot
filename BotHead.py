import discord
from discord.ext import commands
import os
from tools.basicTools import readJson
import sys
import mysql.connector

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
        client.load_extension(f'cogs.{f[:-3]}')


@client.command(brief="Admin only command: Load a Cog.")
async def load(ctx, extension):
    client.add_cog(f'cogs.{extension}')
    print(f'cog:{extension} loaded')
    await ctx.message.delete()


@client.command(brief="Admin only command: Unload a Cog.")
async def unload(ctx, extension):
    client.remove_cog(f'cogs.{extension}')
    print(f'cog:{extension} unloaded')
    await ctx.message.delete()


@client.command(brief="Admin only command: Reload a Cog.")
async def reload(ctx, extension):
    client.remove_cog(f'cogs.{extension}')
    print(f'cog:{extension} unloaded')
    client.add_cog(f'cogs.{extension}')
    print(f'cog:{extension} loaded')
    await ctx.message.delete()


@client.event
async def on_ready():
    print(f"""Logged on as {client.user}!""")
    await client.change_presence(status=discord.Status.online, activity=discord.Game('listening'))


@client.event
async def on_disconnect():
    await client.change_presence(status=discord.Status.offline, activity=discord.Game('sleeping'))


if token:
    client.run(token)
