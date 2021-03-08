# DiscordBot (PlopBot)

A general purpose discord bot written in Python using the discord.py library.

The bot is intended to be deployed in a docker container but can be run using a python3 interpreter.

## Setup

Clone the repository and make a file named "info.json" containing the following with bold typed words replaced with relevant information.

    {
      "live_token": "DISCORD_BOT_TOKEN",
      "soundboard_database": {
        "server_address": "DATABASE_ADDRESS",
        "username": "DATABASE_USERNAME",
        "password": "DATABASE_PASSWORD",
        "database": "DATABASE_DATABASE"
      },
      "twitter": {
        "apikey": "TWITTER_API_KEY",
        "apisecret": "TWITTER_API_SECRET",
        "accesstoken": "TWITTER_ACCESS_TOKEN",
        "accesstokensecret": "TWITTER_TOKEN_SECRET"
      },
      "admins": [
        "ADMIN1",
        "ADMIN2"
      ],
      "command_channels": [
        "bot_commands"
      ],
      "welcome_channels": [
        "general"
      ],
      "welcome_messages": [
        "hello"
      ],
      "status": [
        "status1",
        "status2"
      ]
    }

## Run:

### Docker:
Build and run the bot making sure you mount the correct location for your source.
    
    docker build -t "discord" . && docker run -v PATH_TO_SOURCE_DIR:/usr/src/app/ --detach --name DiscordBot "discord"

### Python:
Runs the bot, the boolean is for testing and will be replaced in future builds with the choice of json name.
    
    python3 BotHead.py false