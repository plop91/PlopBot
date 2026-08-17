# PlopBot

A Discord bot with an integrated soundboard and text to speech capabilities written in Python using discord.py.

## Setup

Clone the repository, then copy [info/blank_info.json](info/blank_info.json) to `info/info.json` and fill in
the placeholder values:

```sh
cp info/blank_info.json info/info.json
```

At minimum you need:

| Key | What it is |
| --- | --- |
| `token` | Discord bot token |
| `soundboard_database` | MySQL host, username, password and database name |
| `admins` | Discord user IDs allowed to run admin commands |
| `openai.apikey` | Only needed for the image and assistant commands |

Everything else in the template is optional — Twitter credentials, welcome messages, the status rotation,
and the channels used for command restrictions and version announcements.

> **Keep `info/info.json` out of git.** It holds your bot token and database password. The root `.gitignore`
> excludes `*.json` everywhere except `info/blank_info.json`, so your real config is ignored by default —
> check with `git check-ignore -v info/info.json` if you are unsure. The bot itself never writes to this
> file; anything it needs to persist goes to `info/runtime_data.json`.

Requires **ffmpeg** on the host (already included in the Docker image), and MySQL for the ban, version and
assistant features. The bot will start without a reachable database — the soundboard, TTS and YouTube
playback all work regardless — and reconnects on its own once the database comes back.

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

Install the requirements, then run the bot. The config defaults to `info/info.json`; point `--json` at a
different file to override it. The database connection options can also be overridden individually, otherwise
they are taken from the config file.

```sh
pip install -r requirements.txt
```

```sh
python3 BotHead.py  [-h] [--json JSON] 
                    [--db_host DB_HOST] 
                    [--db_username DB_USERNAME] 
                    [--db_password DB_PASSWORD]
                    [--db_name DB_NAME]
```
