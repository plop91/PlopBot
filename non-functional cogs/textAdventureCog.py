import discord
from discord.ext import commands
from tools.TextAdventure.start import adventure
import json

def readJson(file):
    with open(file) as f:
        data = json.load(f)
        f.close()
        return data

info = readJson("info.json")


class TextAdventure(commands.Cog):

    def __init__(self, client, info, adventure):
        self.client = client
        self.info = info
        self.adventure = adventure

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""text adventure cog ready!""")

    @commands.command()
    async def stop(self,ctx):
        print("stop")

    @commands.Cog.listener()
    async def on_message(self, message):
        print(f"test:{message}")


def setup(client):
    client.add_cog(TextAdventure(client, info))
