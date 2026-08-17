"""
This cog contains the general commands for the bot.
"""
from discord.ext import commands, tasks
import settings
import discord
import random
from cogs.adminCog import not_banned


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
        Logs that the cog was loaded properly and checks for version updates
        :return: None
        """
        settings.logger.info(f"general cog ready!")

        # Announce the running build via its codename before the hourly rotation
        # takes over, so the devs can see what is deployed on startup
        await self.set_version_codename_presence()

        self.change_status.start()

        # Check for version update and notify if changed
        await self.check_and_notify_version_update()

    async def set_version_codename_presence(self):
        """
        Sets the bot presence to the codename of the running version
        :return: None
        """
        codename = settings.get_version_codename()

        if codename == settings.UNKNOWN_VERSION_CODENAME:
            settings.logger.warning(
                f"No codename for version {settings.VERSION}, add one to VERSION_CODENAMES in settings.py")

        settings.logger.info(f"Setting startup presence to codename for version {settings.VERSION}")
        await self.client.change_presence(status=discord.Status.online, activity=discord.Game(codename))

    async def check_and_notify_version_update(self):
        """
        Checks if the bot version has changed and sends notifications to configured channels
        :return: None
        """
        try:
            current_version = settings.VERSION

            # Check if version has changed
            if not settings.version_db.check_version_changed(current_version):
                settings.logger.info(f"Version {current_version} already notified, skipping announcement")
                return

            settings.logger.info(f"New version detected: {current_version}, sending announcements")

            # Get GitHub URL from config (with fallback)
            github_url = settings.info_json.get("github_url", "https://github.com")
            disclaimer_url = f"{github_url}/blob/master/DISCLAIMER.md"

            # Build the announcement embed
            embed = discord.Embed(
                title="Bot Updated!",
                description=f"PlopBot has been updated to version **{current_version}**",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="Source Code",
                value=f"[View on GitHub]({github_url})",
                inline=False
            )
            embed.add_field(
                name="Data Usage Disclaimer",
                value=f"By using this bot, you agree to our [Data Usage Policy]({disclaimer_url}).\n\n"
                      f"**Important:** Any data you provide to this bot may be used by the server owner "
                      f"and/or the developer of this application in perpetuity and for any reason. "
                      f"Please review the full disclaimer before continuing to use this bot.",
                inline=False
            )
            embed.set_footer(text="Thank you for using PlopBot!")

            # Get announcement channels from config
            announcement_channels = settings.info_json.get("announcement_channels", [])

            if not announcement_channels:
                settings.logger.warning("No announcement channels configured, skipping version notification")
                # Still update the version so we don't spam on next restart
                settings.version_db.set_last_version(current_version)
                return

            # Send to all configured announcement channels across all guilds
            for guild in self.client.guilds:
                for channel in guild.text_channels:
                    if str(channel.name) in announcement_channels:
                        try:
                            await channel.send(embed=embed)
                            settings.logger.info(f"Sent version update notification to {guild.name}#{channel.name}")
                        except discord.Forbidden:
                            settings.logger.warning(f"No permission to send to {guild.name}#{channel.name}")
                        except discord.HTTPException as e:
                            settings.logger.error(f"Failed to send to {guild.name}#{channel.name}: {e}")

            # Update the stored version after successful notification
            settings.version_db.set_last_version(current_version)

        except Exception as e:
            settings.logger.error(f"Error during version update notification: {e}")

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        logs any incoming messages and responds to 'hey' with 'hi' to verify bot is functional.
        :arg message: message object
        :return: None
        """
        _id = message.guild
        message.content = message.content.strip().lower()
        settings.logger.info(f"Message from {message.author}: {message.content}")
        if message.author != self.client.user:
            if message.content.strip().lower() == "hey":
                await message.channel.send("Hi")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        """
        logs any deleted messages
        :arg message: message object
        :return: None
        """
        settings.logger.info(f"deleted message- {message.author} : {message.content}")

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

    @commands.command()
    @not_banned()
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
    @not_banned()
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
        settings.logger.info(f"status changed automatically")
        await self.client.change_presence(status=discord.Status.online, activity=discord.Game(
            settings.info_json["status"][random.randint(0, len(settings.info_json["status"]) - 1)]))


async def setup(client):
    """
    Adds the cog to the client
    :param client: Client object
    :return: None
    """
    await client.add_cog(General(client))
