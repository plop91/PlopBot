"""
Driver file for Bot


"""

from discord.ext import commands
import settings
import discord
import argparse
import os

parser = argparse.ArgumentParser(prog='Discord Bot',
                                 description='a discord bot with a soundboard and some additional features.')

parser.add_argument('--json', help='Path to json file', default='info.json')
parser.add_argument('--db_host', help='Database hostname or ip by default taken from json file', default=None)
parser.add_argument('--db_username', help='Database username by default taken from json file', default=None)
parser.add_argument('--db_password', help='Database password by default taken from json file', default=None)
parser.add_argument('--db_name', help='Database name by default taken from json file', default=None)

args = parser.parse_args()

# Initialize settings to connect to database, open json and setup logging
settings.init(args)

client = commands.Bot(command_prefix='.')


@client.command(brief="Admin only command: Load a Cog.")
async def load(ctx, extension):
    """Loads a new cog into the bot while running"""
    settings.logger.info(f"load: {extension} :: from {ctx.author}")
    if ctx.author not in settings.info_json["admins"]:
        settings.logger.warning(f"User: {ctx.author} is not an admin but tried to load a cog!")
    elif str(ctx.message.channel) not in settings.info_json["command_channels"]:
        settings.logger.info(f"User: {ctx.author} is an admin but tried to load in a non command channel!")
    else:
        client.load_extension(f'cogs.{extension}Cog')
        settings.logger.info(f"cog:{extension} loaded")
        await ctx.message.delete()


@client.command(brief="Admin only command: Unload a Cog.")
async def unload(ctx, extension):
    """Unloads an active cog from the bot"""
    settings.logger.info(f"unload: {extension} :: from {ctx.author}")
    if ctx.author not in settings.info_json["admins"]:
        settings.logger.warning(f"User: {ctx.author} is not an admin but tried to unload a cog!")
    elif str(ctx.message.channel) not in settings.info_json["command_channels"]:
        settings.logger.info(f"User: {ctx.author} is an admin but tried to unload in a non command channel!")
    else:
        client.unload_extension(f'cogs.{extension}Cog')
        settings.logger.info(f"cog:{extension} unloaded")
    await ctx.message.delete()


@client.command(brief="Admin only command: Reload a Cog.")
async def reload(ctx, extension):
    """Unloads then reloads a cog"""
    settings.logger.info(f"reload: {extension} :: from {ctx.author}")
    if ctx.author not in settings.info_json["admins"]:
        settings.logger.warning(f"User: {ctx.author} is not an admin but tried to reload a cog!")
    elif str(ctx.message.channel) not in settings.info_json["command_channels"]:
        settings.logger.info(f"User: {ctx.author} is an admin but tried to reload in a non command channel!")
    else:
        client.unload_extension(f'cogs.{extension}Cog')
        settings.logger.info(f"reload from {ctx.author} unloaded")
        client.load_extension(f'cogs.{extension}Cog')
        settings.logger.info(f"reload from {ctx.author} loaded")
    await ctx.message.delete()


@client.event
async def on_ready():
    """Logs that the cog was loaded properly"""
    settings.logger.info(f"Logged on as {client.user}!")
    await client.change_presence(status=discord.Status.online, activity=discord.Game('listening'))


@client.event
async def on_disconnect():
    """Logs the bot turning off"""
    settings.logger.info(f"Logged off!")
    await client.change_presence(status=discord.Status.offline, activity=discord.Game('sleeping'))


# Load cogs and start bot
if __name__ == "__main__":

    for f in os.listdir('./cogs'):
        if f.endswith('.py'):
            client.load_extension(f'cogs.{f[:-3]}')

    client.run(settings.token)
