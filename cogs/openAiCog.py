"""
This cog is for generating images and text using openai
"""
import time

import discord
import settings
from discord.ext import commands
from openai import OpenAI as Oai
import wget
import os
import textwrap
from PIL import Image
import json
import asyncio

from db.openai_database_manager import OpenAIDatabaseManager

global logger

blacklist = []


def blacklisted(user):
    """
    Checks if a user is blacklisted
    :param user: user to check
    :return: True if blacklisted, False otherwise
    """
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
        # openai.api_key = self.api_key
        self.openai_client = Oai(api_key=self.api_key)

        self.db_manager = OpenAIDatabaseManager(
            settings.info_json["openai"]["db_host"],
            settings.info_json["openai"]["db_username"],
            settings.info_json["openai"]["db_password"],
            settings.info_json["openai"]["database_name"]
        )

        try:
            self.db_manager.connect()
        except Exception as e:
            settings.logger.warning(f"Error connecting to openai database: {e}")

        self.active_assistants = {}
        self.active_threads = {}

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

        if not blacklisted(ctx.author):
            prompt = ' '.join(args)
            settings.logger.info(f"generating image")
            response = self.openai_client.images.generate(
                model="dall-e-3",
                prompt=prompt,
                size="1024x1024",
                quality="standard",
                n=1
            )
            # image_url = response['data'][0]['url']
            image_url = response.data[0].url
            image_filename = wget.download(image_url)
            await ctx.send(file=discord.File(image_filename))
            os.remove(image_filename)

            # todo: add to database
        else:
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")

    @commands.command(pass_context=True, aliases=["editimg", "editimage", "edit_image"],
                      brief="edit an image from a prompt using openai")
    async def edit_img(self, ctx):
        """
        Edit an image from a prompt using openai
        :arg ctx: Context
        :return: None
        """

        if not blacklisted(ctx.author):
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
            response = self.openai_client.images.create_variation(
                image=open("temp.png", "rb"),
                n=1,
                size="1024x1024"
            )
            os.remove("temp.png")
            image_url = response['data'][0]['url']
            image_filename = wget.download(image_url)
            await ctx.send(file=discord.File(image_filename))
            os.remove(image_filename)

            # todo: add to database
        else:
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")

    async def get_updated_assistants(self, ctx):
        """
        Get the updated assistants from openai
        :return: None
        """
        guild = ctx.guild.id
        my_assistants = self.openai_client.beta.assistants.list(
            order="desc",
            limit=100
        )
        if guild not in self.active_assistants:
            self.active_assistants[guild] = {}
        for assistant in my_assistants.data:
            name = assistant.name
            if name in self.active_assistants[guild]:
                if assistant.id != self.active_assistants[guild][name].id:
                    self.active_assistants[guild][name] = assistant
            else:
                self.active_assistants[guild][name] = assistant

    @commands.command(pass_context=True, aliases=["la", "listassistants"],
                      brief="Prints the list of existing assistants")
    async def list_assistants(self, ctx):
        """
        Prints the list of existing assistants
        :arg ctx: Context
        :return: None
        """
        if not blacklisted(ctx.author):

            await ctx.typing()

            await self.get_updated_assistants(ctx)

            guild = ctx.guild.id
            if guild in self.active_assistants:
                await ctx.send("Current active assistants: " + ", ".join(list(self.active_assistants[guild].keys())))
        else:
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")

    @commands.command(pass_context=True, aliases=["cra", "createassistant"],
                      brief="Create an assistant from a prompt using openai")
    async def create_assistant(self, ctx, name, *args):
        """
        Create an assistant from a prompt using openai
        :arg ctx: Context
        :arg name: Name of the assistant
        :arg args: Arguments
        :return: None
        """
        if not blacklisted(ctx.author):

            await ctx.typing()

            await self.get_updated_assistants(ctx)

            guild = ctx.guild.id
            # TODO: check if the assistant already exists on openai
            if guild in self.active_assistants:
                if name in self.active_assistants[guild]:
                    await ctx.send(f"Assistant {name} already exists")
                    return

            # functions = os.listdir("../openAI_functions/")
            # ctx.send(f"functions: {functions}")

            # TODO: add all the functions to the assistant
            tools = [{"type": "code_interpreter"}, {"type": "retrieval"}]

            functions = os.listdir("openAI_functions/")
            for function in functions:
                if function.endswith(".json"):
                    try:
                        with open(f"openAI_functions/{function}", "r") as file:
                            data = file.read()
                            if data:
                                tools.append(json.loads(data))
                    except FileNotFoundError as e:
                        settings.logger.warning(f"File not found: {e}")
                    except Exception as e:
                        settings.logger.warning(f"Error loading function: {e}")

            # generate tool notifications
            notification = ""
            for tool in tools:
                if tool["type"] == "code_interpreter":
                    notification += "Code interpreter tool added\n"
                elif tool["type"] == "retrieval":
                    notification += "Retrieval tool added\n"
                elif tool["type"] == "function":
                    notification += f"Function tool added: {tool['function']['name']}\n"
                else:
                    notification += "Unknown tool!!!!!\n"

            prompt = ' '.join(args)  # the prompt used to initialize the assistant

            settings.logger.info(f"creating assistant")
            assistant = self.openai_client.beta.assistants.create(
                name=name,
                instructions=prompt,
                tools=tools,
                model="gpt-4-turbo-preview"
            )
            # if an assistant already exists for this guild
            if guild in self.active_assistants:
                self.active_assistants[guild][name] = assistant
            else:
                self.active_assistants[guild] = {name: assistant}

            await ctx.send(f"Assistant {name} created with tools:\n{notification}")
        else:
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")

    async def handle_tool_call(self, ctx, run, thread_id):
        """
        Handles the tool call for the assistant
        :param ctx: Context
        :param run: Run object
        :param thread_id: Thread id
        """
        if run.required_action.submit_tool_outputs:
            if run.required_action.submit_tool_outputs.tool_calls:
                outputs = []
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    try:
                        # await ctx.send(f"{tool_call}")
                        if tool_call.function.name == "get_weather":
                            # await ctx.send(f"get weather tool call args: {tool_call.function.arguments}")
                            # TODO: actually get the weather
                            # send 20 degrees celsius
                            output = {
                                "tool_call_id": tool_call.id,
                                "output": "20C"
                            }
                            outputs.append(output)
                        elif tool_call.function.name == "get_chat_history":
                            chat_history = []
                            async for message in ctx.channel.history(limit=200):
                                chat_history.append(message)
                            count = 0
                            chat = ""
                            for message in chat_history:
                                if count >= 20:
                                    break
                                if message.content and message.author != self.client.user:
                                    chat += message.author.name + ": " + message.content + "\n"
                                    count += 1
                            output = {
                                "tool_call_id": tool_call.id,
                                "output": chat
                            }
                            outputs.append(output)

                        elif tool_call.function.name == "get_users_voice":
                            await ctx.send(f"tool call {tool_call.function.name} not implemented yet")
                            output = {
                                "tool_call_id": tool_call.id,
                                "output": " ".join([])
                            }
                            outputs.append(output)

                        elif tool_call.function.name == "get_users_text":
                            members = ctx.channel.members
                            online_members = []
                            for member in members:
                                if member.status == discord.Status.online:
                                    online_members.append(member.name)
                            output = {
                                "tool_call_id": tool_call.id,
                                "output": " ".join(online_members)
                            }
                            outputs.append(output)

                        elif tool_call.function.name == "get_soundboard_names":
                            audio = self.client.get_cog('Audio')
                            output = {
                                "tool_call_id": tool_call.id,
                                "output": " ".join(audio.sounds)
                            }
                            outputs.append(output)

                        elif tool_call.function.name == "play_soundboard":
                            audio = self.client.get_cog('Audio')
                            sound = tool_call.function.arguments
                            if sound in audio.sounds:
                                audio.play(ctx, sound)
                            else:
                                await ctx.send(f"Sound {sound} not found")

                        # get bot usage
                        # get player stats
                        else:
                            await ctx.send(f"tool call {tool_call.function.name} not recognized")
                    except Exception as e:
                        await ctx.send(f"Error: {e}")
                try:
                    self.openai_client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=outputs
                    )
                except Exception as e:
                    await ctx.send(f"Error: {e}")

    @commands.command(pass_context=True, aliases=["ca", "chatassistant"],
                      brief="chat with an assistant using openai")
    async def chat_assistant(self, ctx, name, *args):
        """
        Chat with an assistant using openai
        :arg ctx: Context
        :arg name: Name of the assistant
        :arg args: Arguments
        :return: None
        """
        if not blacklisted(ctx.author):
            await ctx.typing()

            await self.get_updated_assistants(ctx)

            guild = ctx.guild.id
            prompt = ' '.join(args)
            # check if assistant exists
            if ctx.guild.id not in self.active_assistants:
                await ctx.send(f"Assistant {name} does not exist")
                return

            if name not in self.active_assistants[guild]:
                await ctx.send(f"Assistant {name} does not exist")
                return

            assistant = self.active_assistants[guild][name]
            thread = self.openai_client.beta.threads.create()
            if guild in self.active_threads:
                if name not in self.active_threads[guild]:
                    self.active_threads[guild][name] = thread
            else:
                self.active_threads[guild] = {name: thread}

            thread_id = self.active_threads[guild][name].id
            self.openai_client.beta.threads.messages.create(
                thread_id=thread_id,
                role="user",
                content=prompt
            )
            run = self.openai_client.beta.threads.runs.create(
                thread_id=thread_id,
                assistant_id=assistant.id
            )
            start_time = run.created_at
            while True:
                run = self.openai_client.beta.threads.runs.retrieve(
                    thread_id=thread_id,
                    run_id=run.id
                )

                current_time = time.time()
                if current_time - start_time > 60:
                    # TODO: if the assistant times out, deduct from the user's usage, then cancel the run
                    await ctx.send("Assistant time out - cancelling")
                    run = self.openai_client.beta.threads.runs.cancel(
                        thread_id=thread_id,
                        run_id=run.id
                    )
                    if run.status == "cancelling" or run.status == "cancelled":
                        await ctx.send("Assistant run cancelled")
                    else:
                        await ctx.send("Error cancelling assistant run")
                    return

                if "completed" in run.status:
                    break
                elif run.status == "queued":
                    pass
                elif run.status == "in_progress":
                    pass
                elif run.status == "failed":
                    await ctx.send("Assistant failed")
                    return
                elif run.status == "expired":
                    await ctx.send("Assistant expired")
                    return
                elif run.status == "requires_action":
                    await self.handle_tool_call(ctx, run, thread_id)
                elif run.status == "cancelled":
                    await ctx.send("Assistant cancelled")
                    return
                elif run.status == "cancelling":
                    await ctx.send("Assistant cancelling")
                    return
                else:
                    await ctx.send(f"{run.status} not recognized")
                    return
                await asyncio.sleep(2)

            messages = self.openai_client.beta.threads.messages.list(
                thread_id=thread_id
            )

            for content in messages.data[0].content:
                # break up long messages
                if content.type == "text":
                    for line in textwrap.wrap(f"{name} says: {content.text.value}", 1024):
                        await ctx.send(line)
                # retrieve image file
                else:
                    image_data = self.openai_client.files.content(content.image_file.file_id)
                    image_data_bytes = image_data.read()

                    image_filename = "./my-image.png"
                    with open(image_filename, "wb") as file:
                        file.write(image_data_bytes)
                        await ctx.send(file=discord.File(image_filename))
                        os.remove(image_filename)

        else:
            settings.logger.info(f"User {ctx.author} is blacklisted from AI cog!")

    # TODO: add upload file for retrieval tool
    # TODO: add ability to add functions to the assistant on the fly

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
            blacklist.append(str(user).strip().lower())
            await ctx.send(f"{user} has been banned from using the openai cog")
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
