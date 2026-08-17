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
- `soundboard_database`: MySQL connection details (all four database managers share these credentials)
- `openai.apikey`: OpenAI API key for AI features
- `admins`: List of admin user IDs

**Optional configuration:**

- `openai.text_gen_engine`: Chat model for the assistant commands (defaults to `DEFAULT_CHAT_MODEL` in openAiCog.py)
- `twitter`: Twitter API credentials
- `command_channels`: Channels where bot commands are allowed
- `welcome_channels` and `welcome_messages`: Welcome message configuration
- `announcement_channels` and `github_url`: Used by the version update announcement
- `status`: Bot status messages the hourly rotation picks from

**The bot never writes to this file.** Anything mutable it needs to persist goes in `info/runtime_data.json`
instead, so a runtime write can never touch the file holding the token. See `append_runtime_data()` /
`load_runtime_data()` in settings.py.

## Architecture

### Core Structure

**BotHead.py**: Main entry point. The `PlopBot` class extends `commands.Bot` and automatically loads all cogs from the `cogs/` directory during `setup_hook()`. It also defines `on_command_error`, which is the only thing standing between a failing command and complete silence — if you add a new failure mode, give it a branch there.

**settings.py**: Global settings module that:

- Initializes logging (creates `bot.log` and `discord.log`)
- Loads the `info.json` configuration file (read-only; see Configuration above)
- Creates the database managers and holds them on a `Settings` dataclass
- Provides module-level access to `info_json`, `token`, `logger`, `soundboard_db`, `ban_db`, `version_db`, `assistant_db` (via `__getattr__`, which raises if `init()` has not run)
- Defines `VERSION`, `VERSION_CODENAMES` (the startup presence codename), `parse_ban_duration()`, the runtime data helpers, and `DatabaseUnavailableError`

**Command prefix**: All bot commands use the `.` prefix (e.g., `.play`, `.help`)

### Cog System

The bot uses discord.py's cog system to organize features into separate modules in the `cogs/` directory:

- **audioCog.py**: YouTube audio playback, soundboard management, TTS (Google TTS)
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

All managers subclass **BaseDBManager** (settings.py), which owns connection handling:

- `connect()` raises `DatabaseUnavailableError` on failure rather than leaving a `None` cursor behind
- `_execute_with_reconnect()` reconnects lazily, so a manager constructed while MySQL was down recovers on first use
- `_create_table()` runs on every successful connect, so a table missed during an outage is created when the server returns
- **The bot starts without a database.** Soundboard, TTS and YouTube do not need one. Anything that does need one must either catch `DatabaseUnavailableError` or let it reach `on_command_error`, which reports it to the user.

The four managers, all sharing the `soundboard_database` credentials:

- **SoundboardDBManager** — `discord_soundboard` (filename, name, date_added). `verify_db()` syncs filesystem clips with database rows.
- **BanDBManager** — `discord_bans`. Backs the `@not_banned()` check, which runs on nearly every command.
- **VersionDBManager** — `discord_version`, single row. Tracks which version has already been announced.
- **AssistantDBManager** — `discord_assistants` (guild_id, name, instructions, conversation_id). Holds the AI personalities that used to live on OpenAI's servers.

**OpenAIDatabaseManager** (db/openai_database_manager.py) is dead code — nothing imports it, and `AssistantDBManager` supersedes the part of it that was ever used. Delete it rather than extending it.

### Audio System

**YTDLSource** (in audioCog.py):

- Wraps yt-dlp for YouTube audio extraction
- Uses `discord.PCMVolumeTransformer` for volume control
- Downloads to `youtube/` directory with restrictive filenames

**Soundboard**:

- MP3 files stored in `soundboard/` directory
- Filename mapping built at cog initialization (lowercase, .mp3 extension stripped)
- Database tracks all soundboard entries with unique names

