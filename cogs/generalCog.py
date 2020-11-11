from discord.ext import commands, tasks
from utility.tools import readJson, addToJson
import settings
import discord
import random
import datetime


class general(commands.Cog):

    def __init__(self, client, info):
        self.client = client
        self.info = info

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""{datetime.datetime.now()}: general cog ready!""")
        self.change_status.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        _id = message.guild
        message.content = message.content.strip().lower()
        print(f"""{datetime.datetime.now()}: Message from {message.author}: {message.content}""")
        if message.author != self.client.user:
            if message.content.lower() == "hey":
                await message.channel.send("Hi")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        print(f'{datetime.datetime.now()}: deleted message- {message.author} : {message.content}')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        print(f'{datetime.datetime.now()}: member joined- {member}')

        for channel in member.guild.channels:
            if str(channel) in self.info["welcome_channels"]:
                await channel.send(f"""Who the fuck are you {member.mention}?""")

    @commands.command(brief="Change the bot presence to the argument string.")
    async def echo(self, ctx, tag):
        print(f"""{datetime.datetime.now()}: echo from {ctx.author} : {tag}""")
        if tag:
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game(tag))
            addToJson("info.json", settings.json, "status", tag)
            await ctx.message.delete()

    @commands.command(brief="List the previous statuses the bot will loop through.")
    async def status(self, ctx):
        print(f"""{datetime.datetime.now()}: status from {ctx.author}""")
        s = ""
        for status in settings.json["status"]:
            s += status + ", "

        embed_var = discord.Embed(title="Status:", description=s, color=0x00ff00)

        await ctx.channel.send(embed=embed_var)
        await ctx.message.delete()

    @tasks.loop(seconds=0, minutes=0, hours=1)
    async def change_status(self):
        print(f"""{datetime.datetime.now()}: status changed automatically""")
        await self.client.change_presence(status=discord.Status.online, activity=discord.Game(
            settings.json["status"][random.randint(0, len(settings.json["status"]) - 1)]))


def setup(client):
    client.add_cog(general(client, settings.json))
