"""
This cog is for generating images and text using openai
"""
import discord
import settings
from settings import add_to_json
from discord.ext import commands
import openai
import wget
import os
from PIL import Image


class openAI(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.api_key = settings.info_json["openai"]["apikey"]
        openai.api_key = self.api_key

    @commands.Cog.listener()
    async def on_ready(self):
        """Logs that the cog was loaded properly"""
        settings.logger.info(f"openai cog ready!")

    @commands.command(pass_context=True, aliases=["genimg", "genimage", "gen_image"],
                      brief="generate an image from a prompt using openai")
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

    @commands.command(pass_context=True, aliases=["editimg", "editimage", "edit_image"],
                      brief="edit an image from a prompt using openai")
    async def edit_img(self, ctx, *args):
        """
        Edit an image from a prompt using openai
        :param ctx: Context
        :param args: Arguments
        """
        if ctx.message.attachments[0] is None:
            await ctx.send("No image attached")
            return
        # elif not ctx.message.attachments[0].filename.endswith('.png'):
        #     await ctx.send("Image must be png format")
        #     return
        await ctx.message.attachments[0].save("temp.png")

        png = Image.open("temp.png")
        png.load()  # required for png.split()
        png = png.convert("RGBA")
        png = png.resize((1024, 1024))
        png.save("temp.png", 'png', quality=100)

        # mask = Image.new("RGBA", png.size, (255, 255, 255, 0))
        # mask.putalpha(0)
        # mask.save("mask.png", 'png', quality=100)

        prompt = ' '.join(args)
        settings.logger.info(f"editing image")
        # response = openai.Image.create_edit(
        #     image=open("temp.png", "rb"),
        #     mask=open("mask.png", "rb"),
        #     prompt=prompt,
        #     n=1,
        #     size="1024x1024"
        # )
        response = openai.Image.create_variation(
            image=open("temp.png", "rb"),
            n=1,
            size="1024x1024"
        )
        os.remove("temp.png")
        # os.remove("mask.png")
        image_url = response['data'][0]['url']
        image_filename = wget.download(image_url)
        await ctx.send(file=discord.File(image_filename))
        os.remove(image_filename)





    @commands.command(pass_context=True, aliases=["gentext", "gentxt", "gen_txt", "text"],
                      brief="generate text from a prompt using openai")
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
