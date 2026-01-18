# PlopBot

A Discord bot with an integrated soundboard and text to speech capabilities written in Python using discord.py.

## Setup

Clone the repository and make a file named "info.json" containing the following with bold typed words replaced with relevant information.

```json
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

## Run

### Docker (Recommended)

**Using Docker Compose:**

```bash
# Build and start the bot
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down
```

**Using Docker directly:**

```bash
# Build the image
docker build -t plopbot:latest .

# Run the container with volume mounts for persistent data
docker run -d \
  --name plopbot \
  --restart unless-stopped \
  -v $(pwd)/soundboard:/app/soundboard \
  -v $(pwd)/info:/app/info \
  -v $(pwd)/voices:/app/voices \
  plopbot:latest
```

### Python

Run the bot. If your json file uses a name other than json.info, you can specify it using --json. You can also override any of the database connection options by specifying them, otherwise they will be taken from the info.json file.

```sh
python3 BotHead.py  [-h] [--json JSON] 
                    [--db_host DB_HOST] 
                    [--db_username DB_USERNAME] 
                    [--db_password DB_PASSWORD]
                    [--db_name DB_NAME]
```
