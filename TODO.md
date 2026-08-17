# PlopBot TODO

Task list from the code review of 2026-08-17. Ordered by priority, not by area.
Line references are accurate as of commit `97e0b4f`.

- **Critical** — security exposure, data loss, or a hard external deadline. Do these first.
- **High** — the bot is visibly broken or silently swallowing failures.
- **Medium** — real bugs with limited blast radius, plus infra/maintainability debt.
- **Low** — cleanup, style, and papercuts.

---

## Critical

- [x] **Stop `add_to_json` from leaking secrets and destroying config.** *(done 2026-08-17)*
      `add_to_json` is gone. The bot no longer writes to the config file at all — mutable runtime data now lives in `info/runtime_data.json`, which never contains credentials and is covered by the `*.json` rule in the root [.gitignore](.gitignore).
  - [x] ~~Write to the actual loaded config path~~ — superseded: the config file is now read-only to the bot. Writes go to `RUNTIME_DATA_FILE` via `append_runtime_data()`.
  - [x] Serialize to a temp file and atomically replace — `_write_json_atomic()` writes to a temp file in the same directory, `fsync`s, then `os.replace()`s; a failed write removes the temp file and leaves the destination untouched.
  - [x] Guard the missing-key case — `append_runtime_data()` uses `setdefault`, and a corrupt data file raises instead of being silently overwritten.
  - [x] Verify no `info.json` has already been committed — one was added in `e17d6ac` (2020-03-05) and removed in `60437a6`, but it predates credentials being stored in config: server IDs, nicknames, and channel lists only. **No token, DB block, or API keys. No rotation needed.**
  - [x] Uncomment `*.json` in [.gitignore](.gitignore) with a `!info/blank_info.json` negation — done; verified the template is still tracked and not ignored.
  - Also done as part of this: `.echo` removed entirely; startup presence now set from `VERSION_CODENAMES` (see below). `.add_scribble`/`.list_scribble` kept, now backed by the runtime data file, with a one-time migration of existing words out of `info.json`.
