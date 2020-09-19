import discord
from discord.ext import commands, tasks
from tools.basicTools import readJson, addToJson
import random

json_name = "info.json"
json = readJson(json_name)


class general(commands.Cog):

    def __init__(self, client, info):
        self.client = client
        self.info = info

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""general cog ready!""")
        self.change_status.start()

    @commands.Cog.listener()
    async def on_message(self, message):
        _id = message.guild
        message.content = message.content.strip().lower()
        if message.content:
            print(f"""Message from {message.author}: {message.content}""")
        if message.author != self.client.user:
            if message.content.lower() == "hey":
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

    @commands.command(brief="Change the bot presence to the argument string.")
    async def echo(self, ctx, tag):
        if tag:
            await self.client.change_presence(status=discord.Status.online, activity=discord.Game(tag))
            addToJson(json_name, "status", tag)
            await ctx.message.delete()

    @commands.command(brief="List the previous statuses the bot will loop through.")
    async def status(self, ctx):

        u_json = readJson(json_name)
        s = ""
        for status in u_json["status"]:
            s += status + ", "

        embed_var = discord.Embed(title="Status:", description=s, color=0x00ff00)

        await ctx.channel.send(embed=embed_var)
        await ctx.message.delete()

    @tasks.loop(seconds=0, minutes=0, hours=1)
    async def change_status(self):
        u_json = readJson(json_name)
        await self.client.change_presence(status=discord.Status.online, activity=discord.Game(
            u_json["status"][random.randint(0, len(u_json["status"]) - 1)]))


def setup(client):
    client.add_cog(general(client, json))
