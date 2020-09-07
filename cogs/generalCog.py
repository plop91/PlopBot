import discord
from discord.ext import commands
from tools.basicTools import readJson

json_name = "info.json"
json = readJson(json_name)


class general(commands.Cog):

    def __init__(self, client, info):
        self.client = client
        self.info = info

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""general cog ready!""")

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
                await channel.send(f"""Who the fuck are you {member.mention}?""")

    @commands.command()
    async def printTag(self, ctx, tag):
        i = 1
        for name in self.info[tag]:
            await ctx.send(f'number {i}: {name}')
            i += 1


def setup(client):
    client.add_cog(general(client, json))
