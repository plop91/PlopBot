from discord.ext import commands
import settings
import discord
import requests


class glide(commands.Cog):
    url = "http://192.168.1.19:8000/image/"

    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        """Logs that the cog was loaded properly"""
        settings.logger.info(f"glide cog ready!")

    @commands.command(brief="generate an image")
    async def gen_image(self, ctx, prompt):
        """"""
        settings.logger.info(f"gen image from {ctx.author} : {prompt}")
        await ctx.channel.send("generating image")
        myobj = {"un": "ian", "pw": "plop", "prompt": prompt}
        response = requests.post(self.url, json=myobj)
        with open("gen.png", "wb") as f:
            f.write(response.content)
        await ctx.channel.send(file=discord.File("gen.png"))


def setup(client):
    client.add_cog(glide(client))
