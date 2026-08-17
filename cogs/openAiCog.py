"""
This cog is for generating images and chatting with assistants using openai.

Assistants are personalities stored in our own database; the instructions are
sent with every request and the conversation history is kept by OpenAI via the
Conversations API. The Assistants API this used to be built on is removed on
2026-08-26.
"""
import discord
import settings
from discord.ext import commands
from openai import AsyncOpenAI, BadRequestError, NotFoundError, OpenAIError
import wget
import os
import json
from PIL import Image

from cogs.adminCog import not_banned, is_admin

BLACKLIST_FILE = "openai_blacklist.json"

# Model used for chat. Override with openai.text_gen_engine in info.json.
DEFAULT_CHAT_MODEL = "gpt-5.6-luna"

# Discord rejects messages over 2000 characters, leave room for formatting
MAX_MESSAGE_LENGTH = 1900


def load_blacklist():
    """Load blacklist from file"""
    try:
        if os.path.exists(BLACKLIST_FILE):
            with open(BLACKLIST_FILE, 'r') as f:
                return json.load(f)
        return []
    except Exception as e:
        settings.logger.error(f"Error loading blacklist: {e}")
        return []


def save_blacklist(blacklist_data):
    """Save blacklist to file"""
    try:
        with open(BLACKLIST_FILE, 'w') as f:
            json.dump(blacklist_data, f, indent=4)
    except Exception as e:
        settings.logger.error(f"Error saving blacklist: {e}")


blacklist = load_blacklist()


def blacklisted(user):
    """
    Checks if a user is blacklisted
    :param user: user to check
    :return: True if blacklisted, False otherwise
    """
    return str(user).strip().lower() in blacklist


def chunk_message(text, limit=MAX_MESSAGE_LENGTH):
    """
    Splits text into Discord sized pieces, breaking on line boundaries where possible
    :param text: text to split
    :param limit: maximum size of each piece
    :return: list of strings
    """
    if not text:
        return []

    chunks = []
    current = ""

    for line in text.split("\n"):
        # A single line too long to send has to be hard split
        while len(line) > limit:
            if current:
                chunks.append(current)
                current = ""
            chunks.append(line[:limit])
            line = line[limit:]

        if len(current) + len(line) + 1 > limit:
            chunks.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line

    if current:
        chunks.append(current)

    return chunks


