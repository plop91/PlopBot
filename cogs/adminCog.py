"""
This cog contains the admin commands for the bot.
"""
import subprocess
import discord
from discord.ext import commands
import settings


def is_admin():
    """
    Check decorator that verifies the user is an admin.
    Checks user ID against the admins list in info.json.
    """
    async def predicate(ctx):
        # Support both user ID (int/string) and legacy username format
        admin_list = settings.info_json.get("admins", [])
        user_id = str(ctx.author.id)
        username = str(ctx.author)

        is_authorized = user_id in admin_list or ctx.author.id in admin_list or username in admin_list

        if not is_authorized:
            await ctx.channel.send("You do not have permission to run this command")
            settings.logger.warning(f"Unauthorized admin command attempt by {ctx.author} (ID: {ctx.author.id})")

        return is_authorized

    return commands.check(predicate)


def in_command_channel():
    """
    Check decorator that verifies the command is in an allowed channel.
    """
    async def predicate(ctx):
        command_channels = settings.info_json.get("command_channels", [])
        # If no command channels configured, allow all channels
        if not command_channels:
            return True

        channel_name = str(ctx.message.channel)
        if channel_name not in command_channels:
            await ctx.channel.send("This command cannot be used in this channel")
            settings.logger.warning(f"Command {ctx.command} attempted in non-command channel {channel_name}")
            return False

        return True

    return commands.check(predicate)