- [x] **Migrate off the OpenAI Assistants API — hard cutoff 2026-08-26.** *(done 2026-08-17)*
      Rewritten onto the Responses API with the Conversations API for state. Personalities now live in our own `discord_assistants` table (`AssistantDBManager`) instead of on OpenAI's servers, so they survive both the sunset and a bot restart. The run-polling state machine is gone — a turn is one awaited call.
      Refs: [OpenAI announcement](https://community.openai.com/t/assistants-api-beta-deprecation-august-26-2026-sunset/1354666), [migration guide](https://developers.openai.com/api/docs/guides/migrate-to-responses), [conversation state](https://developers.openai.com/api/docs/guides/conversation-state)
  - [x] Personalities persisted locally — `.cra` is now a pure DB insert with no API call at all.
  - [x] Thread state ported — one conversation per (guild, assistant), id stored in the DB, recreated transparently on a server-side 404.
  - [x] `retrieval` and `code_interpreter` dropped (never used — no files were ever uploaded).
  - [x] Model updated: reads `openai.text_gen_engine`, defaults to `gpt-5.6-luna` ($0.20/$1.20 per 1M). **Verify the ID against your account** — the bare `gpt-5.6` alias routes to Sol at 25× the price.
  - [x] Switched to `AsyncOpenAI`, which also closes the "sync OpenAI client blocks the event loop" item below.
  - [x] Tool/function calling dropped; `openAI_functions/*.json` deleted (`git rm`). Most handlers were stubs or broken.
  - [ ] **Not verified against the live API** — every test used fakes. Run `.cra`, `.ca`, `.forget`, `.dela` against the real account before the 26th, and confirm the `discord_assistants` table creates cleanly on your MySQL version.
  - [ ] Nothing was exported from the old Assistants account. If any personality there is worth keeping, dump it with `beta.assistants.list()` **before 2026-08-26** and re-create it with `.cra`.
- [x] **Replace the fake webhook authentication.** *(neutralized 2026-08-17 — disabled, not fixed)*
      The website webhook handler in [audioCog.py](cogs/audioCog.py) authenticated on the magic string `www.sodersjerna.com` in message content, so any member could type `www.sodersjerna.com:someone:play:airhorn` and puppet the bot into any voice channel. The block is commented out with a warning header; the site is still up but believed unused. **The vulnerability is gone because the code no longer runs — the underlying flaw was never repaired.**
      If it comes back, all three of these must be done first (they're repeated in the comment header above the dead code so they can't be missed):
  - [ ] Authenticate properly — check `message.webhook_id` and/or restrict to a dedicated channel + known author ID.
  - [ ] Guard `data[1]`/`data[2]`/`data[3]` — currently `IndexError` on any message starting with that prefix.
  - [ ] Handle `message.guild is None` (DMs) before `message.guild.members`.
- [x] **Fix `.say`: wrong signature + arbitrary file write.** *(done 2026-08-17)*
      TTS is now generated into a `BytesIO` and streamed straight to ffmpeg via `FFmpegPCMAudio(pipe=True)`. Nothing is written to disk at all, which removes the traversal, the soundboard pollution, and the concurrent-overwrite clash structurally rather than by validation.
  - [x] Changed to `async def say(self, ctx, *, text=None)` — the whole message is spoken, and a bare `.say` gets a usage hint instead of a `MissingRequiredArgument`.
  - [x] ~~Write TTS to a temp path outside `soundboard/`~~ — superseded: no file is written, so `verify_db()` can't promote TTS into the soundboard any more.
  - [x] Length limit now applies to the full text.
  - [x] Also fixed while here: `gTTS()` moved into `run_in_executor` (it does a network round trip), and `play()` is guarded against `ClientException` so a collision reports instead of failing silently.
  - Behaviour change: `.play say` no longer replays the last TTS, because no `say.mp3` is produced. (That file was already gone from `soundboard/` before this change — not deleted by this work.)
- [x] **A database outage silently kills every command.** *(done 2026-08-17)*
      New `DatabaseUnavailableError` replaces the `AttributeError` on a `None` cursor, the connection is re-established lazily on first use, and `on_command_error` reports the outage to whoever ran the command.
  - [x] `connect()` now raises `DatabaseUnavailableError` instead of logging a warning and leaving a half-dead manager. It also clears `db`/`my_cursor` so state is never inconsistent, and exposes a `connected` property.
  - [x] `_execute_with_reconnect()` calls `_ensure_connection()` first, so a manager that started with no database reconnects on first use rather than blowing up.
  - [x] **Deviation from the plan below:** startup does *not* fail fast. The bot no longer needs the database to run — soundboard, TTS and YouTube all work without it — so a dead database logs a prominent error and the bot starts anyway, retrying on use. The original complaint (a bare `AttributeError` at startup) is fixed either way. Table creation moved into `connect()`, so a table missed while the server was down is created as soon as it comes back.
  - [x] Policy decided: **fail open.** `ALLOW_COMMANDS_WHEN_DB_UNAVAILABLE = True` in [adminCog.py](cogs/adminCog.py) — an unreachable ban list lets commands through rather than locking everyone out of a soundboard. Flip the constant to fail closed.

---

## High

- [x] **Add an `on_command_error` handler** in [BotHead.py](BotHead.py). *(done 2026-08-17, as part of the database outage fix — the two are the same defect)* Handles `CommandNotFound` and `CheckFailure` silently (the checks already explain themselves), `NoPrivateMessage`, `CommandOnCooldown` with the retry time, `UserInputError` with a `.help` hint, `DatabaseUnavailableError` with its own message, `Forbidden` logged rather than shouted, and anything else logged with a full traceback plus a plain apology to the user. The handler is itself wrapped so it can never raise.
      Note the branch order matters: `NoPrivateMessage` subclasses `CheckFailure`, so it must be matched before the silent `CheckFailure` return — verified in test, not assumed.
- [ ] **Don't let one bad cog kill the bot.** [BotHead.py:32-34](BotHead.py#L32-L34) loads extensions with no `try`/`except`. A config missing the `twitter` or `openai` section `KeyError`s in [twitterCog.py:27](cogs/twitterCog.py#L27) / [openAiCog.py:107](cogs/openAiCog.py#L107) and the bot never starts. Optional features should degrade.
- [ ] **Fix the three broken permission checks** — replace all of them with the existing, correct `@is_admin()` / `@not_banned()` decorators from [adminCog.py](cogs/adminCog.py#L10-L72).
  - [ ] [audioCog.py:300](cogs/audioCog.py#L300) — `ctx.author not in settings.info_json["blacklist"]` compares a `Member` to a list of strings. Always true. Also `KeyError`s on configs built from the README sample, which has no `blacklist` key.
  - [ ] [openAiCog.py:406](cogs/openAiCog.py#L406), [openAiCog.py:426](cogs/openAiCog.py#L426) — same comparison bug, always **false**, so `.openai_ban` / `.openai_unban` can never be used by anyone. Both are also missing `@is_admin()`. (Left as-is through the migration — the working `@not_banned()` ban system already covers this, so consider deleting both commands and the file-based blacklist outright.)
  - [ ] [openAiCog.py:407](cogs/openAiCog.py#L407) — stores `str(user)` of a `*args` **tuple** (`"('@bob',)"`) while [openAiCog.py:53](cogs/openAiCog.py#L53) looks up `str(ctx.author)` (`"bob"`). The blacklist could never match even if reachable.
- [ ] **Blocking I/O on the event loop** — the biggest structural problem. One loop; every sync call blocks heartbeats and risks disconnects. ([audioCog.py:177-178](cogs/audioCog.py#L177-L178) already does this right with `run_in_executor` — follow that pattern.)
  - [ ] [voiceCog.py:101-120](cogs/voiceCog.py#L101-L120) — `time.sleep(5)` in a poll loop freezes the **entire bot for up to 180 seconds**. Worst offender.
  - [ ] [voiceCog.py:33,66,86,102,129](cogs/voiceCog.py#L33) — synchronous `requests` → `aiohttp`.
  - [ ] [adminCog.py:59](cogs/adminCog.py#L59) — sync MySQL query on every command invocation. Cache ban lookups in memory with invalidation on `.ban`/`.unban`.
  - [x] ~~[audioCog.py](cogs/audioCog.py) — `gTTS().save()` (network + file write)~~ — done 2026-08-17: generation moved into `run_in_executor`, and there is no file write left to block on.
  - [x] ~~[openAiCog.py](cogs/openAiCog.py) — sync `OpenAI` client; `.chat_assistant` polls up to 60s~~ — done 2026-08-17: now `AsyncOpenAI`, and the polling loop no longer exists.
  - [ ] `wget.download()` in `gen_img` / `edit_img` ([openAiCog.py](cogs/openAiCog.py)) — still blocking, still the unmaintained-since-2015 `wget` package. Untouched by the Assistants migration.
  - [ ] [audioCog.py:577](cogs/audioCog.py#L577) — `verify_db()` inside a `tasks.loop`.
- [ ] **Bound user input — current DoS vectors.**
  - [ ] [gameCog.py:137](cogs/gameCog.py#L137) — `.roll 999999999 1000000` builds a multi-MB string, then fails Discord's 2000-char limit. Cap `sides` and `times`.
  - [ ] [audioCog.py:149-195](cogs/audioCog.py#L149-L195) — unlimited `.mp3` uploads from any user: no size cap, no rate limit, no permission check. Fills the disk.
  - [ ] `.youtube` / `.stream` — no duration or filesize limit; downloads only cleaned up every 24h ([audioCog.py:570](cogs/audioCog.py#L570)).
- [ ] **Crash fixes.**
  - [ ] [gameCog.py:89](cogs/gameCog.py#L89) — `ctx.author.voice.channel` `AttributeError`s when the caller isn't in voice; the `if voice is not None` guard on line 91 is unreachable. `.teams` always crashes for the case it tries to handle.
  - [ ] [audioCog.py:364-375](cogs/audioCog.py#L364-L375) — `.stream` is missing from the `before_invoke` chain at [audioCog.py:552-554](cogs/audioCog.py#L552-L554), so `ctx.voice_client.play()` is `None.play()` when not connected.
  - [ ] [generalCog.py:32](cogs/generalCog.py#L32) — `self.change_status.start()` in `on_ready`, which re-fires on every reconnect → `RuntimeError: Task is already launched`. Move to `cog_load` or guard with `is_running()`.
  - [ ] [audioCog.py:175](cogs/audioCog.py#L175) — saves to `./soundboard/raw/`, which nothing creates (absent from the Dockerfile `mkdir`, and `soundboard/` is `.dockerignore`d). Fresh deploys `FileNotFoundError` on the first upload.
  - [ ] [audioCog.py:181](cogs/audioCog.py#L181) — `audio_json['streams'][0]['duration']` `KeyError`s when ffprobe reports no stream duration.
  - [ ] `.edit_img` — the `response['data'][0]['url']` subscript was fixed to attribute access during the migration, but the command is still suspect: `create_variation` ignores the user's prompt entirely, `dall-e-3` never supported variations, and it writes to a fixed `temp.png` shared across concurrent users. Needs a rewrite onto a current image model, or deletion.
  - [ ] [generalCog.py:136](cogs/generalCog.py#L136) — unguarded `info_json["welcome_channels"]`. Audit all remaining direct `info_json[...]` indexing and move to `.get()` with defaults, as the newer code does.
- [ ] **Implement the environment-variable config that [.env.example](.env.example) advertises.** Nothing in the codebase reads env vars (`grep os.environ` → zero hits) and `docker-compose.yml` never maps them, so `DISCORD_TOKEN` / `DB_PASSWORD` are silently ignored. Either implement it (preferred — secrets in a mounted JSON file is the weakest part of the deployment story) or delete the file.

---

## Medium

### Silently-wrong behavior

- [x] ~~`if e.code == 400:` then `if e.code == "content_policy_violation":` — the outer test never passes~~ — done 2026-08-17: the dead outer check is gone, policy violations now report properly.
- [x] ~~`play_soundboard` never appends to `outputs`; `audio.play(ctx, sound)` invokes a `Command` object unawaited~~ — moot as of 2026-08-17: `handle_tool_call` deleted with the tool support. Re-read this note if tools are ever reintroduced.
- [x] ~~`threads.create()` runs on every `.chat_assistant` call~~ — done 2026-08-17: one conversation per (guild, assistant), created once and stored in the DB. Conversations now actually accumulate context; `.forget` clears one deliberately.
- [ ] [settings.py:273-276](settings.py#L273-L276) — `verify_db` compares lowercased DB filenames against original-case `os.listdir` names. Any file with an uppercase letter is deleted and re-added on every maintenance cycle, forever.
- [ ] [audioCog.py:155](cogs/audioCog.py#L155) vs [audioCog.py:170](cogs/audioCog.py#L170) — the duplicate check normalizes with `.replace(' ','')` but the save path also strips `_`. `my_clip.mp3` passes the check, then overwrites `myclip.mp3`.
- [ ] [audioCog.py:493](cogs/audioCog.py#L493) — `self.volume` is cog-global; a volume change in one guild applies to all of them.
- [ ] [generalCog.py:112](cogs/generalCog.py#L112) — `message.content = message.content.strip().lower()` mutates the shared `Message` object every other listener and `ctx` holds. It only avoids breaking command parsing today because `StringView` is built before this task runs — a load-order coincidence. Anything reading `ctx.message.content` later gets mangled input (e.g. case-sensitive YouTube IDs).
- [ ] [voiceCog.py:82](cogs/voiceCog.py#L82) — `''.join(text)` joins words with no separator: "hello world" → "helloworld".
- [ ] [voiceCog.py:63](cogs/voiceCog.py#L63) — `open()` handle passed to `requests` and never closed.
- [ ] [audioCog.py:283-284](cogs/audioCog.py#L283-L284) — bare `except Exception` in `play_clip` logs a warning and tells the user nothing.
- [ ] Hardcoded voice API address `192.168.1.230:8000` in five places in [voiceCog.py](cogs/voiceCog.py#L33) — move to config (`.env.example` already reserves `VOICE_API_URL`).
- [ ] Add `@commands.guild_only()` to commands that assume `ctx.guild` (`.youtube`, `.teams`, `.play`, …) — they `AttributeError` in DMs.

### Infrastructure

- [ ] **Pin dependencies.** All `>=`, no lockfile — `yt-dlp >= 2023.3.4` resolves to whatever is newest.
  - [ ] Remove `argparse >= 1.1` from [requirements.txt](requirements.txt) — it installs a 2015 PyPI package that shadows the stdlib module.
  - [ ] Remove `markovify` (unused since `97e0b4f`) and `pydub` (unused).
  - [ ] Remove the stray bare `install` line in [dev-requirements.txt](dev-requirements.txt), which installs a random package.
- [x] **Revive CI** *(done 2026-08-17)* — every action upgraded to a ref verified to resolve against the GitHub API: `checkout@v7`, `setup-python@v7`, `codeql-action@v4`, `setup-qemu@v4`, `setup-buildx@v4`, `login@v4`, `metadata@v6`, `build-push@v7`. Python bumped 3.8 → 3.11 to match the Dockerfile (3.8 could not even import `settings.py`, which uses builtin generics). CodeQL `Autobuild` replaced with `build-mode: none`, which is what interpreted languages require. Added pip caching, gha build caching, `concurrency` cancellation, a `permissions: contents: read` block, linting on pull requests, and a pytest step that activates by itself once a `tests/` directory exists.
  - [x] Docker Hub publishing now requires the lint job to pass (`needs: build`) and is restricted to pushes on `plop91/PlopBot`, so forks and PRs no longer attempt a login they have no secrets for. Per-branch image tags are unchanged.
  - [ ] Advisory lint reports 49 pre-existing nits (`C901`, `E402`, `F401`, `F841`, `E501`…). None are new, and the blocking pass (`E9,F63,F7,F82`) is clean, verified locally against the exact CI command. Several overlap with items in the Low section below.
- [ ] **Add tests.** Zero exist. Start with the pure logic where the subtle bugs live: `parse_ban_duration`, `verify_db` diffing, the embed pagination in [audioCog.py:301-329](cogs/audioCog.py#L301-L329).
- [ ] **Logging.**
  - [ ] `logging.FileHandler` with no rotation ([settings.py:39-40](settings.py#L39-L40)) → use `RotatingFileHandler`.
  - [ ] [generalCog.py:113](cogs/generalCog.py#L113) logs the full content of every message in every channel at INFO — an ever-growing plaintext archive of the server's chat on disk. Reconcile against [DISCLAIMER.md](DISCLAIMER.md) or drop to content-free logging.
- [ ] **Database layer.**
  - [ ] Consolidate the three separate MySQL connections to the same database ([settings.py:80-103](settings.py#L80-L103)) onto one.
  - [ ] Set `autocommit=True` — read paths never commit, so a `SELECT` snapshot can go stale indefinitely under REPEATABLE READ if anything modifies the DB out-of-band.
  - [ ] [settings.py:236](settings.py#L236) — `SELECT *` with positional column access is fragile; name the columns.
- [ ] **Docker.**
  - [ ] `.hash` ([adminCog.py:105](cogs/adminCog.py#L105)) can never work: [.dockerignore](.dockerignore) excludes `.git`, so it always reports "Is this a git repository?". Bake the SHA in as a build arg/label.
  - [ ] Bind-mounted `./soundboard` and `./info` keep host ownership, but the image runs as uid 1000 (`botuser`) — uploads and blacklist writes fail unless the host dirs match.
  - [ ] `openai_blacklist.json` is written to `/app`, which isn't a volume — the blacklist is lost on every container recreate.
  - [ ] Add a `HEALTHCHECK`.
- [ ] **Delete dead code.** All of it is in git history.
  - [ ] [db/openai_database_manager.py](db/openai_database_manager.py) — 283 lines, over half the methods are `pass`. Now genuinely orphaned: the import and the commented-out instantiation were removed in the migration, so this is a clean `git rm`. Note `AssistantDBManager` in settings.py supersedes part of what it planned.
  - [ ] [BotHead.py:36-86](BotHead.py#L36-L86) — 50 lines of commented-out cog management.
- [x] ~~Resolve the `openAI_functions/*.json` state~~ — done 2026-08-17: deletion staged with `git rm --cached`, directory removed, and the `os.listdir` that crashed on it is gone.
- [ ] **Narrow `Intents.all()`** ([BotHead.py:97](BotHead.py#L97)) to only the intents actually used.
- [x] **Fix README drift** *(done 2026-08-17)* — the duplicated config blob is gone; README now points at [info/blank_info.json](info/blank_info.json) with a table of the required keys, a warning about keeping the real config out of git, and a note that the bot runs without a database. CLAUDE.md updated in the same pass: database architecture, the no-disk-writes TTS invariant, the nonexistent `database_scripts/` directory, and the Development Notes entry that was telling contributors to hand-roll the broken admin check.

---

## Low

- [ ] [settings.py:265](settings.py#L265) — `db_file_set` computed and never used.
- [ ] [audioCog.py:308,310,328](cogs/audioCog.py#L308) — `DEBUG: SENDING REAL MESSAGE` style logs left in production paths.
- [ ] [audioCog.py:301-329](cogs/audioCog.py#L301-L329) — the `.play` embed pagination is hard to follow and only accidentally respects Discord's field limits. Rewrite against the 1024-char/25-field/6000-char rules.
- [ ] [audioCog.py:233,255,259](cogs/audioCog.py#L233) — the `TODO: this is a garbage hack` string munging in `play_clip`; keep the display name alongside the path instead of round-tripping through `replace()`.
- [ ] [audioCog.py:9](cogs/audioCog.py#L9) — `from discord.utils import get` is shadowed by the `get` command at [audioCog.py:505](cogs/audioCog.py#L505). Works, but confusing; alias the import.
- [ ] [audioCog.py:5](cogs/audioCog.py#L5) — unused `from asyncio import sleep`. Sweep unused imports repo-wide.
- [ ] [settings.py:5-16](settings.py#L5-L16) — `VERSION` is declared above the imports; move below (PEP 8).
- [ ] [audioCog.py:513-521](cogs/audioCog.py#L513-L521) — the `.get` path check uses a `startswith` prefix comparison, which would match a sibling `soundboard_other/` directory. The separate `..` check saves it today; use `os.path.commonpath` instead.
- [ ] [gameCog.py:105-110](cogs/gameCog.py#L105-L110) — `teams` mutates `iteams` inside a loop over `range(1, iteams + 1)`. It happens to produce correct sizes; rewrite it so that isn't load-bearing.
- [ ] Remove leftover untracked `markov/` and `texts/` directories now that markov generation is gone.
- [ ] [voiceCog.py:11](cogs/voiceCog.py#L11) — `Voices` has no `__init__`, so `Voices(client)` never stores `client`. Harmless today (it's unused), but inconsistent with every other cog.
- [x] ~~stray `global logger` at module scope~~ — removed 2026-08-17.
- [ ] `.repeat` ([generalCog.py:156](cogs/generalCog.py#L156)) has a sane cap but no cooldown — easy spam vector.
- [ ] Every `VERSION` bump needs a matching entry in `VERSION_CODENAMES` ([settings.py:5-16](settings.py#L5-L16)). Unmapped versions fall back to `"unreleased"` and log a warning at startup rather than failing, so it's easy to miss — consider adding it to the release checklist.

---

## Suggested batching

1. **PR 1 — secrets + visibility:** critical `add_to_json` fix, `on_command_error`, the three broken permission checks. Small, self-contained, and makes everything else diagnosable.
2. **PR 2 — OpenAI:** Assistants migration or clean disable. Deadline-driven.
3. **PR 3 — input handling:** `.say` signature/traversal, webhook auth, input bounds.
4. **PR 4 — event loop:** blocking I/O sweep, starting with `voiceCog`'s `time.sleep` and the per-command DB query.
5. **PR 5 — housekeeping:** pin deps, revive CI, delete dead code, first tests.
