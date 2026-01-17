# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PlopBot is a Discord bot with soundboard and text-to-speech capabilities, built using discord.py. It features audio playback from YouTube, OpenAI integration for text/image generation, voice cloning, and Twitter integration.

## Running the Bot

### Docker (Recommended)

```bash
# Build and start with docker-compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop the bot
docker-compose down

# Build directly with Docker
docker build -t plopbot:latest .

# Run with volume mounts
docker run -d \
  --name plopbot \
  --restart unless-stopped \
  -v $(pwd)/soundboard:/app/soundboard \
  -v $(pwd)/info:/app/info \
  -v $(pwd)/markov:/app/markov \
  -v $(pwd)/voices:/app/voices \
  plopbot:latest
```

### Python (Development)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the bot (default uses info/info.json)
python3 BotHead.py

# Run with custom config or database overrides
python3 BotHead.py --json info/testinginfo.json \
  --db_host localhost \
  --db_username myuser \
  --db_password mypass \
  --db_name mydb
```

## Configuration

The bot requires an `info.json` file (or custom JSON specified via `--json`). Use `info/blank_info.json` as a template:

**Required configuration:**
- `token`: Discord bot token
- `soundboard_database`: MySQL connection details for soundboard storage
- `openai.apikey`: OpenAI API key for AI features
- `admins`: List of admin user IDs

**Optional configuration:**
- `twitter`: Twitter API credentials
- `command_channels`: Channels where bot commands are allowed
- `welcome_channels` and `welcome_messages`: Welcome message configuration
- `status`: Bot status messages

## Architecture

### Core Structure

**BotHead.py**: Main entry point. The `PlopBot` class extends `commands.Bot` and automatically loads all cogs from the `cogs/` directory during `setup_hook()`.

**settings.py**: Global settings module that:
- Initializes logging (creates `bot.log` and `discord.log`)
- Loads the `info.json` configuration file
- Creates the `SoundboardDBManager` instance for MySQL database operations
- Provides global variables: `info_json`, `token`, `logger`, `soundboard_db`

**Command prefix**: All bot commands use the `.` prefix (e.g., `.play`, `.help`)

### Cog System

The bot uses discord.py's cog system to organize features into separate modules in the `cogs/` directory:

- **audioCog.py**: YouTube audio playback, soundboard management, TTS (Google TTS), Markov chain text generation
- **voiceCog.py**: Voice cloning system integration (communicates with external API at 192.168.1.230:8000)
- **openAiCog.py**: OpenAI text/image generation, assistant management, thread-based conversations
- **twitterCog.py**: Twitter integration via Tweepy
- **adminCog.py**: Admin-only commands
- **gameCog.py**: Game-related commands
- **generalCog.py**: General utility commands

Each cog is automatically loaded at startup. All cogs should follow the pattern:
```python
class MyCog(commands.Cog):
    def __init__(self, client):
        self.client = client

    @commands.Cog.listener()
    async def on_ready(self):
        settings.logger.info(f"my cog ready!")

async def setup(client):
    await client.add_cog(MyCog(client))
```

### Database Architecture

**SoundboardDBManager** (in settings.py):
- Manages `discord_soundboard` table (columns: filename VARCHAR(255), name VARCHAR(255), date_added)
- Implements automatic reconnection on `CR_SERVER_GONE_ERROR`
- All database operations should use the global `settings.soundboard_db` instance
- The `verify_db()` method syncs filesystem soundboard files with database entries

**OpenAIDatabaseManager** (in db/openai_database_manager.py):
- Separate database manager for OpenAI feature persistence
- Currently commented out in openAiCog.py but structure exists for user tracking and blacklisting

### Audio System

**YTDLSource** (in audioCog.py):
- Wraps yt-dlp for YouTube audio extraction
- Uses `discord.PCMVolumeTransformer` for volume control
- Downloads to `youtube/` directory with restrictive filenames

**Soundboard**:
- MP3 files stored in `soundboard/` directory
- Filename mapping built at cog initialization (lowercase, .mp3 extension stripped)
- Database tracks all soundboard entries with unique names

**TTS**: Uses Google Text-to-Speech (gTTS) library for voice generation

### OpenAI Integration

The OpenAI cog supports:
- Image generation via DALL-E
- Text generation and chat completions
- OpenAI Assistants API with thread management
- Function calling (definitions in `openAI_functions/*.json`)

Active assistants and threads are tracked per-user in `active_assistants` and `active_threads` dictionaries.

### Voice Cloning System

The voice cog communicates with an external voice cloning API:
- `.add_voice <name>`: Creates a new voice profile
- `.add_clip <name>`: Uploads training clips for a voice
- `.make_clip <name> <text>`: Generates audio using the trained voice

## Database Migrations

Database schema changes are managed in `database_scripts/`:
- SQL migration files define schema changes
- `apply_db_migration.py` provides Python-based migration application
- When modifying the soundboard table structure, update both the SQL and the migration script

## Persistent Directories

The following directories should be volume-mounted in Docker or persisted:
- `soundboard/`: MP3 files for the soundboard
- `info/`: Configuration JSON files
- `markov/`: Markov chain training data
- `voices/`: Voice cloning data
- `youtube/`: Downloaded YouTube audio (can be temporary)
- `temp/`: Temporary file storage

## Logging

The bot creates two log files:
- `bot.log`: All bot logging output (DEBUG level)
- `discord.log`: Discord.py library logs (INFO level)

Both logs also output to console. Use `settings.logger` for all bot logging.

## Dependencies

Key dependencies (see requirements.txt):
- discord.py >= 2.3.2
- mysql-connector-python >= 8.0.23
- yt-dlp >= 2023.3.4 (YouTube download)
- openai >= 1.12.0 (OpenAI API)
- gtts >= 2.5.1 (Text-to-speech)
- ffmpeg-python >= 0.2.0 (Audio processing)
- tweepy >= 4.14.0 (Twitter API)
- markovify >= 0.9.0 (Markov chains)

System dependency: **ffmpeg** must be installed for audio playback.

## Development Notes

- Admin checks should verify `ctx.author` against `settings.info_json["admins"]`
- Command channel restrictions check against `settings.info_json["command_channels"]`
- Database operations should handle `CR_SERVER_GONE_ERROR` and implement reconnection
- All file paths should be relative to the working directory (`/app` in Docker)
- OpenAI blacklist is stored in `openai_blacklist.json` at the root
