import discord
import settings
from utility.tools import addToJson
from discord.ext import commands


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
        addToJson("info.json", settings.json, "scribble", tag)
        await ctx.message.delete()

    @commands.command(pass_context=True, aliases=['list'],
                      brief="",
                      description="")
    async def list_scribble(self, ctx):
        embed_var = discord.Embed(title="Scribble words", description="description", color=0x00ff00)
        s = ""
        if len(settings.json["scribble"]) > 0:
            for scribble in settings.json["scribble"]:
                if len(s) + len(scribble) >= 1024:
                    embed_var.add_field(name="scribbles:", value=s, inline=False)
                    s = ""
                s += scribble + ", "
            embed_var.add_field(name="scribbles:", value=s, inline=False)
            await ctx.channel.send(embed=embed_var)
        await ctx.message.delete()


def setup(client):
    client.add_cog(game(client))
