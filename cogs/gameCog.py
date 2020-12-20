import random
import discord
import datetime
from discord.ext import commands
from utility.tools import readJson

json = readJson("info.json")

HANGMAN_PICS = ['''
   +---+
       |
       |
       |
      ===''', '''
   +---+
   O   |
       |
       |
      ===''', '''
   +---+
   O   |
   |   |
       |
      ===''', '''
   +---+
   O   |
  /|   |
       |
      ===''', '''
   +---+
   O   |
  /|\\  |
       |
      ===''', '''
   +---+
   O   |
  /|\\  |
  /    |
      ===''', '''
   +---+
   O   |
  /|\\  |
  / \\  |
      ===''']


class game(commands.Cog):
    active_hangman = False
    hangman_word = ""
    hangman_hidden = ""
    hangman_guesses = ""
    hangman_wrong_guesses = 0

    def __init__(self, client, info):
        self.client = client
        self.info = info

    @commands.Cog.listener()
    async def on_ready(self):
        print(f"""{datetime.datetime.now()}: game cog ready!""")

    @commands.command()
    async def hangman(self, ctx, command):
        if command.lower() == "create":
            if self.active_hangman:
                await ctx.send("There is already an active game of hangman use 'end' to end the game before "
                               "starting a new one.")
                return
            else:
                with open('dictionary.txt', 'r') as file:
                    words = []
                    for line in file:
                        words.append(line)
                    self.hangman_word = random.choice(words)
                    self.hangman_hidden = ""
                    self.hangman_guesses = ""
                    for letter in self.hangman_word:
                        self.hangman_hidden += "- "

                embed_var = discord.Embed(title="Hangman", description="", color=0x00ff00)

                embed_var.add_field(name="real word:", value=self.hangman_word, inline=False)

                embed_var.add_field(name="Hidden word:", value=self.hangman_hidden, inline=False)

                embed_var.add_field(name="image:", value=HANGMAN_PICS[0], inline=False)

                await ctx.channel.send(embed=embed_var)

                print(self.hangman_hidden)

                self.active_hangman = True

                return

        if command.lower() == "end":
            self.active_hangman = False

        if self.active_hangman:
            if len(command) == 1:
                if command in self.hangman_word:
                    self.hangman_hidden += command
                    ###############################
                else:
                    self.hangman_guesses += command
            else:
                await ctx.send("A guess must be only one letter")

        else:
            await ctx.send("There is no active game use create to start a new game")


def setup(client):
    client.add_cog(game(client, json))
