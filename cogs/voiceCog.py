import discord
import settings
from discord.ext import commands
import requests
import os
import time
import json
import asyncio


class Voices(commands.Cog):
    """
    Functions:
    add_voice: this function adds a voice to the database (NOTE: any clips attached to the message will be included)
        arg: voice_name: str
    add_clip:
        arg: voice_name: str
    make clip: this function creates new clips with the given text and voice, this function will also create a new message,
    the message will inform the user that the clip is being processed, the message will be updated when the clip is ready.
        arg: voice_name: str
        arg: text: str
    """

    def __init__(self, client):
        """
        Constructor for the voices cog
        :param client: Client object
        """
        self.client = client
        # Get voice API URL from config, fallback to localhost
        self.voice_api_url = settings.info_json.get("voice_api", {}).get("url", "http://localhost:8000")

    @commands.command(pass_context=True, aliases=['av'], brief='Adds a voice', help='Adds a voice')
    async def add_voice(self, ctx, voice_name: str):
        """
        Adds a voice to the database
        :param ctx: context
        :param voice_name: voice name
        """
        # try to make a voice
        r = requests.put(f'{self.voice_api_url}/new_voice?name={voice_name}')
        if r.status_code == 200:
            await ctx.send(f'Voice {voice_name} added')
        else:
            await ctx.send(f'Failed to add voice {voice_name}')

        if ctx.message.attachments:
            # TODO: add the clips to the database
            pass

    @commands.command(pass_context=True, aliases=['ac'], brief='Adds a clip', help='Adds a clip')
    async def add_clip(self, ctx, voice_name: str):
        """
        Adds a clip to the database
        :param ctx: context
        :param voice_name: voice name
        """
        if not ctx.message.attachments:
            await ctx.send('No clip attached')
            return

        # mk temp dir
        if not os.path.exists('temp'):
            os.makedirs('temp')
        # download clip
        for f in ctx.message.attachments:
            await f.save(f'temp/{f.filename}')

            # upload clip to server
            with open(f'temp/{f.filename}', 'rb') as file:
                files = {'file': file}
                # try to make a clip
                r = requests.put(f'{self.voice_api_url}/new_clip?voice_name={voice_name}', files=files)

            if r.status_code == 200:
                await ctx.send(f'Clip {f.filename} added to voice {voice_name}')
            else:
                await ctx.send(f'Failed to add clip {f.filename} to voice {voice_name}')

    @commands.command(pass_context=True, aliases=['mc'], brief='Makes a clip', help='Makes a clip')
    async def make_clip(self, ctx, voice_name: str, *text: str):
        """
        Makes a clip with the given text and voice
        :param ctx: context
        :param voice_name: voice name
        :param text: text
        """
        # create data
        data = {'model': voice_name, 'text': ''.join(text), 'preset': "standard", "candidates": 1}
        json_data = json.dumps(data)

        # make request
        r = requests.put(f'{self.voice_api_url}/gen_voice', data=json_data)

        # check if request was successful
        if r.status_code == 200:
            await ctx.send(f'Clip is being processed')
        else:
            await ctx.send(f'Failed to make clip: {r.status_code} {r.text}')
            return

        # get uuid
        uuid = r.json()["uuid"]

        # get start time
        start_time = time.time()

        while True:
            r = requests.get(f'{self.voice_api_url}/get_clip?uid={uuid}&clip=0')
            # TODO: schedule a task to check every few seconds so the bot can do other things
            if r.status_code == 200:
                # download clip
                if not os.path.exists("voices"):
                    os.mkdir("voices")
                with open(f'voices/{uuid}.wav', 'wb') as f:
                    f.write(r.content)
                await ctx.send(f'Clip ready', file=discord.File(f'voices/{uuid}.wav'))
                # TODO: fix this
                # await ctx.author.voice.channel.connect()
                # source = discord.PCMVolumeTransformer(
                #     discord.FFmpegPCMAudio(source=f"{f'voices/{uuid}.wav'}"), volume=1.0)
                # ctx.voice_client.play(source)
                break
            if time.time() - start_time > 180:
                await ctx.send(f'Clip timed out')
                break
            await asyncio.sleep(5)

    @commands.command(pass_context=True, aliases=['lv'], brief='Lists voices', help='Lists voices')
    async def list_voices(self, ctx):
        """
        Lists voices
        :param ctx: context
        """
        r = requests.get(f'{self.voice_api_url}/get_voices')
        if r.status_code == 200:
            voices = r.json()["voices"]
            await ctx.send('Voices:\n' + "\n".join(voices))
        else:
            await ctx.send(f'Failed to list voices')


async def setup(client):
    """
    Sets up the cog
    :param client: Client object
    :return: None
    """
    await client.add_cog(Voices(client))
