import discord
import settings
from discord.ext import commands
import requests
import os
import time
import json
import asyncio
import re
from urllib.parse import quote, urlparse


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
        raw_url = settings.info_json.get("voice_api", {}).get("url", "http://localhost:8000")

        # Validate and sanitize the API URL
        if not self._validate_api_url(raw_url):
            settings.logger.error(f"Invalid voice API URL configured: {raw_url}. Using localhost fallback.")
            self.voice_api_url = "http://localhost:8000"
        else:
            self.voice_api_url = raw_url.rstrip('/')

        # Request timeout in seconds to prevent DoS
        self.request_timeout = 30

    def _validate_api_url(self, url: str) -> bool:
        """
        Validates the API URL to prevent SSRF attacks
        :param url: URL to validate
        :return: True if valid, False otherwise
        """
        try:
            parsed = urlparse(url)
            # Only allow http and https schemes
            if parsed.scheme not in ['http', 'https']:
                settings.logger.warning(f"Invalid URL scheme: {parsed.scheme}")
                return False

            # Ensure hostname is present
            if not parsed.netloc:
                settings.logger.warning("URL missing hostname")
                return False

            # Block localhost variations, internal IPs (for production security)
            # Uncomment these checks in production:
            # blocked_hosts = ['127.', '0.0.0.0', 'localhost', '10.', '172.16.', '192.168.', '169.254.']
            # if any(parsed.netloc.startswith(blocked) for blocked in blocked_hosts):
            #     settings.logger.warning(f"Blocked internal/localhost URL: {parsed.netloc}")
            #     return False

            return True
        except Exception as e:
            settings.logger.error(f"Error validating URL: {e}")
            return False

    def _sanitize_voice_name(self, voice_name: str) -> str:
        """
        Sanitizes voice name to prevent injection attacks
        :param voice_name: Voice name to sanitize
        :return: Sanitized voice name or None if invalid
        """
        # Only allow alphanumeric, underscore, and hyphen
        if not re.match(r'^[a-zA-Z0-9_-]+$', voice_name):
            return None
        # Limit length
        if len(voice_name) > 50:
            return None
        return voice_name

    def _sanitize_uuid(self, uuid: str) -> str:
        """
        Sanitizes UUID to prevent injection attacks
        :param uuid: UUID to sanitize
        :return: Sanitized UUID or None if invalid
        """
        # UUID format validation
        if not re.match(r'^[a-f0-9-]+$', uuid, re.IGNORECASE):
            return None
        # Limit length
        if len(uuid) > 36:
            return None
        return uuid

    @commands.command(pass_context=True, aliases=['av'], brief='Adds a voice', help='Adds a voice')
    async def add_voice(self, ctx, voice_name: str):
        """
        Adds a voice to the database
        :param ctx: context
        :param voice_name: voice name
        """
        # Sanitize voice name to prevent injection
        sanitized_name = self._sanitize_voice_name(voice_name)
        if not sanitized_name:
            await ctx.send(f'Invalid voice name. Use only alphanumeric characters, underscores, and hyphens.')
            settings.logger.warning(f"Invalid voice name attempted by {ctx.author}: {voice_name}")
            return

        # try to make a voice
        # Use URL encoding for safety
        r = requests.put(f'{self.voice_api_url}/new_voice?name={quote(sanitized_name)}', timeout=self.request_timeout)
        if r.status_code == 200:
            await ctx.send(f'Voice {sanitized_name} added')
        else:
            await ctx.send(f'Failed to add voice {sanitized_name}')

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
        # Sanitize voice name to prevent injection
        sanitized_name = self._sanitize_voice_name(voice_name)
        if not sanitized_name:
            await ctx.send(f'Invalid voice name. Use only alphanumeric characters, underscores, and hyphens.')
            settings.logger.warning(f"Invalid voice name attempted by {ctx.author}: {voice_name}")
            return

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
                # try to make a clip - use URL encoding for safety
                r = requests.put(f'{self.voice_api_url}/new_clip?voice_name={quote(sanitized_name)}', files=files, timeout=self.request_timeout)

            if r.status_code == 200:
                await ctx.send(f'Clip {f.filename} added to voice {sanitized_name}')
            else:
                await ctx.send(f'Failed to add clip {f.filename} to voice {sanitized_name}')

    @commands.command(pass_context=True, aliases=['mc'], brief='Makes a clip', help='Makes a clip')
    async def make_clip(self, ctx, voice_name: str, *text: str):
        """
        Makes a clip with the given text and voice
        :param ctx: context
        :param voice_name: voice name
        :param text: text
        """
        # Sanitize voice name to prevent injection
        sanitized_name = self._sanitize_voice_name(voice_name)
        if not sanitized_name:
            await ctx.send(f'Invalid voice name. Use only alphanumeric characters, underscores, and hyphens.')
            settings.logger.warning(f"Invalid voice name attempted by {ctx.author}: {voice_name}")
            return

        # create data - use sanitized name
        data = {'model': sanitized_name, 'text': ''.join(text), 'preset': "standard", "candidates": 1}
        json_data = json.dumps(data)

        # make request
        r = requests.put(f'{self.voice_api_url}/gen_voice', data=json_data, timeout=self.request_timeout)

        # check if request was successful
        if r.status_code == 200:
            await ctx.send(f'Clip is being processed')
        else:
            await ctx.send(f'Failed to make clip: {r.status_code} {r.text}')
            return

        # get uuid
        try:
            uuid = r.json()["uuid"]
        except (KeyError, json.JSONDecodeError) as e:
            await ctx.send(f'Invalid response from voice API')
            settings.logger.error(f"Invalid response from voice API: {e}")
            return

        # Sanitize UUID to prevent injection
        sanitized_uuid = self._sanitize_uuid(uuid)
        if not sanitized_uuid:
            await ctx.send(f'Invalid UUID received from API')
            settings.logger.error(f"Invalid UUID from API: {uuid}")
            return

        # get start time
        start_time = time.time()

        while True:
            r = requests.get(f'{self.voice_api_url}/get_clip?uid={quote(sanitized_uuid)}&clip=0', timeout=self.request_timeout)
            # TODO: schedule a task to check every few seconds so the bot can do other things
            if r.status_code == 200:
                # download clip
                if not os.path.exists("voices"):
                    os.mkdir("voices")
                with open(f'voices/{sanitized_uuid}.wav', 'wb') as f:
                    f.write(r.content)
                await ctx.send(f'Clip ready', file=discord.File(f'voices/{sanitized_uuid}.wav'))
                # TODO: fix this
                # await ctx.author.voice.channel.connect()
                # source = discord.PCMVolumeTransformer(
                #     discord.FFmpegPCMAudio(source=f"{f'voices/{sanitized_uuid}.wav'}"), volume=1.0)
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
        r = requests.get(f'{self.voice_api_url}/get_voices', timeout=self.request_timeout)
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