class OpenAI(commands.Cog):
    """
    This cog is for generating images and chatting with assistants using openai
    """

    def __init__(self, client):
        """
        Constructor for the openai cog
        :param client: Client object
        """
        self.client = client

        openai_config = settings.info_json.get("openai", {})
        self.api_key = openai_config.get("apikey")
        if not self.api_key:
            raise RuntimeError("no openai.apikey in the config file, the openai commands are unavailable")

        self.openai_client = AsyncOpenAI(api_key=self.api_key)
        self.model = openai_config.get("text_gen_engine", DEFAULT_CHAT_MODEL)

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Logs that the cog was loaded properly
        :return: None
        """
        settings.logger.info(f"openai cog ready! chat model: {self.model}")

    async def send_chunked(self, ctx, text):
        """
        Sends a possibly long message as several Discord messages
        :param ctx: Context
        :param text: text to send
        :return: None
        """
        for chunk in chunk_message(text):
            await ctx.send(chunk)

    async def start_conversation(self, guild_id, name):
        """
        Creates a new OpenAI conversation and stores it against the assistant
        :param guild_id: Guild the assistant belongs to
        :param name: Name of the assistant
        :return: The new conversation id
        """
        conversation = await self.openai_client.conversations.create()
        settings.assistant_db.set_conversation_id(guild_id, name, conversation.id)
        settings.logger.info(f"Started conversation {conversation.id} for assistant '{name}' in guild {guild_id}")
        return conversation.id

    async def end_conversation(self, conversation_id):
        """
        Deletes a conversation on OpenAI, ignoring one that is already gone
        :param conversation_id: Conversation to delete
        :return: None
        """
        if not conversation_id:
            return

        try:
            await self.openai_client.conversations.delete(conversation_id)
        except NotFoundError:
            pass
        except OpenAIError as e:
            settings.logger.warning(f"Could not delete conversation {conversation_id}: {e}")

    @commands.command(pass_context=True, aliases=["genimg", "genimage", "gen_image"],
                      brief="generate an image from a prompt using openai")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @not_banned()
    async def gen_img(self, ctx, *args):
        """
        Generate an image from a prompt using openai
        :arg ctx: Context of the command
        :arg args: Arguments
        :return: None
        """

        if not blacklisted(ctx.author):
            prompt = ' '.join(args)
            settings.logger.info(f"generating image")
            try:
                response = await self.openai_client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1
                )
                image_url = response.data[0].url
                image_filename = wget.download(image_url)
                await ctx.send(file=discord.File(image_filename))
                os.remove(image_filename)
            except BadRequestError as e:
                if e.code == "content_policy_violation":
                    await ctx.send("Your prompt was rejected by OpenAI's safety system due to content policy violation")
                    return
                raise e
        else:
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")

    @commands.command(pass_context=True, aliases=["editimg", "editimage", "edit_image"],
                      brief="edit an image from a prompt using openai")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @not_banned()
    async def edit_img(self, ctx, *args):
        """
        Edit an image from a prompt using openai
        :arg ctx: Context
        :return: None
        """

        if not blacklisted(ctx.author):
            if not ctx.message.attachments:
                await ctx.send("No image attached")
                return
            if ctx.message.attachments[0] is None:
                await ctx.send("No image attached")
                return
            await ctx.message.attachments[0].save("temp.png")

            png = Image.open("temp.png")
            png.load()  # required for png.split()
            png = png.convert("RGBA")
            png = png.resize((1024, 1024))
            png.save("temp.png", 'png', quality=100)
            settings.logger.info(f"editing image")
            with open("temp.png", "rb") as image_file:
                response = await self.openai_client.images.create_variation(
                    image=image_file,
                    n=1,
                    size="1024x1024"
                )
            os.remove("temp.png")
            image_url = response.data[0].url
            image_filename = wget.download(image_url)
            await ctx.send(file=discord.File(image_filename))
            os.remove(image_filename)
        else:
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")

    @commands.command(pass_context=True, aliases=["la", "listassistants"],
                      brief="Prints the list of existing assistants")
    @commands.guild_only()
    @not_banned()
    async def list_assistants(self, ctx):
        """
        Prints the list of existing assistants
        :arg ctx: Context
        :return: None
        """
        if blacklisted(ctx.author):
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")
            return

        names = settings.assistant_db.list_assistants(ctx.guild.id)

        if not names:
            await ctx.send("No assistants yet, create one with '.cra <name> <personality>'")
            return

        await ctx.send("Current assistants: " + ", ".join(names))

    @commands.command(pass_context=True, aliases=["cra", "createassistant"],
                      brief="Create an assistant with the given personality")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.guild_only()
    @not_banned()
    async def create_assistant(self, ctx, name, *, instructions=None):
        """
        Create an assistant with the given personality
        :arg ctx: Context
        :arg name: Name of the assistant
        :arg instructions: The personality, sent as instructions on every message
        :return: None
        """
        if blacklisted(ctx.author):
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")
            return

        if not instructions:
            await ctx.send("Give the assistant a personality: '.cra <name> <personality>'")
            return

        created = settings.assistant_db.add_assistant(
            guild_id=ctx.guild.id,
            name=name,
            instructions=instructions,
            created_by=str(ctx.author)
        )

        if not created:
            await ctx.send(f"Assistant {name} already exists")
            return

        await ctx.send(f"Assistant {name} created. Talk to it with '.ca {name} <message>'")

    @commands.command(pass_context=True, aliases=["ca", "chatassistant"],
                      brief="chat with an assistant using openai")
    @commands.cooldown(1, 60, commands.BucketType.user)
    @commands.guild_only()
    @not_banned()
    async def chat_assistant(self, ctx, name, *, message=None):
        """
        Chat with an assistant using openai
        :arg ctx: Context
        :arg name: Name of the assistant
        :arg message: What to say to the assistant
        :return: None
        """
        if blacklisted(ctx.author):
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")
            return

        if not message:
            await ctx.send(f"Say something to the assistant: '.ca {name} <message>'")
            return

        assistant = settings.assistant_db.get_assistant(ctx.guild.id, name)
        if not assistant:
            await ctx.send(f"Assistant {name} does not exist")
            return

        async with ctx.typing():
            conversation_id = assistant['conversation_id']
            if not conversation_id:
                conversation_id = await self.start_conversation(ctx.guild.id, name)

            try:
                try:
                    response = await self.openai_client.responses.create(
                        model=self.model,
                        instructions=assistant['instructions'],
                        input=message,
                        conversation=conversation_id
                    )
                except NotFoundError:
                    # The conversation is gone on OpenAI's side, start a fresh one
                    settings.logger.info(f"Conversation {conversation_id} missing, starting a new one")
                    conversation_id = await self.start_conversation(ctx.guild.id, name)
                    response = await self.openai_client.responses.create(
                        model=self.model,
                        instructions=assistant['instructions'],
                        input=message,
                        conversation=conversation_id
                    )
            except OpenAIError as e:
                settings.logger.error(f"Assistant '{name}' failed: {e}")
                await ctx.send(f"{name} could not answer, check the bot logs.")
                return

        reply = response.output_text
        if not reply:
            await ctx.send(f"{name} had nothing to say.")
            return

        await self.send_chunked(ctx, f"{name} says: {reply}")

    @commands.command(pass_context=True, aliases=["forget", "resetassistant"],
                      brief="Clear an assistant's memory of the conversation so far")
    @commands.guild_only()
    @not_banned()
    async def reset_assistant(self, ctx, name):
        """
        Clears the conversation history of an assistant, keeping its personality
        :arg ctx: Context
        :arg name: Name of the assistant
        :return: None
        """
        if blacklisted(ctx.author):
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")
            return

        assistant = settings.assistant_db.get_assistant(ctx.guild.id, name)
        if not assistant:
            await ctx.send(f"Assistant {name} does not exist")
            return

        await self.end_conversation(assistant['conversation_id'])
        settings.assistant_db.set_conversation_id(ctx.guild.id, name, None)

        settings.logger.info(f"{ctx.author} reset the conversation for assistant '{name}'")
        await ctx.send(f"{name} has forgotten the conversation so far.")

    @commands.command(pass_context=True, aliases=["dela", "deleteassistant"],
                      brief="Admin only command: Delete an assistant")
    @commands.guild_only()
    @is_admin()
    async def delete_assistant(self, ctx, name):
        """
        Deletes an assistant and the conversation attached to it
        :arg ctx: Context
        :arg name: Name of the assistant
        :return: None
        """
        assistant = settings.assistant_db.get_assistant(ctx.guild.id, name)
        if not assistant:
            await ctx.send(f"Assistant {name} does not exist")
            return

        await self.end_conversation(assistant['conversation_id'])
        settings.assistant_db.remove_assistant(ctx.guild.id, name)

        settings.logger.info(f"Assistant '{name}' deleted by {ctx.author}")
        await ctx.send(f"Assistant {name} deleted.")

    @commands.command(pass_context=True, aliases=["openai_ban_user", "openai_banuser", "obu"],
                      brief="Ban a user from using the openai cog")
    async def openai_ban(self, ctx, *user):
        """
        Bans a user from using the openai cog
        :param ctx: Context
        :param user: User to ban
        :return: None
        """
        if ctx.author in settings.info_json["admins"]:
            user_str = str(user).strip().lower()
            if user_str not in blacklist:
                blacklist.append(user_str)
                save_blacklist(blacklist)
                await ctx.send(f"{user} has been banned from using the openai cog")
            else:
                await ctx.send(f"{user} is already banned")
        else:
            await ctx.send(f"{ctx.author} is not an admin and cannot ban someone from using the openai cog")

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
            user_str = str(user).strip().lower()
            if user_str in blacklist:
                blacklist.remove(user_str)
                save_blacklist(blacklist)
                await ctx.send(f"{user} has been unbanned from using the openai cog")
            else:
                await ctx.send(f"{user} is not in the blacklist")
        else:
            await ctx.send(f"{user} is not an admin and cannot be unbanned from using the openai cog")


async def setup(client):
    """
    Sets up the cog
    :param client: Client object
    :return: None
    """
    await client.add_cog(OpenAI(client))
