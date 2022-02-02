from discord.ext import commands
import settings
import discord
import requests


class glide(commands.Cog):
    url = "http://192.168.1.19:8000/webhook/"
    generating = 0

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
        webhook = None
        webhooks = ctx.channel.webhooks()
        for hook in webhooks:
            if hook.name == 'glide':
                webhook = hook
        if webhook is None:
            webhook = await ctx.channel.create_webhook(name='glide')
        webhook = webhook.url
        await ctx.channel.send("generating image")
        _json = {"un": "ian", "pw": "plop", "prompt": prompt, "messageid": ctx.message.id, "webhook": webhook}
        response = requests.post(self.url, json=_json)
        with open("gen.jpg", "wb") as f:
            f.write(response.content)
        await ctx.channel.send(file=discord.File("gen.jpg"))


def setup(client):
    client.add_cog(glide(client))
