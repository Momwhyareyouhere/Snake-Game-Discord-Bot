import discord
from discord.ext import commands, tasks
import random
import os

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
    except ValueError:
        print("Invalid field_size. Make sure it is a valid integer.")
        exit(1)

    
    bot = commands.Bot(command_prefix="!", intents=intents)

    
    black_square = ":black_large_square:"
    green_square = ":green_square:"
    red_square = ":red_square:"
    border_square = ":yellow_square:"
    arrows = ["⬆️", "⬇️", "⬅️", "➡️"]

    games = {}  

    @bot.event
    async def on_ready():
        print(f'Bot is ready. Logged in as {bot.user.name}.')
        print(f'Owner ID: {config["owner_id"]}')
        print(f'Bot is running with token: {config["bot_token"]}')

    @bot.command(name='snake_game')
    async def snake_game(ctx):
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
            'show_score': config['show_score'],
            'field_size': config['field_size'],
            'game_over_screen': config['game_over_screen'],
            'add_border': config['add_border'],
            'hit_border_game_over': config['hit_border_game_over'],
            'owner': ctx.author.name,
            'owner_id': ctx.author.id,  
            'server_id': ctx.guild.id,
            'server_name': ctx.guild.name
        }

        description = create_grid(games[ctx.author.id]['snake'], games[ctx.author.id]['food'])
        if games[ctx.author.id]['show_score']:
            description += f"\nScore: {games[ctx.author.id]['score']}"

        embed = discord.Embed(title="Snake Game", description=description, color=0x00ff00)
        games[ctx.author.id]['message'] = await ctx.send(f"Snake Game by {ctx.author.name}", embed=embed)

        for arrow in arrows:
            await games[ctx.author.id]['message'].add_reaction(arrow)
        
        game_loop.start()

    @tasks.loop(seconds=1)
    async def game_loop():
        for user_id, game_state in games.items():
            if not game_state['running']:
                continue

            if game_state['paused']:
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

            if game_state['game_over_screen'] and new_head in snake[1:]:
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
        if ctx.author.id in games and games[ctx.author.id]['running']:
            games[ctx.author.id]['paused'] = True
            await ctx.send("Game paused.")
        else:
            await ctx.send("No game running for you.")

    @bot.command(name='continue')
    async def continue_game(ctx):
        if ctx.author.id in games and games[ctx.author.id]['running']:
            if games[ctx.author.id]['paused']:
                games[ctx.author.id]['paused'] = False
                await ctx.send("Game resumed.")
            else:
                await ctx.send("Game is not paused.")
        else:
            await ctx.send("No game running for you.")

    @bot.command(name='exit')
    async def exit_game(ctx):
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
            else:
                await game_state['message'].delete()

            del games[game_state['owner_id']]

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
