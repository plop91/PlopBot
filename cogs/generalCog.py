import discord
from discord.ext import commands
from tools.basicTools import readJson


info = readJson("info.json")


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
        print(f"""Message from {message.author}: {message.content}""")
        if message.author != self.client:
            if message.content == "hey":
                await message.channel.send("Hi")
            elif message.content == "bool":
                await message.channel.send("To bool or not to bool this is the question")
            elif message.content == "to bool":
                for name in info["boolers"]:
                    member = discord.utils.get(message.guild.members, name=name)
                    await message.channel.send(f"""call to bool {member.mention}?""")
            elif message.content.find("fuck") != -1 and message.content.find("you") != -1 and message.content.find(
                    "jon") != -1:
                await message.channel.send("yeah fuck you jon!!!!")
            elif message.content.find("fuck") != -1 and message.content.find("you") != -1 and (
                    message.content.find("bradley") != -1 or message.content.find("brad") != -1 or message.content.find(
                    "bob") != -1):
                await message.channel.send("yeah fuck you brad!!!!")
            if str(message.channel) in info["command_channels"]:
                if str(message.author) in info["valid_users"]:
                    if message.content == "!stop":
                        await self.client.logout()
                    elif message.content == "!users":
                        await message.channel.send(f"""number of members {_id.member_count}""")
                else:
                    print(
                        f"""User: {message.author} tried to do command {message.content}, in channel {message.channel}""")

    @commands.Cog.listener()
    async def on_member_join(self, member):
        for channel in member.guild.channels:
            if str(channel) in info["welcome_channels"]:
                await channel.send(f"""Who are you{member.mention}?""")

    @commands.command()
    async def ping(self, ctx):
        await ctx.send('test')

    @commands.command()
    async def printTag(self, ctx, tag):
        i = 1
        for name in info[tag]:
            await ctx.send(f'number {i}: {name}')
            i += 1


def setup(client):
    client.add_cog(general(client, info))
