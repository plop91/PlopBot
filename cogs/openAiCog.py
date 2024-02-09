"""
This cog is for generating images and text using openai
"""
import discord
import settings
from discord.ext import commands
import openai
import wget
import os
from PIL import Image

# import mysql.connector
# from mysql.connector import errorcode
#
# class OpenAIDatabaseManager:
#     """
#     This class is for managing the openai database
#     """
#
#     def __init__(self):
#         """
#         Constructor for the openai database manager
#         :param client: Client object
#         """


blacklist = []


def blackisted(user):
    return str(user).strip().lower() in blacklist


class OpenAI(commands.Cog):
    """
    This cog is for generating images and text using openai
    """

    def __init__(self, client):
        """
        Constructor for the openai cog
        :param client: Client object
        """
        self.client = client
        self.api_key = settings.info_json["openai"]["apikey"]
        openai.api_key = self.api_key

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Logs that the cog was loaded properly
        :return: None
        """
        settings.logger.info(f"openai cog ready!")

    @commands.command(pass_context=True, aliases=["genimg", "genimage", "gen_image"],
                      brief="generate an image from a prompt using openai")
    async def gen_img(self, ctx, *args):
        """
        Generate an image from a prompt using openai
        :arg ctx: Context of the command
        :arg args: Arguments
        :return: None
        """

        if not blackisted(ctx.author):
            prompt = ' '.join(args)
            settings.logger.info(f"generating image")
            response = openai.Image.create(
                model="dall-e-3",
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response['data'][0]['url']
            image_filename = wget.download(image_url)
            await ctx.send(file=discord.File(image_filename))
            os.remove(image_filename)
        else:
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")

    @commands.command(pass_context=True, aliases=["editimg", "editimage", "edit_image"],
                      brief="edit an image from a prompt using openai")
    async def edit_img(self, ctx, *args):
        """
        Edit an image from a prompt using openai
        :arg ctx: Context
        :arg args: Arguments
        :return: None
        """

        if not blackisted(ctx.author):
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
        else:
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")

    @commands.command(pass_context=True, aliases=["gentext", "gentxt", "gen_txt", "text"],
                      brief="generate text from a prompt using openai")
    async def gen_text(self, ctx, *args):
        """
        Generate text from a prompt using openai
        :arg ctx: Context
        :arg args: Arguments
        :return: None
        """

        if not blackisted(ctx.author):
            prompt = ' '.join(args)
            settings.logger.info(f"generating text")
            if settings.info_json["openai"]["text_gen_engine"] is None:
                engine = "text-davinci-003"
            else:
                engine = settings.info_json["openai"]["text_gen_engine"]
            response = openai.Completion.create(
                engine=engine,
                prompt=prompt,
                temperature=0,
                max_tokens=150,
            )
            await ctx.send(response['choices'][0]['text'])
        else:
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")

    @commands.command(pass_context=True, aliases=["openai_ban_user", "openai_banuser"],
                      brief="Ban a user from using the openai cog")
    async def openai_ban(self, ctx, *user):
        """
        Bans a user from using the openai cog
        :param ctx: Context
        :param user: User to ban
        :return: None
        """
        if ctx.author in settings.info_json["admins"]:
            blacklist.append(str(user).strip().lower())
            await ctx.send(f"{user} has been banned from using the openai cog")
        else:
            await ctx.send(f"{user} is not an admin and cannot be banned from using the openai cog")

    @commands.command(pass_context=True, aliases=["openai_unban_user", "openai_unbanuser"],
                      brief="Unban a user from using the openai cog")
    async def openai_unban(self, ctx, *user):
        """
        Unbans a user from using the openai cog
        :param ctx: Context
        :param user: User to unban
        :return: None
        """
        if ctx.author in settings.info_json["admins"]:
            blacklist.remove(str(user).strip().lower())
            await ctx.send(f"{user} has been unbanned from using the openai cog")
        else:
            await ctx.send(f"{user} is not an admin and cannot be unbanned from using the openai cog")


async def setup(client):
    """
    Sets up the cog
    :param client: Client object
    :return: None
    """
    await client.add_cog(OpenAI(client))
