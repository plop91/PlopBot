import discord
from discord import guild
from discord.ext import commands
from tools.basicTools import readJson

json = readJson("info.json")


class general(commands.Cog):

    def __init__(self, client, info):
        self.client = client
        self.info = info

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""Logged on as {self.client.user}!""")

    @commands.Cog.listener()
    async def on_message(self, message):
        _id = message.guild
        message.content = message.content.strip().lower()
        print(f"""Message from {message.author}: {message.content}""")
        if message.author != self.client.user:
            if message.content == "hey":
                await message.channel.send("Hi")

            elif message.content == "bool":
                await message.channel.send("To bool or not to bool this is the question")

            elif message.content == "to bool":
                for name in self.info["boolers"]:
                    member = discord.utils.get(message.guild.members, name=name)
                    await message.channel.send(f"""call to bool {member.mention}?""")

            elif message.content.find("fuck") != -1 and message.content.find("you") != -1:
                for name in self.info["nicknames"]:
                    if message.content.find(name) != -1:
                        await message.channel.send(f"yeah fuck you {name}!!!!")

            elif str(message.channel) in self.info["command_channels"]:
                if str(message.author) in self.info["valid_users"]:
                    if message.content == "!stop":
                        await self.client.logout()
                    elif message.content == "!users":
                        await message.channel.send(f"""number of members {_id.member_count}""")
                else:
                    print(
                        f"""User: {message.author} tried to do command {message.content}, in channel {
                        message.channel}""")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        print(f'deleted message- {message.author} : {message.content}')

    @commands.Cog.listener()
    async def on_member_join(self, member):
        for channel in member.guild.channels:
            if str(channel) in self.info["welcome_channels"]:
                await channel.send(f"""Who are you{member.mention}?""")

    @commands.command()
    async def stop(self, ctx):
        await self.client.logout()

    @commands.command()
    async def printTag(self, ctx, tag):
        i = 1
        for name in self.info[tag]:
            await ctx.send(f'number {i}: {name}')
            i += 1

    @commands.command()
    async def echo(self, ctx, tag):
        if tag:
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game(tag))

    @commands.command()
    async def splitTeam(self, ctx, channel1, channel2):
        voice_channel1 = discord.utils.get(ctx.message.server.channels, name=str(channel1),
                                           type=discord.ChannelType.voice)
        voice_channel2 = discord.utils.get(ctx.message.server.channels, name=str(channel2),
                                           type=discord.ChannelType.voice)
        members1 = voice_channel1.voice_members
        members2 = voice_channel2.voice_members
        memids = []
        for member in members1:
            memids.append(member.id)
        for member in members2:
            memids.append(member.id)
        ctx.send(memids)


def setup(client):
    client.add_cog(general(client, json))
