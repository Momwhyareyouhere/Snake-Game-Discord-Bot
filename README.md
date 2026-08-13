# Snake-Game-Discord-Bot

THIS REPOSITORY IS STILL ON WORKING BUT YOU CAN USE IT

## Installation

```
git clone https://github.com/Momwhyareyouhere/Snake-Game-Discord-Bot.git
cd Snake-Game-Discord-Bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python bot.py
```

On Windows, use `.venv\Scripts\python` and `.venv\Scripts\pip` instead.

## Config

To get config.txt go to this website: https://momwhyareyouhere.github.io/Snake_game_setup

Place `config.txt` in the project folder before running the bot. It must contain `bot_token` and `owner_id`, plus the game options `show_score`, `game_over_screen`, `add_border`, `hit_border_game_over`, and `field_size`.

## Commands

- `!snake_game` - start a game (control with the arrow reactions)
- `!pause` - pause your game (your message is deleted, no reply on success)
- `!continue` - resume your game (your message is deleted, no reply on success)
- `!exit` - end your game (your message is deleted, no reply on success)
- `!leaderboard` - show the top 10 best scores (saved in scores.json)

## Owner commands

- `!liveview <username or discord id>` - spectate a running game in real time (works in a channel or via DM). The live view updates, pauses, and stops together with the player's game.
- `!blacklist <username or discord id>` - block a user from playing. Any game they are currently playing is ended.
- `!whitelist <username or discord id>` - remove a user from the blacklist.

Note: the blacklist is stored in memory and resets when the bot restarts.

It will gonna be comming next updates new commands for the owner and a new system
