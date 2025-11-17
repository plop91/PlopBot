"""
This cog contains the admin commands for the bot.
"""
from discord.ext import commands
import settings
import subprocess


class Admin(commands.Cog):
    """
    Admin cog for the bot
    """

    def __init__(self, client):
        """
        Constructor for the admin cog
        :arg client: client object
        """
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Logs that the cog was loaded properly
        :return: None
        """
        settings.logger.info(f"admin cog ready!")

    @commands.command(brief="Admin only command: provide current git commit hash")
    async def hash(self, ctx):
        """
        provide current git commit hash
        :arg ctx: context of the command
        :return: None
        """
        if str(ctx.author) in settings.info_json["admins"]:
            try:
                # Get the current git commit hash
                result = subprocess.run(
                    ['git', 'rev-parse', '--short', 'HEAD'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    commit_hash = result.stdout.strip()
                    await ctx.send(f"Current commit hash: `{commit_hash}`")
                else:
                    await ctx.send("Failed to get git commit hash")
            except subprocess.TimeoutExpired:
                await ctx.send("Git command timed out")
            except Exception as e:
                settings.logger.error(f"Error getting git hash: {e}")
                await ctx.send("Error retrieving git commit hash")
        else:
            await ctx.send("You do not have permission to run this command")
            settings.logger.warning(f"Unauthorized hash command attempt by {ctx.author}")

    @commands.command(brief="Admin only command: provide current version")
    async def version(self, ctx):
        """
        provide current version of the bot
        :arg ctx: context of the command
        :return: None
        """
        if str(ctx.author) in settings.info_json["admins"]:
            try:
                # Try to get version from git tag
                result = subprocess.run(
                    ['git', 'describe', '--tags', '--always'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    version = result.stdout.strip()
                    await ctx.send(f"Bot version: `{version}`")
                else:
                    await ctx.send("Version information not available")
            except subprocess.TimeoutExpired:
                await ctx.send("Git command timed out")
            except Exception as e:
                settings.logger.error(f"Error getting version: {e}")
                await ctx.send("Error retrieving version information")
        else:
            await ctx.send("You do not have permission to run this command")
            settings.logger.warning(f"Unauthorized version command attempt by {ctx.author}")

    @commands.command(brief="Admin only command: Turn the bot off.")
    async def kill(self, ctx):
        """
        Preforms a shutdown of the bot
        :arg ctx: context of the command
        :return: None
        """
        # try to gracefully shut down the bot
        # noinspection PyBroadException
        try:
            if str(ctx.author) in settings.info_json["admins"]:
                settings.logger.info(f"kill from {ctx.author}!")
                if str(ctx.message.channel) in settings.info_json["command_channels"]:
                    await self.client.close()
            else:
                await ctx.channel.send("You do not have permission to run this command")
                settings.logger.warning(f"Unauthorized kill attempt by {ctx.author}")
        # if the bot fails to close kill it
        except Exception:
            exit(1)

    @commands.command(brief="Admin only command: Restart the bot.")
    async def restart(self, ctx):
        """
        Preforms a restart of the bot
        Note: This command closes the bot. The bot should be managed by a process manager
        (like systemd or docker) that will automatically restart it.
        :arg ctx: context of the command
        :return: None
        """
        # try to gracefully shut down the bot
        # noinspection PyBroadException
        try:
            if str(ctx.author) in settings.info_json["admins"]:
                settings.logger.info(f"restart from {ctx.author}!")
                if str(ctx.message.channel) in settings.info_json["command_channels"]:
                    await ctx.send("Restarting bot... (requires process manager)")
                    await self.client.close()
            else:
                await ctx.channel.send("You do not have permission to run this command")
                settings.logger.warning(f"Unauthorized restart attempt by {ctx.author}")
        # if the bot fails to close kill it
        except Exception:
            exit(1)


async def setup(client):
    """
    Adds the cog to the bot
    :arg client: client object
    :return: None
    """
    await client.add_cog(Admin(client))
