import discord
from discord.ext import commands, tasks
import random
import os
import json

filename = 'config.txt'

if not os.path.isfile(filename):
    print("Please download config.txt and insert it into this folder: https://momwhyareyouhere.github.io/Snake_game_setup")
    exit(1)
else:
    print(f"{filename} exists. Proceeding with the rest of the script.")

    intents = discord.Intents.all()

    def read_config():
        config = {}
        with open('config.txt', 'r') as f:
            for line in f:
                line = line.strip()
                if ' = ' in line:
                    key, value = line.split(' = ', 1)
                    config[key.strip()] = value.strip()
                else:
                    pass
        return config

    config = read_config()

    
    required_keys = ['bot_token', 'owner_id']
    for key in required_keys:
        if key not in config or not config[key]:
            print(f"Invalid {key}. Please make sure it is set in the config file.")
            exit(1)

    try:
        
        for key in ['show_score', 'game_over_screen', 'add_border', 'hit_border_game_over']:
            if config.get(key) not in ['true', 'false']:
                print(f"Invalid value for {key}. Make sure you set it to 'true' or 'false'.")
                exit(1)

        
        config['show_score'] = config['show_score'].lower() == 'true'
        config['game_over_screen'] = config['game_over_screen'].lower() == 'true'
        config['add_border'] = config['add_border'].lower() == 'true'
        config['hit_border_game_over'] = config['hit_border_game_over'].lower() == 'true'

        
        config['field_size'] = int(config['field_size'])
        config['owner_id'] = int(config['owner_id'])
    except ValueError:
        print("Invalid field_size or owner_id. Make sure they are valid integers.")
        exit(1)

    
    bot = commands.Bot(command_prefix="!", intents=intents)

    
    black_square = ":black_large_square:"
    green_square = ":green_square:"
    red_square = ":red_square:"
    border_square = ":yellow_square:"
    arrows = ["⬆️", "⬇️", "⬅️", "➡️"]

    games = {}  
    blacklist = set()

    scores_file = 'scores.json'

    def load_scores():
        if os.path.isfile(scores_file):
            with open(scores_file, 'r') as f:
                return json.load(f)
        return {}

    def save_scores():
        with open(scores_file, 'w') as f:
            json.dump(scores, f, indent=2)

    scores = load_scores()

    async def delete_command_message(ctx):
        try:
            await ctx.message.delete()
        except (discord.errors.Forbidden, discord.errors.NotFound):
            pass

    def resolve_user_id(target):
        target = target.strip()
        if target.startswith('<@'):
            target = target.strip('<@!>')
        target = target.split('#')[0]
        if target.isdigit():
            return int(target)
        for guild in bot.guilds:
            for member in guild.members:
                if member.name.lower() == target.lower() or member.display_name.lower() == target.lower():
                    return member.id
        return None

    @bot.event
    async def on_ready():
        print(f'Bot is ready. Logged in as {bot.user.name}.')
        print(f'Owner ID: {config["owner_id"]}')

    @bot.command(name='snake_game')
    async def snake_game(ctx):
        if ctx.author.id in blacklist:
            await ctx.send("You are blacklisted from playing the snake game.")
            return

        if ctx.author.id in games and games[ctx.author.id]['running']:
            await ctx.send("A game is already running for you!")
            return

        initial_score = games[ctx.author.id]['score'] if ctx.author.id in games else 0
        games[ctx.author.id] = {
            'running': True,
            'paused': False,  
            'snake': [(config['field_size'] // 2, config['field_size'] // 2)],
            'direction': (1, 0),
            'food': generate_food_position(),
            'score': initial_score,
            'message': None,
            'live_views': [],
            'show_score': config['show_score'],
            'field_size': config['field_size'],
            'game_over_screen': config['game_over_screen'],
            'add_border': config['add_border'],
            'hit_border_game_over': config['hit_border_game_over'],
            'owner': ctx.author.name,
            'owner_id': ctx.author.id,  
            'server_id': ctx.guild.id if ctx.guild else None,
            'server_name': ctx.guild.name if ctx.guild else None
        }

        description = create_grid(games[ctx.author.id]['snake'], games[ctx.author.id]['food'])
        if games[ctx.author.id]['show_score']:
            description += f"\nScore: {games[ctx.author.id]['score']}"

        embed = discord.Embed(title="Snake Game", description=description, color=0x00ff00)
        games[ctx.author.id]['message'] = await ctx.send(f"Snake Game by {ctx.author.name}", embed=embed)

        for arrow in arrows:
            await games[ctx.author.id]['message'].add_reaction(arrow)
        
        game_loop.start()

    @bot.command(name='liveview')
    async def liveview(ctx, *, target: str):
        if ctx.author.id != config['owner_id']:
            await ctx.send("Only the owner can use this command.")
            return

        target = target.strip()
        if target.startswith('<@'):
            target = target.strip('<@!>')
        target = target.split('#')[0]

        game_state = None
        if target.isdigit():
            game_state = games.get(int(target))
        else:
            for user_id, gs in games.items():
                if gs['running'] and gs['owner'].lower() == target.lower():
                    game_state = gs
                    break

        if not game_state or not game_state['running']:
            await ctx.send(f"No running game found for '{target}'.")
            return

        description = create_grid(game_state['snake'], game_state['food'])
        if game_state['show_score']:
            description += f"\nScore: {game_state['score']}"

        embed = discord.Embed(title="Snake Game (Live View)", description=description, color=0x00ff00)
        view_message = await ctx.send(f"Live view of {game_state['owner']}'s game", embed=embed)
        game_state['live_views'].append(view_message)

    @bot.command(name='blacklist')
    async def blacklist_cmd(ctx, *, target: str):
        if ctx.author.id != config['owner_id']:
            await ctx.send("Only the owner can use this command.")
            return

        user_id = resolve_user_id(target)
        if user_id is None:
            await ctx.send(f"Could not find user '{target}'.")
            return

        if user_id in blacklist:
            await ctx.send("User is already blacklisted.")
            return

        blacklist.add(user_id)
        await ctx.send(f"User {user_id} has been blacklisted from the snake game.")

        game_state = games.get(user_id)
        if game_state and game_state['running']:
            game_state['running'] = False
            await game_over(game_state, forced_exit=True)

    @bot.command(name='whitelist')
    async def whitelist_cmd(ctx, *, target: str):
        if ctx.author.id != config['owner_id']:
            await ctx.send("Only the owner can use this command.")
            return

        user_id = resolve_user_id(target)
        if user_id is None:
            await ctx.send(f"Could not find user '{target}'.")
            return

        if user_id in blacklist:
            blacklist.remove(user_id)
            await ctx.send(f"User {user_id} has been removed from the blacklist.")
        else:
            await ctx.send("User is not blacklisted.")

    @tasks.loop(seconds=1)
    async def game_loop():
        for user_id, game_state in list(games.items()):
            try:
                if not game_state['running']:
                    continue

                if game_state['paused']:
                    continue

                if game_state['message'] is None:
                    continue

                snake = game_state['snake']
                head = snake[0]
                dx, dy = game_state['direction']
                new_head = ((head[0] + dx) % game_state['field_size'], (head[1] + dy) % game_state['field_size'])

                if game_state['hit_border_game_over'] and game_state['add_border']:
                    if new_head[0] == 0 or new_head[0] == game_state['field_size'] - 1 or new_head[1] == 0 or new_head[1] == game_state['field_size'] - 1:
                        game_state['running'] = False
                        await game_over(game_state)
                        continue

                if new_head in snake[1:]:
                    game_state['running'] = False
                    await game_over(game_state)
                    continue

                snake.insert(0, new_head)

                if new_head == game_state['food']:
                    game_state['score'] += 1
                    game_state['food'] = generate_food_position()
                else:
                    snake.pop()

                description = create_grid(snake, game_state['food'])
                if game_state['show_score']:
                    description += f"\nScore: {game_state['score']}"

                embed = discord.Embed(title="Snake Game", description=description, color=0x00ff00)
                await game_state['message'].edit(embed=embed)

                live_embed = discord.Embed(title="Snake Game (Live View)", description=description, color=0x00ff00)
                for view_message in game_state['live_views']:
                    await view_message.edit(embed=live_embed)
            except Exception as e:
                print(f"Error processing game for user {user_id}: {e}")

    @bot.event
    async def on_reaction_add(reaction, user):
        for user_id, game_state in games.items():
            if not game_state['running'] or user.bot or reaction.message.id != game_state['message'].id:
                continue

            
            if user.id != game_state['owner_id']:
                await reaction.remove(user)
                await user.send("You can't control this game!")
                return

            emoji = str(reaction.emoji)
            if emoji in arrows:
                game_state['direction'] = {
                    "⬆️": (0, -1),
                    "⬇️": (0, 1),
                    "⬅️": (-1, 0),
                    "➡️": (1, 0)
                }[emoji]
                await reaction.remove(user)

    @bot.command(name='pause')
    async def pause(ctx):
        await delete_command_message(ctx)
        if ctx.author.id in games and games[ctx.author.id]['running']:
            games[ctx.author.id]['paused'] = True
        else:
            await ctx.send("No game running for you.")

    @bot.command(name='continue')
    async def continue_game(ctx):
        await delete_command_message(ctx)
        if ctx.author.id in games and games[ctx.author.id]['running']:
            if games[ctx.author.id]['paused']:
                games[ctx.author.id]['paused'] = False
        else:
            await ctx.send("No game running for you.")

    @bot.command(name='exit')
    async def exit_game(ctx):
        await delete_command_message(ctx)
        if ctx.author.id in games and games[ctx.author.id]['running']:
            game_state = games[ctx.author.id]
            game_state['running'] = False
            await game_over(game_state, forced_exit=True)
        else:
            await ctx.send("No game running for you.")

    @bot.event
    async def on_command_error(ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            original_error = error.original
            if isinstance(original_error, discord.errors.Forbidden):
                await ctx.send("I don't have permission to perform this action.")
            elif isinstance(original_error, discord.errors.HTTPException):
                await ctx.send("HTTP exception occurred.")
            else:
                await ctx.send(f"An error occurred: {str(original_error)}")

    async def game_over(game_state, forced_exit=False):
        if game_state['message']:
            if game_state['game_over_screen']:
                description = create_grid(game_state['snake'], game_state['food'])
                description += f"\nGame Over! Your final score was: {game_state['score']}"
                embed = discord.Embed(title="Snake Game Over", description=description, color=0xff0000)
                await game_state['message'].edit(embed=embed)
                for view_message in game_state['live_views']:
                    await view_message.edit(embed=embed)
            else:
                await game_state['message'].delete()
                for view_message in game_state['live_views']:
                    await view_message.delete()

            old_best = scores.get(str(game_state['owner_id']), {}).get('score', 0)
            if game_state['score'] > old_best:
                scores[str(game_state['owner_id'])] = {
                    'name': game_state['owner'],
                    'score': game_state['score']
                }
                save_scores()

            del games[game_state['owner_id']]

    @bot.command(name='leaderboard')
    async def leaderboard(ctx):
        if not scores:
            await ctx.send("No scores recorded yet. Play a game to set one!")
            return

        top = sorted(scores.items(), key=lambda item: item[1]['score'], reverse=True)[:10]
        lines = []
        for rank, (user_id, entry) in enumerate(top, 1):
            lines.append(f"{rank}. {entry['name']} - {entry['score']}")

        embed = discord.Embed(title="Snake Game Leaderboard", description="\n".join(lines), color=0x00ff00)
        await ctx.send(embed=embed)

    def create_grid(snake, food):
        grid = ""
        for y in range(config['field_size']):
            for x in range(config['field_size']):
                if config['add_border'] and (x == 0 or x == config['field_size'] - 1 or y == 0 or y == config['field_size'] - 1):
                    grid += border_square + " "
                elif (x, y) in snake:
                    grid += green_square + " "
                elif (x, y) == food:
                    grid += red_square + " "
                else:
                    grid += black_square + " "
            grid += "\n"
        return grid

    def generate_food_position():
        if config['add_border']:
            possible_positions = [(x, y) for x in range(1, config['field_size'] - 1) for y in range(1, config['field_size'] - 1)]
        else:
            possible_positions = [(x, y) for x in range(config['field_size']) for y in range(config['field_size'])]

        for user_id, game_state in games.items():
            for segment in game_state['snake']:
                if segment in possible_positions:
                    possible_positions.remove(segment)

        return random.choice(possible_positions)

    try:
        bot.run(config['bot_token'])
    except discord.errors.LoginFailure:
        print("Invalid bot_token. Make sure you enter a working token.")
