# PlopBot

<img src="https://img.shields.io/badge/Discord-5865F2?style=for-the-badge&logo=discord&logoColor=white" /><img src="https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue" /><img src="https://img.shields.io/badge/Docker-2CA5E0?style=for-the-badge&logo=docker&logoColor=white" /><img src="https://img.shields.io/badge/MariaDB-003545?style=for-the-badge&logo=mariadb&logoColor=white" /><img src="https://img.shields.io/badge/ChatGPT-74aa9c?style=for-the-badge&logo=openai&logoColor=white" /><img src="https://img.shields.io/badge/PyCharm-000000.svg?&style=for-the-badge&logo=PyCharm&logoColor=white" />


A Discord bot with an integrated soundboard and text to speech capabilities written in Python using discord.py.

## Setup

Clone the repository and make a file named "info.json" containing the following with bold typed words replaced with relevant information.

```
{
  "token": "DISCORD_BOT_TOKEN",
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
  "openai": {
    "apikey": "OPENAI_API_KEY",
    "text_gen_engine": "text-davinci-003"
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
```

## Run:

### Docker:

Build and run the bot making sure you mount the correct location for your source.

```
docker build -t "discord" . && docker run -v PATH_TO_SOURCE_DIR:/usr/src/app/ --detach --name DiscordBot "discord"
```

### Python:

Run the bot. If your json file uses a name other than json.info, you can specify it using --json. You can also override any of the database connection options by specifying them, otherwise they will be taken from the info.json file.

```
python3 BotHead.py  [-h] [--json JSON] 
                    [--db_host DB_HOST] 
                    [--db_username DB_USERNAME] 
                    [--db_password DB_PASSWORD]
                    [--db_name DB_NAME]
```