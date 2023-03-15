import discord
import settings
from settings import add_to_json
from discord.ext import commands
import openai
import wget
import os


class openAI(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.api_key = settings.info_json["openai"]["apikey"]
        openai.api_key = self.api_key

    @commands.Cog.listener()
    async def on_ready(self):
        """Logs that the cog was loaded properly"""
        settings.logger.info(f"openai cog ready!")

    @commands.command(pass_context=True, brief="generate an image from a prompt using openai")
    async def gen_img(self, ctx, *args):
        """
        Generate an image from a prompt using openai
        :param ctx: Context
        :param args: Arguments
        """
        prompt = ' '.join(args)
        settings.logger.info(f"generating image")
        response = openai.Image.create(
            prompt=prompt,
            n=1,
            size="1024x1024"
        )
        image_url = response['data'][0]['url']
        image_filename = wget.download(image_url)
        await ctx.send(file=discord.File(image_filename))
        os.remove(image_filename)

    @commands.command(pass_context=True, brief="generate text from a prompt using openai")
    async def gen_text(self, ctx, *args):
        """
        Generate text from a prompt using openai
        :param ctx: Context
        :param args: Arguments
        """
        prompt = ' '.join(args)
        settings.logger.info(f"generating text")
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0,
            max_tokens=150,
        )
        await ctx.send(response['choices'][0]['text'])


async def setup(client):
    await client.add_cog(openAI(client))
