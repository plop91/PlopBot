import discord
import settings
from settings import add_to_json
from discord.ext import commands
import random


class game(commands.Cog):

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        settings.logger.info(f"game cog ready!")

    @commands.command(pass_context=True, aliases=['add'],
                      brief="",
                      description="")
    async def add_scribble(self, ctx, tag):
        tag = tag.strip().lower()
        add_to_json("info.json", settings.info_json, "scribble", tag)
        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['list'],
                      brief="",
                      description="")
    async def list_scribble(self, ctx):
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
                      brief="Divides the current channel into two random teams.",
                      description="Divides the current channel into two random teams.")
    async def teams(self, ctx):
        """Divides the current channel into two random teams."""

        # get current voice channel of author
        voice = ctx.author.voice.channel
        
        if voice is not None:
            # filter bots from list of members in channel
            people = list(filter(lambda x: (not x.bot), voice.members))
            settings.logger.info(f"Teams with members: ".join(m.name for m in people))
            
            team2 = random.sample(people, int(len(people)/2))
            for x in team2:
                people.remove(x)
            team1 = people
            
            await ctx.send("Team 1: "+", ".join(m.name for m in team1))
            await ctx.send("Team 2: "+", ".join(m.name for m in team2))
        else:
            settings.logger.info(f"Could not find voice channel of member.")
            await ctx.send("Don't think you're in a voice channel")

        await ctx.message.delete()


async def setup(client):
    await client.add_cog(game(client))
