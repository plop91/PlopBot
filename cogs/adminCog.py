import discord
from discord.ext import commands
from tools.basicTools import readJson


info = readJson("info.json")


class admin(commands.Cog):

    def __init__(self, client, info):
        self.client = client
        self.info = info

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""admin cog ready!""")

    @commands.command()
    async def kill(self, ctx):
        print(ctx.message.channel)
        if str(ctx.message.channel) in info["command_channels"]:
            await self.client.logout()
            exit(0)



def setup(client):
    client.add_cog(admin(client, info))
