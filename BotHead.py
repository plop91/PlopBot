#!/usr/bin/env python3
"""
PlopBot is a discord bot that can play sounds and has some additional features.
This is the main file for the bot.
"""
import asyncio
import os
import traceback
import discord
from discord.ext import commands
import argparse
import settings


class PlopBot(commands.Bot):
    """
    The main bot class.
    """
    def __init__(self, *args, **kwargs):
        """
        Constructor for the bot.
        :arg args:
        :arg kwargs:
        :return: None
        """
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        """
        Setup hook for the bot, loads all cogs.

        A cog that fails to load is skipped rather than taking the whole bot down with it;
        an optional feature missing its configuration should cost you that feature, not the
        soundboard. Failures are logged loudly and summarised once loading finishes.
        :return: None
        """
        loaded, failed = [], []

        for f in sorted(os.listdir('./cogs')):
            if not f.endswith('.py'):
                continue

            extension = f'cogs.{f[:-3]}'
            try:
                await self.load_extension(extension)
                loaded.append(extension)
            except Exception as e:
                failed.append(extension)
                # The cause is more useful than the ExtensionFailed wrapper
                cause = e.__cause__ or e
                settings.logger.error(f"Could not load {extension}, continuing without it: "
                                      f"{type(cause).__name__}: {cause}")
                settings.logger.debug(traceback.format_exc())

        settings.logger.info(f"Loaded {len(loaded)} cogs: {', '.join(c.split('.')[-1] for c in loaded)}")
        if failed:
            settings.logger.warning(f"{len(failed)} cog(s) unavailable: "
                                    f"{', '.join(c.split('.')[-1] for c in failed)}")

    async def on_command_error(self, ctx, error) -> None:
        """
        Reports command failures to the user rather than failing silently.

        Without this, every cooldown, missing argument, permission problem and unhandled
        exception is invisible to whoever ran the command.
        :arg ctx: context of the command
        :arg error: the exception that was raised
        :return: None
        """
        try:
            if isinstance(error, commands.CommandNotFound):
                return

            if isinstance(error, commands.NoPrivateMessage):
                await ctx.send("That command only works in a server.")
                return

            # The check decorators (is_admin, not_banned, in_command_channel) already
            # explain themselves to the user, so do not talk over them
            if isinstance(error, commands.CheckFailure):
                return

            if isinstance(error, commands.CommandOnCooldown):
                await ctx.send(f"That command is on cooldown, try again in {error.retry_after:.0f}s.")
                return

            if isinstance(error, commands.UserInputError):
                await ctx.send(f"{error} Try `.help {ctx.command}`.")
                return

            # Unwrap the exception raised inside the command body
            original = getattr(error, 'original', error)

            if isinstance(original, settings.DatabaseUnavailableError):
                settings.logger.error(f"{ctx.command} failed, database unavailable: {original}")
                await ctx.send("The bot's database is unreachable, try again shortly.")
                return

            if isinstance(original, discord.Forbidden):
                settings.logger.warning(f"{ctx.command} lacked a Discord permission: {original}")
                return

            settings.logger.error(
                f"Unhandled error in {ctx.command} from {ctx.author}: "
                f"{''.join(traceback.format_exception(type(original), original, original.__traceback__))}")
            await ctx.send("Something went wrong running that command.")

        except discord.HTTPException:
            # Never let the error handler raise on its own
            settings.logger.warning(f"Could not report an error for {ctx.command}: {traceback.format_exc()}")

    # @commands.command(brief="Admin only command: Load a Cog.")
    # async def load(self, ctx, extension):
    #     """Loads a new cog into the bot while running"""
    #     settings.logger.info(f"load: {extension} :: from {ctx.author}")
    #     if ctx.author not in settings.info_json["admins"]:
    #         settings.logger.warning(f"User: {ctx.author} is not an admin but tried to load a cog!")
    #     elif str(ctx.message.channel) not in settings.info_json["command_channels"]:
    #         settings.logger.info(f"User: {ctx.author} is an admin but tried to load in a non command channel!")
    #     else:
    #         await self.load_extension(f'cogs.{extension}Cog')
    #         settings.logger.info(f"cog:{extension} loaded")
    #         await ctx.message.delete()
    #
    # @commands.command(brief="Admin only command: Unload a Cog.")
    # async def unload(self, ctx, extension):
    #     """Unloads an active cog from the bot"""
    #     settings.logger.info(f"unload: {extension} :: from {ctx.author}")
    #     if ctx.author not in settings.info_json["admins"]:
    #         settings.logger.warning(f"User: {ctx.author} is not an admin but tried to unload a cog!")
    #     elif str(ctx.message.channel) not in settings.info_json["command_channels"]:
    #         settings.logger.info(f"User: {ctx.author} is an admin but tried to unload in a non command channel!")
    #     else:
    #         await self.unload_extension(f'cogs.{extension}Cog')
    #         settings.logger.info(f"cog:{extension} unloaded")
    #     await ctx.message.delete()
    #
    # @commands.command(brief="Admin only command: Reload a Cog.")
    # async def reload(self, ctx, extension):
    #     """Unloads then reloads a cog"""
    #     settings.logger.info(f"reload: {extension} :: from {ctx.author}")
    #     if ctx.author not in settings.info_json["admins"]:
    #         settings.logger.warning(f"User: {ctx.author} is not an admin but tried to reload a cog!")
    #     elif str(ctx.message.channel) not in settings.info_json["command_channels"]:
    #         settings.logger.info(f"User: {ctx.author} is an admin but tried to reload in a non command channel!")
    #     else:
    #         await self.reload_extension(f'cogs.{extension}Cog')
    #         settings.logger.info(f"reload from {ctx.author}")
    #     await ctx.message.delete()
    #
    # @commands.event
    # async def on_ready(self):
    #     """Logs that the cog was loaded properly"""
    #     settings.logger.info(f"Logged on as {self.user}!")
    #     # await load_cogs()
    #     await self.change_presence(status=discord.Status.online, activity=discord.Game('listening'))
    #
    # @commands.event
    # async def on_disconnect(self):
    #     """Logs the bot turning off"""
    #     settings.logger.info(f"Logged off!")
    #     await self.change_presence(status=discord.Status.offline, activity=discord.Game('sleeping'))


async def main(args):
    """
    Main entry point for the bot.
    :arg args: arguments from argparse
    :return: None
    """
    settings.init(args)

    async with PlopBot(command_prefix='.', intents=discord.Intents.all()) as bot:
        await bot.start(settings.token)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog='Discord Bot',
                                     description='a discord bot with a soundboard and some additional features.')

    parser.add_argument('--json', help='Path to json file', default='info/info.json')
    parser.add_argument('--db_host', help='Database hostname or ip by default taken from json file', default=None)
    parser.add_argument('--db_username', help='Database username by default taken from json file', default=None)
    parser.add_argument('--db_password', help='Database password by default taken from json file', default=None)
    parser.add_argument('--db_name', help='Database name by default taken from json file', default=None)

    arguments = parser.parse_args()

    # Initialize settings to connect to database, open json and setup logging

    asyncio.run(main(arguments))
