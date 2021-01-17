from discord.ext import commands, tasks
from utility.tools import addToJson
import settings
import discord
import random


class general(commands.Cog):

    def __init__(self, client):
        self.client = client

    # Logs that the cog was loaded properly
    @commands.Cog.listener()
    async def on_ready(self):
        settings.logger.info(f"general cog ready!")
        self.change_status.start()

    # logs any incoming messages and responds to 'hey' with 'hi'.
    @commands.Cog.listener()
    async def on_message(self, message):
        _id = message.guild
        message.content = message.content.strip().lower()
        settings.logger.info(f"Message from {message.author}: {message.content}")
        if message.author != self.client.user:
            if message.content.lower() == "hey":
                await message.channel.send("Hi")

    # logs any deleted messages
    @commands.Cog.listener()
    async def on_message_delete(self, message):
        settings.logger.info(f"deleted message- {message.author} : {message.content}")

    # Greets new members to the server with a random welcome message
    @commands.Cog.listener()
    async def on_member_join(self, member):
        settings.logger.info(f"member joined- {member}")
        for channel in member.guild.channels:
            if str(channel) in settings.json["welcome_channels"]:
                await channel.send(f"""{random.choice(settings.json["welcome_messages"])} {member.mention}?""")

    # Changes the bot status in discord and adds the status to list of usable statuses
    @commands.command(brief="Change the bot presence to the argument string.")
    async def echo(self, ctx, tag):
        settings.logger.info(f"echo from {ctx.author} : {tag}")
        if tag:
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game(tag))
            addToJson("info.json", settings.json, "status", tag)
            await ctx.message.delete()

    # Lists statuses the bot will cycle through every hour and a half.
    @commands.command(brief="List the previous statuses the bot will loop through.")
    async def status(self, ctx):
        settings.logger.info(f"status from {ctx.author}")

        embed_var = discord.Embed(title="Status:", description="", color=0x00ff00)
        s = ""
        for status in settings.json["status"]:
            if len(s) + len(status) >= 1024:
                embed_var.add_field(name="status:", value=s, inline=False)
                s = ""
            s += status + ", "
        embed_var.add_field(name="status:", value=s, inline=False)

        await ctx.channel.send(embed=embed_var)
        await ctx.message.delete()

    # changes the bot to a randomly provided status.
    @tasks.loop(seconds=0, minutes=30, hours=1)
    async def change_status(self):
        settings.logger.info(f"status changed automatically")
        await self.client.change_presence(status=discord.Status.online, activity=discord.Game(
            settings.json["status"][random.randint(0, len(settings.json["status"]) - 1)]))


def setup(client):
    client.add_cog(general(client))
