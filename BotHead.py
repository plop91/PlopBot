from discord.ext import commands
import settings
import discord
import datetime
import os

client = commands.Bot(command_prefix='.')


@client.command(brief="Admin only command: Load a Cog.")
async def load(ctx, extension):
    print(f"""{datetime.datetime.now()}: load from {ctx.author} """)
    if str(ctx.message.channel) in settings.json["command_channels"]:
        client.add_cog(f'{extension}')
        print(f'cog:{extension} loaded')
        await ctx.message.delete()


@client.command(brief="Admin only command: Unload a Cog.")
async def unload(ctx, extension):
    print(f"""{datetime.datetime.now()}: unload from {ctx.author}""")
    if str(ctx.message.channel) in settings.json["command_channels"]:
        client.remove_cog(f'{extension}')
        print(f'cog:{extension} unloaded')
    await ctx.message.delete()


@client.command(brief="Admin only command: Reload a Cog.")
async def reload(ctx, extension):
    print(f"""{datetime.datetime.now()}: reload from {ctx.author}""")
    if str(ctx.message.channel) in settings.json["command_channels"]:
        client.remove_cog(f'{extension}')
        print(f'cog:{extension} unloaded')
        client.add_cog(f'{extension}')
        print(f'cog:{extension} loaded')
    await ctx.message.delete()


@client.event
async def on_ready():
    print(f"""{datetime.datetime.now()}: Logged on as {client.user}!""")
    await client.change_presence(status=discord.Status.online, activity=discord.Game('listening'))


@client.event
async def on_disconnect():
    print(f"""{datetime.datetime.now()}: Logged off!""")
    await client.change_presence(status=discord.Status.offline, activity=discord.Game('sleeping'))


if __name__ == "__main__":

    settings.init(db_host="192.168.1.250", db_username="discord", db_password="plop9100")

    for f in os.listdir('./cogs'):
        if f.endswith('.py'):
            client.load_extension(f'cogs.{f[:-3]}')

    client.run(settings.token)
