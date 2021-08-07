from discord.ext import commands, tasks
from settings import addToJson
import settings
import discord
import random


class general(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """Logs that the cog was loaded properly"""
        settings.logger.info(f"general cog ready!")
        self.change_status.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        """logs any incoming messages and responds to 'hey' with 'hi' to verify bot is functional."""
        _id = message.guild
        message.content = message.content.strip().lower()
        settings.logger.info(f"Message from {message.author}: {message.content}")
        if message.author != self.client.user:
            if message.content.strip().lower() == "hey":
                await message.channel.send("Hi")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """logs any deleted messages"""
        settings.logger.info(f"deleted message- {message.author} : {message.content}")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Greets new members to the server with a random welcome message"""
        settings.logger.info(f"member joined- {member}")
        for channel in member.guild.channels:
            if str(channel) in settings.info_json["welcome_channels"]:
                await channel.send(f"""{random.choice(settings.info_json["welcome_messages"])} {member.mention}?""")

    @commands.command(brief="Change the bot presence to the argument string.")
    async def echo(self, ctx, tag):
        """Changes the bot status in discord and adds the status to list of usable statuses"""
        settings.logger.info(f"echo from {ctx.author} : {tag}")
        if tag:
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game(tag))
            addToJson("info.json", settings.info_json, "status", tag)
            await ctx.message.delete()

    @commands.command()
    async def repeat(self, ctx, times: int, content='repeating...'):
        """Repeats a message multiple times."""
        for i in range(times):
            await ctx.send(content)

    @commands.command(brief="List the previous statuses the bot will loop through.")
    async def status(self, ctx):
        """Lists statuses the bot will cycle through."""
        settings.logger.info(f"status from {ctx.author}")

        embed_var = discord.Embed(title="Status:", description="", color=0x00ff00)
        s = ""
        for status in settings.info_json["status"]:
            if len(s) + len(status) >= 1024:
                embed_var.add_field(name="status:", value=s, inline=False)
                s = ""
            s += status + ", "
        embed_var.add_field(name="status:", value=s, inline=False)

        await ctx.channel.send(embed=embed_var)
        await ctx.message.delete()

    @tasks.loop(seconds=0, minutes=30, hours=1)
    async def change_status(self):
        """changes the bot to a randomly provided status."""
        settings.logger.info(f"status changed automatically")
        await self.client.change_presence(status=discord.Status.online, activity=discord.Game(
            settings.info_json["status"][random.randint(0, len(settings.info_json["status"]) - 1)]))


def setup(client):
    client.add_cog(general(client))