**TTS**: Uses Google Text-to-Speech (gTTS). `.say` renders into a `BytesIO` and streams it to
`FFmpegPCMAudio(pipe=True)` — **it deliberately writes nothing to disk.** Writing TTS into `soundboard/`
is what previously allowed path traversal via the filename argument, let `verify_db()` promote throwaway
speech into permanent clips, and made two guilds overwrite each other's file mid-playback. Keep it in memory.
gTTS itself is a blocking network call, so it runs through `run_in_executor`.

### OpenAI Integration

The OpenAI cog supports:

- Image generation via DALL-E
- Named per-guild "assistants": a personality (system prompt) you can hold a running conversation with

Assistants are **not** OpenAI Assistant objects. The Assistants API was removed on 2026-08-26, so
personalities live in our own `discord_assistants` table (see `AssistantDBManager` in settings.py) and the
instructions are passed to `responses.create()` on every message. Conversation history is held by OpenAI
via the Conversations API; the `conversation_id` is stored alongside the personality so a conversation
survives a restart. If OpenAI no longer has the conversation, the cog silently starts a new one.

The cog uses `AsyncOpenAI` — every call must be awaited. The chat model is read from
`openai.text_gen_engine` in info.json, defaulting to `DEFAULT_CHAT_MODEL` in openAiCog.py.

Function/tool calling was dropped during the migration. If it is reintroduced, note that the Responses API
uses a flatter tool schema than the old Assistants format (`{"type": "function", "name": ..., "parameters": ...}`
with no nested `function` key) and that tool calls and outputs are separate items paired by `call_id`.

### Voice Cloning System

The voice cog communicates with an external voice cloning API:

- `.add_voice <name>`: Creates a new voice profile
- `.add_clip <name>`: Uploads training clips for a voice
- `.make_clip <name> <text>`: Generates audio using the trained voice

## Database Migrations

There is no migration tooling in this repo. (Older docs referenced a `database_scripts/` directory and an
`apply_db_migration.py`; neither exists.)

Tables are created on demand: each manager's `_create_table()` runs `CREATE TABLE IF NOT EXISTS` on every
successful connect. That covers new installs and new tables, but **it does not alter existing tables** — if
you change a column on a table that is already deployed, you have to apply that by hand against the database.

## Persistent Directories

The following directories should be volume-mounted in Docker or persisted:

- `soundboard/`: MP3 files for the soundboard
- `info/`: Configuration JSON files, plus `runtime_data.json` (scribble words). Losing this directory loses
  both the bot's credentials and anything it has persisted.
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
- openai >= 2.8.0 (OpenAI API — the Conversations API needs a recent SDK)
- gtts >= 2.5.1 (Text-to-speech)
- ffmpeg-python >= 0.2.0 (Audio processing)
- tweepy >= 4.14.0 (Twitter API)

System dependency: **ffmpeg** must be installed for audio playback.

## Development Notes

- **Use the check decorators in `cogs/adminCog.py`: `@is_admin()`, `@not_banned()`, `@in_command_channel()`.**
  Do not hand-roll `if ctx.author in settings.info_json["admins"]` — `ctx.author` is a `Member` and the config
  holds strings, so that comparison is always false. The same mistake in `audioCog` was always *true*. Several
  such checks are still in the codebase and are listed in TODO.md.
- Add `@commands.guild_only()` to anything touching `ctx.guild`, or it raises in DMs
- Database operations go through `BaseDBManager`; reconnection is already handled, but callers must expect
  `DatabaseUnavailableError`
- **Nothing blocking on the event loop.** Network and disk calls (`requests`, `gTTS`, `ffmpeg.probe`, the MySQL
  driver, `wget`) freeze the entire bot, including its heartbeat. Use `async` libraries or `run_in_executor`.
  There are known offenders left — see the High section of TODO.md.
- All file paths should be relative to the working directory (`/app` in Docker)
- OpenAI blacklist is stored in `openai_blacklist.json` at the root. It is broken (see TODO.md) and the
  `@not_banned()` ban system supersedes it.
- **TODO.md tracks known defects by priority.** Check it before assuming something odd is intentional.
