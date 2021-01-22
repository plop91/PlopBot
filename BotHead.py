from discord.ext import commands
import settings
import discord
import os

# Initialize settings to connect to database, open json and setup logging
settings.init(db_host="192.168.1.250", db_username="discord", db_password="plop9100")
client = commands.Bot(command_prefix='.')


# Loads a new cog into the bot while running
@client.command(brief="Admin only command: Load a Cog.")
async def load(ctx, extension):
    settings.logger.info(f"load: {extension} :: from {ctx.author}")
    if ctx.author not in settings.info_json["admins"]:
        settings.logger.warning(f"User: {ctx.author} is not an admin but tried to load a cog!")
    elif str(ctx.message.channel) not in settings.info_json["command_channels"]:
        settings.logger.info(f"User: {ctx.author} is an admin but tried to load in a non command channel!")
    else:
        client.load_extension(f'cogs.{extension}Cog')
        settings.logger.info(f"cog:{extension} loaded")
        await ctx.message.delete()


# Unloads an active cog from the bot
@client.command(brief="Admin only command: Unload a Cog.")
async def unload(ctx, extension):
    settings.logger.info(f"unload: {extension} :: from {ctx.author}")
    if ctx.author not in settings.info_json["admins"]:
        settings.logger.warning(f"User: {ctx.author} is not an admin but tried to unload a cog!")
    elif str(ctx.message.channel) not in settings.info_json["command_channels"]:
        settings.logger.info(f"User: {ctx.author} is an admin but tried to unload in a non command channel!")
    else:
        client.unload_extension(f'cogs.{extension}Cog')
        settings.logger.info(f"cog:{extension} unloaded")
    await ctx.message.delete()


# Unloads then reloads a cog
@client.command(brief="Admin only command: Reload a Cog.")
async def reload(ctx, extension):
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


# Logs that the cog was loaded properly
@client.event
async def on_ready():
    settings.logger.info(f"Logged on as {client.user}!")
    await client.change_presence(status=discord.Status.online, activity=discord.Game('listening'))


# Logs the bot turning off
@client.event
async def on_disconnect():
    settings.logger.info(f"Logged off!")
    await client.change_presence(status=discord.Status.offline, activity=discord.Game('sleeping'))


# Load cogs and start bot
if __name__ == "__main__":

    for f in os.listdir('./cogs'):
        if f.endswith('.py'):
            client.load_extension(f'cogs.{f[:-3]}')

    client.run(settings.token)
