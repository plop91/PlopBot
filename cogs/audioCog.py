import logging
from discord.ext import commands, tasks
from discord.errors import ClientException
from discord.utils import get
import markovify
from gtts import gTTS
import asyncio
import os
import json
import random
from yt_dlp import YoutubeDL
import discord
import ffmpeg
import shutil
import settings
import traceback

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': 'youtube/%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        """
        This is the constructor for the YTDLSource class. It sets up the YTDLSource object.
        :param source: The source of the audio.
        :param data: The data of the audio.
        :param volume: The volume of the audio.
        """
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        """
        This function is used to get the audio from a YouTube video.
        :param url: The url of the YouTube video.
        :param loop: The loop to use.
        :param stream: Whether to stream the audio.
        :return: The YTDLSource object.
        """
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.sanitize_info(ytdl.extract_info(url, download=not stream)))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Audio(commands.Cog):
    volume = 0.7

    def __init__(self, client):
        """
        This is the constructor for the audio cog. It sets up the maintenance task and loads the soundboard.
        :arg client:
        """
        self.client = client
        self.maintenance.start()
        self.models = {}
        self.sounds = {}
        for file in os.listdir("soundboard"):
            if file.endswith(".mp3"):
                temp = file.strip().replace(".mp3", "").lower()
                self.sounds[temp] = "soundboard/" + file
        if os.path.isdir("markov"):
            for markov in os.listdir("markov"):
                if ".json" in markov:
                    with open("markov/{}".format(markov)) as f:
                        self.models[markov.replace('.json', '')] = markovify.Text.from_json(json.load(f))

    @staticmethod
    def clean_youtube():
        """
        This function removes any downloaded videos from the YouTube folder.
        :return:
        """
        settings.logger.info(f"cleaning youtube folder!")
        for f in os.listdir("youtube"):
            os.remove(os.path.join("youtube", f))

    @commands.Cog.listener()
    async def on_ready(self):
        """
        Logs that the cog was loaded properly and empties the YouTube folder.
        :return: None
        """
        settings.logger.info(f"audio cog ready!")

    @commands.Cog.listener()
    async def on_disconnect(self):
        """
        Logs the cog has turned off
        :return: None
        """
        self.clean_youtube()

    @commands.Cog.listener()
    async def on_message(self, message):
        """
        This listener is to facilitate the ability to download a mp3 for use in the soundboard as well as
        interprets webhook commands.
        :arg: message: The message that was sent.
        :return: None
        """
        # If the message is not from the bot itself.
        if message.author != self.client.user:
            # If there is an attachment
            if message.attachments:
                # For each attachment
                for attachment in message.attachments:
                    # If the file is a mp3
                    if attachment.filename.endswith(".mp3"):
                        # If a file with that name is already in the soundboard folder
                        if os.path.exists(f"./soundboard/{attachment.filename.lower().replace(' ', '')}"):
                            settings.logger.info(
                                f"{message.author} tried to add a mp3 file: {attachment} but a file with that name "
                                f"already exists.")
                            await message.channel.send("A clip with that name already exists please rename it to "
                                                       "upload.")
                            # If a file with that name exists in the soundboard/raw folder
                        elif os.path.exists(f"./soundboard/raw/{attachment.filename.lower().replace(' ', '')}"):
                            settings.logger.info(
                                f"{message.author} tried to add a mp3 file: {attachment} but a file with that name "
                                f"already exists in raw clips.")
                            await message.channel.send("A clip with that name has already been uploaded and is waiting "
                                                       "for admin approval. Notify an admin to resolve.")
                        # If this is a new filename
                        else:
                            filename = attachment.filename.lower().replace(' ', '').replace('_', '')
                            settings.logger.info(f"{message.author} added a mp3 file: {attachment}")
                            await message.channel.send(
                                f"The audio is being downloaded and should be ready shortly the name of the clip will "
                                f"be: {filename.replace('.mp3', '')}")
                            await attachment.save(f"./soundboard/raw/{filename}")
                            audio_json = ffmpeg.probe(f"./soundboard/raw/{filename}")

                            # If the clip is too long it needs to be reviewed
                            if float(audio_json['streams'][0]['duration']) >= 60:
                                await message.channel.send("The clip is longer than a minute and will need to be "
                                                           "reviewed before it can be played.")
                            else:
                                try:
                                    shutil.copy(f"./soundboard/raw/{filename}", f"./soundboard/{filename}")
                                    settings.soundboard_db.add_db_entry(filename.lower(),
                                                                        filename.replace(".mp3", "").lower())
                                    self.sounds[filename.replace(".mp3", "").lower()] = f"./soundboard/{filename}"
                                except ValueError:
                                    await message.channel.send("A file with that name already existed in the database, "
                                                               "contact an admin!")
                                    settings.logger.warning("a file with the same name exists in the database but not "
                                                            "on the server")

            else:
                # divide message as though it was a webhook command
                data = message.content.split(':')
                # check if it has a valid source
                if data[0] == "www.sodersjerna.com":
                    member = await discord.utils.get(message.guild.members, name=data[1])
                    if member is not None and member.voice is not None:
                        for client in self.client.voice_clients:
                            if client.channel.id == member.voice.channel.id:
                                if data[2] == "stop":
                                    if client.is_playing():
                                        client.stop()
                                elif data[2] == "pause":
                                    if client.is_playing():
                                        client.pause()
                                elif data[2] == "resume":
                                    if client.is_paused():
                                        client.resume()
                                elif data[2] == "play":
                                    await self.play_clip(client.channel, client, data[3])
                    await message.delete()

    async def play_clip(self, text_channel, voice_channel, filename):
        """
        This function is used to play a clip from the soundboard folder.
        :arg text_channel: channel to send messages to
        :arg voice_channel: channel to play the clip in
        :arg filename: name of the file to play
        :return: None
        """
        try:
            filename = filename.strip()
            if filename == "random":
                filename = random.choice(list(self.sounds.values()))
                source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(source=f"{filename}"))
            else:
                if filename + ".mp3" in os.listdir("soundboard"):
                    source = discord.PCMVolumeTransformer(
                        discord.FFmpegPCMAudio(source=f"{os.path.join('soundboard', filename + '.mp3')}"))
                else:
                    # TODO: remove this test line
                    settings.logger.info(f"That clip does not exist, test line")
                    await text_channel.send("That clip does not exist.")
                    return
            voice_channel.play(source)

        except AttributeError:
            settings.logger.info(f"Attribute Error: {traceback.format_exc()}")

        except PermissionError:
            settings.logger.warning(f"Permission Error: {traceback.format_exc()}")

        except ClientException:
            settings.logger.warning(f"Client Exception: {traceback.format_exc()}")

        except Exception:
            settings.logger.warning(f"unknown exception {traceback.format_exc()}")

    @commands.command(pass_context=True,
                      aliases=['p', 'PLAY', 'P'],
                      brief="Plays a clip with the same name as the argument. alt command = 'p'",
                      description="Makes the bot play one of the soundboard files. For example if you wanted to play "
                                  "a file named hammer you would enter '.play hammer'/'.p hammer'")
    async def play(self, ctx, filename=None):
        """
        Plays a mp3 from the library of downloaded mp3's
        :arg ctx: context of the message
        :arg filename: name of the file to play
        :return: None
        """
        settings.logger.info(f"play from {ctx.author} :{filename}")
        if ctx.author not in settings.info_json["blacklist"]:
            if filename is None:
                embed_var = discord.Embed(title="Soundboard files",
                                          description="type '.play ' followed by a name to play "
                                                      "file", color=0x00ff00)
                s = ""
                for file in self.sounds.keys():
                    if len(s) + len(file) >= 1024:
                        embed_var.add_field(name="play from a filename:", value=s, inline=False)
                        s = ""
                    s += file + ", "

                embed_var.add_field(name="play from a filename:", value=s, inline=False)

                embed_var.add_field(name="play a random file:", value="random", inline=False)

                await ctx.channel.send(embed=embed_var)
                await ctx.message.delete()

                return

            await self.play_clip(ctx, ctx.voice_client, filename)
        await ctx.message.delete()

    @commands.command(pass_context=True,
                      aliases=['yt', 'YOUTUBE', 'YT'],
                      brief="Plays the youtube clip at the url in the argument. alt command = 'yt'",
                      description="Makes the bot play a youtube videos audio. For example if you wanted to play the "
                                  "youtube video at 'https://www.youtube.com/watch?v=1234' you would enter '.youtube "
                                  "https://www.youtube.com/watch?v=1234'/'.yt https://www.youtube.com/watch?v=1234'")
    async def youtube(self, ctx, *, url):
        """
        Downloads and plays the audio of the provided YouTube link. Plays from an url (almost anything yt_dlp
        supports)
        :arg ctx: context of the message
        :arg url: url of the YouTube video to play
        :return: None
        """
        settings.logger.info(f"youtube from {ctx.author} :{url}")
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.client.loop)
            ctx.voice_client.play(player)
        await ctx.message.delete()

    @commands.command(pass_context=True,
                      aliases=['STREAM'],
                      brief="Streams from a url (same as yt, but doesn't pre-download)",
                      description="Streams from a url (same as yt, but doesn't pre-download)")
    async def stream(self, ctx, *, url):
        """
        Streams from an url (same as yt, but doesn't pre-download)
        :arg ctx: context of the message
        :arg url: url of the YouTube video to play
        :return: None
        """
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=self.client.loop, stream=True)
            ctx.voice_client.play(player)
        await ctx.message.delete()

    @commands.command(pass_context=True,
                      aliases=['l', 'LEAVE', 'L'],
                      brief="Make the bot leave the voice server. alt command = 'l'",
                      description="Makes the bot leave the voice server.")
    async def leave(self, ctx):
        """
        Forces the bot to leave any voice channel it is in.
        :arg ctx: context of the message
        :return: None
        """
        settings.logger.info(f"leave from {ctx.author}")

        channel = ctx.message.author.voice.channel
        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_connected():
            await voice.disconnect()
            settings.logger.info(f"The bot has left {channel}")
        else:
            settings.logger.info(f"Bot was told to leave voice channel, but was not in one!")
            await ctx.send("Don't think I am in a voice channel")

        await ctx.message.delete()

    @commands.command(pass_context=True,
                      aliases=['PAUSE'],
                      brief="Pause everything the bot is playing",
                      description="Makes the bot pause anything that it is playing.")
    async def pause(self, ctx):
        """
        Pauses whatever the bot is playing
        :arg ctx: context of the message
        :return: None
        """
        settings.logger.info(f"pause from {ctx.author}")

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            voice.pause()
        else:
            await ctx.send("No music playing dum dum")

        await ctx.message.delete()

    @commands.command(pass_context=True,
                      aliases=['r', 'RESUME', 'R'],
                      brief="Resume playing paused Music. alt command = 'r'",
                      description="Makes the bot resume playing any paused audio.")
    async def resume(self, ctx):
        """
        Resumes playing if the bot is paused
        :arg ctx: context of the message
        :return: None
        """
        settings.logger.info(f"resume from {ctx.author}")

        voice = get(self.client.voice_clients, guild=ctx.guild)
        if voice and voice.is_paused():
            voice.resume()
        else:
            await ctx.send("No music paused dum dum")

        await ctx.message.delete()

    @commands.command(pass_context=True,
                      aliases=['s', 'STOP', 'S'],
                      brief="Stop any Music the bot is playing or has paused. alt command = 's'",
                      description="Makes the bot stop playing any audio and forget what it was "
                                  "playing and when it stopped.")
    async def stop(self, ctx):
        """
        Stops playing whatever is playing
        :arg ctx: context of the message
        :return: None
        """
        settings.logger.info(f"stop from {ctx.author}")

        voice = get(self.client.voice_clients, guild=ctx.guild)

        if voice and voice.is_playing():
            voice.stop()
        else:
            await ctx.send("No music playing dum dum")

        await ctx.message.delete()

    @commands.command(pass_context=True,
                      aliases=['v', 'VOLUME', 'V', 'vol'],
                      brief="changes the volume of the bot",
                      description="Changes the volume of the bot.")
    async def volume(self, ctx, volume: int):
        """
        Change the volume the bot plays back at
        :arg ctx: context of the message
        :arg volume: volume to change to
        :return: None
        """

        if ctx.voice_client is None:
            return await ctx.send("Not connected to a voice channel.")

        if volume > 100 or volume < 0:
            return await ctx.send("Volume must be between 0 and 100")

        ctx.voice_client.source.volume = volume / 100
        settings.logger.info(f"volume changed to {volume} by {ctx.author}")
        await ctx.message.delete()
        await ctx.send(f"Changed volume to {volume}")

    @commands.command(pass_context=True,
                      aliases=['g', 'GET', 'G'],
                      brief="returns a soundbite",
                      description="returns a soundbite")
    async def get(self, ctx, sound: str):
        """
        Returns a soundbite
        :arg ctx: context of the message
        :arg sound: sound to return
        :return: None
        """
        if os.path.isfile(os.path.join("soundboard", sound)):
            await ctx.channel.send(sound, file=discord.File(sound + ".mp3", os.path.join("soundboard", sound)))

    @commands.command(pass_context=True,
                      aliases=[],
                      brief="",
                      description="Uses a markov chain to generate a sentence and say it using TTS")
    async def markov(self, ctx, model_name, output_file='soundboard/markov.mp3'):
        """
        uses a markov chain to generate a sentence and say it using TTS.
        :arg ctx: context of the message
        :arg model_name: name of the model to use
        :arg output_file: file to save the TTS to
        :return: None
        """
        settings.logger.info(f"reddit from {ctx.author}")
        if model_name in self.models:
            sent = None
            while sent is None:
                sent = self.models[model_name].make_sentence(tries=1000)
            tts = gTTS(sent)
            tts.save(output_file)
            await self.play_clip(ctx, ctx.voice_client, output_file)
        else:
            settings.logger.warning("markov model does not exist")
            await ctx.send("model does not exist")
        await ctx.message.delete()

    @commands.command(aliases=['SAY'],
                      brief="",
                      description="")
    async def say(self, ctx, text, *, tts_file='soundboard/say.mp3'):
        """
        Say the given string in the audio channel using TTS.
        :arg ctx: context of the message
        :arg text: text to say
        :arg tts_file: file to save the TTS to
        :return: None
        """
        settings.logger.info(f"say from {ctx.author} text:{text}")
        text = text.strip().lower()
        gTTS(text).save(tts_file)
        await self.play_clip(ctx, ctx.voice_client, tts_file)
        await ctx.message.delete()

    @play.before_invoke
    @youtube.before_invoke
    @markov.before_invoke
    @say.before_invoke
    async def ensure_voice(self, ctx):
        """
        Verifies the bot is in a voice channel before it tries to play something new.
        :arg ctx: context of the message
        :return: None
        """
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()

    @tasks.loop(seconds=0, minutes=0, hours=24)
    async def maintenance(self):
        """
        task to run maintenance, including removing unneeded YouTube clips and
        :return: None
        """
        self.clean_youtube()
        settings.soundboard_db.verify_db()
        settings.logger.info(f"Maintenance completed")


async def setup(client):
    await client.add_cog(Audio(client))
