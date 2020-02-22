import discord


def readToken():
    with open("token.txt", "r") as f:
        temp_token = f.readlines()
        return temp_token[0].strip()


token = readToken()
client = discord.Client()

servers = {
    "plop91": 680431962149879829
}

valid_users = [
    "plop91#7096"
]
boolers = [
    "BobtheCop",
    "killuhand",
    "cstrobel",
    "Volum",
    "xjsc16x"
]
testers = [
    "plop91",
    "plop9100"
]
command_channels = [
    "bot_test"
]

welcome_chanels = [
    "general"
]


@client.event
async def on_member_join(member):
    for channel in member.guild.channels:
        if str(channel) in welcome_chanels:
            await channel.send(f"""Who are you{member.mention}?""")


@client.event
async def on_ready():
    print(f"""Logged on as {client.user}!""")


@client.event
async def on_message(message):
    _id = message.guild
    print(f"""Message from {message.author}: {message.content}""")
    if message.content == "hey":
        await message.channel.send("Hi")
    elif message.content == "bool":
        await message.channel.send("To bool or not to bool this is the question")
    elif message.content == "to bool":
        for name in testers:
            member = discord.utils.get(message.guild.members, name=name)
            await message.channel.send(f"""call to bool {member.mention}?""")
    elif message.content.find("fuck") != -1 and message.content.find("you") != -1 and message.content.find(
            "jon") != -1 and str(message.author) != "plop91#8989":
        await message.channel.send("yeah fuck you jon!!!!")
    if str(message.channel) in command_channels:
        if str(message.author) in valid_users:
            if message.content == "!stop":
                await client.logout()
            elif message.content == "!users":
                await message.channel.send(f"""number of members {_id.member_count}""")
        else:
            print(f"""User: {message.author} tried to do command {message.content}, in channel {message.channel}""")


client.run(token)
