"""
This cog contains the general commands for the bot.
"""
from discord.ext import commands, tasks
from settings import add_to_json
import settings
import discord
import random


class General(commands.Cog):
    """
    General cog for the bot
    """

    def __init__(self, client):
        """
        Constructor for the general cog
        :arg client: Client object
        :return: None
        """
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Logs that the cog was loaded properly
        :return: None
        """
        settings.logger.info(f"general cog ready!")
        self.change_status.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        Responds to 'hey' with 'hi' to verify bot is functional.
        Only logs command messages to respect user privacy.
        :arg message: message object
        :return: None
        """
        _id = message.guild
        # Only log if it's a command (starts with prefix) or from the bot itself
        # This reduces privacy concerns and log file size
        if message.content.startswith(tuple(settings.info_json.get("command_prefixes", ["!"]))):
            settings.logger.info(f"Command from {message.author}: {message.content}")

        if message.author != self.client.user:
            if message.content.strip().lower() == "hey":
                await message.channel.send("Hi")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """
        Logs metadata of deleted messages without content to respect user privacy
        :arg message: message object
        :return: None
        """
        # Only log metadata, not content, to respect user privacy and GDPR
        settings.logger.info(
            f"deleted message- {message.author} in #{message.channel} "
            f"at {message.created_at} (length: {len(message.content)} chars)"
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """
        Greets new members to the server with a random welcome message
        :arg member: member object
        :return: None
        """
        settings.logger.info(f"member joined- {member}")
        for channel in member.guild.channels:
            if str(channel) in settings.info_json["welcome_channels"]:
                await channel.send(f"""{random.choice(settings.info_json["welcome_messages"])} {member.mention}?""")

    @commands.command(brief="Change the bot presence to the argument string.")
    async def echo(self, ctx, tag):
        """
        Changes the bot status in discord and adds the status to list of usable statuses
        :arg ctx: Context of the command
        :arg tag: tag to add
        :return: None
        """
        settings.logger.info(f"echo from {ctx.author} : {tag}")
        if tag:
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game(tag))
            add_to_json("info.json", settings.info_json, "status", tag)
            await ctx.message.delete()

    @commands.command()
    async def repeat(self, ctx, times: int, content='repeating...'):
        """
        Repeats a message multiple times.
        :arg ctx: Context of the command
        :arg times: number of times to repeat
        :arg content: content to repeat
        :return: None
        """
        MAX_REPEATS = 10
        if times > MAX_REPEATS:
            await ctx.send(f"Max {MAX_REPEATS} repeats allowed")
            return
        for i in range(times):
            await ctx.send(content)

    @commands.command(brief="List the previous statuses the bot will loop through.")
    async def status(self, ctx):
        """
        Lists statuses the bot will cycle through.
        :arg ctx: Context of the command
        :return: None
        """
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

    @tasks.loop(hours=1)
    async def change_status(self):
        """
        changes the bot to a randomly provided status.
        :return: None
        """
        statuses = settings.info_json.get("status", [])
        if not statuses:
            settings.logger.warning("No status messages configured, skipping status change")
            return

        settings.logger.info(f"status changed automatically")
        # Use random.choice instead of randint for cleaner code
        status = random.choice(statuses)
        await self.client.change_presence(status=discord.Status.online, activity=discord.Game(status))


async def setup(client):
    """
    Adds the cog to the client
    :param client: Client object
    :return: None
    """
    await client.add_cog(General(client))