def not_banned():
    """
    Check decorator that verifies the user is not banned from using the bot.
    Use this decorator on commands in other cogs to enforce bans.
    """
    async def predicate(ctx):
        ban_info = settings.ban_db.is_banned(str(ctx.author.id))

        if ban_info:
            if ban_info['permanent']:
                await ctx.channel.send("You are permanently banned from using this bot.")
            else:
                expires = ban_info['expires_at'].strftime("%Y-%m-%d %H:%M:%S")
                await ctx.channel.send(f"You are banned from using this bot until {expires}.")
            settings.logger.info(f"Banned user {ctx.author} (ID: {ctx.author.id}) attempted to use command {ctx.command}")
            return False

        return True

    return commands.check(predicate)


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
    @is_admin()
    async def hash(self, ctx):
        """
        Provide current git commit hash
        :arg ctx: context of the command
        :return: None
        """
        try:
            # Get short hash (7 characters)
            short_hash = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()

            # Get full hash
            full_hash = subprocess.check_output(
                ["git", "rev-parse", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()

            # Get current branch
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                stderr=subprocess.DEVNULL
            ).decode("utf-8").strip()

            await ctx.send(f"**Branch:** {branch}\n**Commit:** `{short_hash}` (`{full_hash}`)")
            settings.logger.info(f"hash command executed by {ctx.author}")

        except subprocess.CalledProcessError:
            await ctx.send("Unable to retrieve git hash. Is this a git repository?")
            settings.logger.warning("git hash command failed - not a git repository or git not available")
        except FileNotFoundError:
            await ctx.send("Git is not installed or not in PATH")
            settings.logger.warning("git hash command failed - git not found")

    @commands.command(brief="Admin only command: provide current version")
    @is_admin()
    async def version(self, ctx):
        """
        Provide current version of the bot
        :arg ctx: context of the command
        :return: None
        """
        await ctx.send(f"**PlopBot Version:** {settings.VERSION}")
        settings.logger.info(f"version command executed by {ctx.author}")

    @commands.command(brief="Admin only command: Ban a user from using the bot")
    @is_admin()
    async def ban(self, ctx, user: discord.Member, duration: str, *, reason: str = None):
        """
        Ban a user from using the bot.
        Usage: .ban @user <duration> [reason]
        Duration: 10m, 2h, 1d, or 'x' for permanent
        :arg ctx: context of the command
        :arg user: The user to ban (mention or ID)
        :arg duration: Ban duration (e.g., 10m, 2h, 1d, x)
        :arg reason: Optional reason for the ban
        :return: None
        """
        try:
            # Parse the duration
            ban_duration = settings.parse_ban_duration(duration)

            # Add the ban
            expires_at = settings.ban_db.add_ban(
                user_id=str(user.id),
                username=str(user),
                banned_by=str(ctx.author),
                duration=ban_duration,
                reason=reason
            )

            # Build response message
            if ban_duration is None:
                duration_str = "permanently"
            else:
                duration_str = f"for {duration}"

            response = f"**{user}** has been banned from using the bot {duration_str}."
            if expires_at:
                response += f"\nExpires: {expires_at.strftime('%Y-%m-%d %H:%M:%S')}"
            if reason:
                response += f"\nReason: {reason}"

            await ctx.send(response)
            settings.logger.info(f"User {user} (ID: {user.id}) banned by {ctx.author} for {duration}. Reason: {reason}")

        except ValueError as e:
            await ctx.send(f"Invalid duration format: {e}\nUse: 10m, 2h, 1d, or 'x' for permanent")

    @commands.command(brief="Admin only command: Unban a user from the bot")
    @is_admin()
    async def unban(self, ctx, user: discord.Member):
        """
        Remove a ban from a user.
        Usage: .unban @user
        :arg ctx: context of the command
        :arg user: The user to unban (mention or ID)
        :return: None
        """
        removed = settings.ban_db.remove_ban(str(user.id))

        if removed:
            await ctx.send(f"**{user}** has been unbanned from the bot.")
            settings.logger.info(f"User {user} (ID: {user.id}) unbanned by {ctx.author}")
        else:
            await ctx.send(f"**{user}** was not banned.")

    @commands.command(brief="Admin only command: List all banned users")
    @is_admin()
    async def banlist(self, ctx):
        """
        List all currently banned users.
        :arg ctx: context of the command
        :return: None
        """
        bans = settings.ban_db.list_bans()

        if not bans:
            await ctx.send("No users are currently banned.")
            return

        # Build the ban list message
        embed = discord.Embed(title="Banned Users", color=discord.Color.red())

        for ban in bans[:25]:  # Limit to 25 to fit in embed
            if ban['permanent']:
                expires_str = "Permanent"
            else:
                expires_str = ban['expires_at'].strftime("%Y-%m-%d %H:%M:%S")

            field_value = f"**Banned by:** {ban['banned_by']}\n**Expires:** {expires_str}"
            if ban['reason']:
                field_value += f"\n**Reason:** {ban['reason']}"

            embed.add_field(
                name=f"{ban['username']} (ID: {ban['user_id']})",
                value=field_value,
                inline=False
            )

        if len(bans) > 25:
            embed.set_footer(text=f"Showing 25 of {len(bans)} bans")

        await ctx.send(embed=embed)
        settings.logger.info(f"Ban list requested by {ctx.author}")

    @commands.command(brief="Admin only command: Turn the bot off.")
    @is_admin()
    @in_command_channel()
    async def kill(self, ctx):
        """
        Performs a shutdown of the bot
        :arg ctx: context of the command
        :return: None
        """
        try:
            settings.logger.info(f"kill from {ctx.author}!")
            await ctx.send("Shutting down...")
            await self.client.close()
        except Exception:
            exit(1)

    @commands.command(brief="Admin only command: Restart the bot.")
    @is_admin()
    @in_command_channel()
    async def restart(self, ctx):
        """
        Performs a restart of the bot
        Note: This command closes the bot. The bot should be managed by a process manager
        (like systemd or docker) that will automatically restart it.
        :arg ctx: context of the command
        :return: None
        """
        try:
            settings.logger.info(f"restart from {ctx.author}!")
            await ctx.send("Restarting bot... (requires process manager)")
            await self.client.close()
        except Exception:
            exit(1)


async def setup(client):
    """
    Adds the cog to the bot
    :arg client: client object
    :return: None
    """
    await client.add_cog(Admin(client))
