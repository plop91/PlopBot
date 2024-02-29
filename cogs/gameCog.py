"""
Game cog for the bot
"""
import discord
import settings
from settings import add_to_json
from discord.ext import commands
import random


class Game(commands.Cog):
    """
    Game cog for the bot
    """

    def __init__(self, client):
        """
        Constructor for the game cog
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
        settings.logger.info(f"game cog ready!")

    @commands.command(pass_context=True, aliases=['add'],
                      brief="",
                      description="")
    async def add_scribble(self, ctx, tag):
        """
        Adds a scribble word to the list of words
        :arg ctx: Context of the command
        :arg tag: tag to add
        :return: None
        """
        tag = tag.strip().lower()
        add_to_json("info.json", settings.info_json, "scribble", tag)
        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['list'],
                      brief="",
                      description="")
    async def list_scribble(self, ctx):
        """
        Lists all the scribble words
        :arg ctx: Context of the command
        :return: None
        """
        embed_var = discord.Embed(title="Scribble words", description="description", color=0x00ff00)
        s = ""
        if len(settings.info_json["scribble"]) > 0:
            for scribble in settings.info_json["scribble"]:
                if len(s) + len(scribble) >= 1024:
                    embed_var.add_field(name="scribbles:", value=s, inline=False)
                    s = ""
                s += scribble + ", "
            embed_var.add_field(name="scribbles:", value=s, inline=False)
            await ctx.channel.send(embed=embed_var)
        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['TEAMS'],
                      brief="Divides the current channel into random teams. Defaults to 2.",
                      description="Divides the current channel into random teams. Defaults to 2.")
    async def teams(self, ctx, teams="2"):
        """
        Divides the current channel into random teams.
        :arg ctx: Context of the command
        :arg teams: number of teams to divide into
        :return: None
        """

        iteams = int(teams)

        # get current voice channel of author
        voice = ctx.author.voice.channel

        if voice is not None:
            # filter bots from list of members in channel
            people = list(filter(lambda x: (not x.bot), voice.members))
            settings.logger.info(f"{iteams} teams with members: ".join(m.name for m in people))

            if iteams < 2:
                iteams = 2

            if len(people) < iteams:
                settings.logger.info(f"Not enough players for {iteams} teams.")
                await ctx.send(f"Not enough players for {iteams} teams.")
            else:
                for x in range(1, iteams + 1):
                    players = random.sample(people, int(len(people) / iteams))
                    for p in players:
                        people.remove(p)
                    await ctx.send(f"Team {x}: " + ", ".join(m.name for m in players))
                    iteams -= 1
        else:
            settings.logger.info(f"Could not find voice channel of member.")
            await ctx.send("Don't think you're in a voice channel")

    @commands.command(pass_context=True, aliases=['dice'],
                      brief="Rolls a random die of specified size. Give a second number for multiple rolls.",
                      description="Rolls a random die of specified size. Give a second number for multiple rolls.")
    async def roll(self, ctx, sides, times="1"):
        """
        Rolls an equally distributed die of specified size
        :arg ctx: Context of the command
        :arg sides: number of sides on die
        :arg times: number of times to roll
        :return: None
        """
        isides = int(sides)
        itimes = int(times)
        settings.logger.info(f"roll from {ctx.author}: {isides} sides")
        if isides > 1 and itimes > 0:
            await ctx.message.channel.send(
                f"""{ctx.author} rolled {", ".join([str(x) for x in random.choices(range(1, isides + 1), 
                                                                                   k=itimes)])}""")


async def setup(client):
    """
    Adds the cog to the client
    :param client: Client object
    :return: None
    """
    await client.add_cog(Game(client))
