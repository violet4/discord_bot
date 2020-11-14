#!/usr/bin/env python
"""
2020-11-05
started from:
https://realpython.com/how-to-make-a-discord-bot-python/

https://discordpy.readthedocs.io/en/latest/faq.html
this page explains why await bot.process_commands(message) is
necessary in on_message, and also explains how to make subcommands.

"""
import re
import requests
import random
import numpy as np
from envbash import load_envbash
import os
from discord.ext import commands, tasks
from discord.enums import Status

load_envbash('env.txt')
TOKEN = os.getenv('DISCORD_TOKEN')
# GUILD = os.getenv('DISCORD_GUILD')

# client = discord.Client()
bot = commands.Bot(command_prefix='!')
info_dir = os.path.join(os.path.dirname(__file__), 'info')

owner_user_id = None
owner_user_id_file = os.path.join(info_dir, 'owner_id.txt')

with open(owner_user_id_file, 'r') as fr:
    owner_user_id = int(fr.read().strip())

bot_channel_id_file = os.path.join(info_dir, 'bot_channel_id.txt')
bot_channel_id = None
with open(bot_channel_id_file, 'r') as fr:
    bot_channel_id = int(fr.read().strip())


async def get_owner():
    try:
        return get_owner.owner
    except AttributeError:
        print(f'owner_user_id: {owner_user_id}')
        setattr(get_owner, 'owner', await bot.fetch_user(owner_user_id))
        return get_owner.owner

async def get_bot_channel():
    try:
        return get_bot_channel.bot_channel
    except AttributeError:
        setattr(
            get_bot_channel, 'bot_channel',
            await bot.fetch_channel(bot_channel_id)
        )
        return get_bot_channel.bot_channel

async def authorized(ctx):
    if ctx.author.id == owner_user_id:
        return True
    await ctx.send(f'you are unauthorized to run this command')
    print(
        f'user @{ctx.author.name}#{ctx.author.discriminator} '
        f'({ctx.author.id}) tried to run: {ctx.message.content}'
    )
    owner = await get_owner()
    await owner.send(
        f'unauthorized user <@!{ctx.author.id}> '
        f'tried to run: {ctx.message.content}'
    )
    return False

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')

    owner = await get_owner()
    await owner.send(f'hello!!!!! up and running!!!!!!')

@bot.event
async def on_message(message):
    '''
    allows us to view and process every message the bot can see
    '''
    if message.author == bot.user:
        return

    if bot.user.name in message.content:
        await message.channel.send('you called my name?')

    if message.author.id != owner_user_id:
        if message.channel.type.name == 'private':
            owner = await get_owner()
            await owner.send(f'<@!{message.author.id}> says: {message.content}')

        print(
            f'\n'
            f'message.channel.type.name: {message.channel.type.name}; '
            f'message.channel.type.value: {message.channel.type.value};\n'
            f'message.content: {message.content}'
        )

    # the new versions of discord.py require this to
    # be able to run normal commands in addition to
    # viewing all messsages
    await bot.process_commands(message)


def load_file(filename):
    filepath = os.path.join(
        os.path.dirname(__file__),
        'info',
        filename
    )
    lines = list()
    with open(filepath, 'r') as fr:
        for line in fr:
            line = line.strip()
            if line:
                lines.append(line)
    return lines


def load_bad_words_re():
    if hasattr(load_bad_words_re, 'bad_words_re'):
        return load_bad_words_re.bad_words_re

    bad_words_re_str = None
    bad_words_file = os.path.join(
        os.path.dirname(__file__),
        'info',
        'bad_words.txt'
    )
    with open(bad_words_file, 'r') as fr:
        bad_words_re_str = fr.read().strip()

    bad_words_re_str = bad_words_re_str.replace('u', '[uv]')
    bad_words_re_str = bad_words_re_str.replace('i', '[i!]')
    bad_words_re_str = bad_words_re_str.replace('a', '[a@]')
    bad_words_re_str = bad_words_re_str.replace('s', r'[s\$]')
    bad_words_re = re.compile(bad_words_re_str, re.I)

    load_bad_words_re.bad_words_re = bad_words_re
    return load_bad_words_re.bad_words_re


def get_happy_character_generator():
    happy_characters = [c for c in '!#%&']
    while True:
        random.shuffle(happy_characters)
        for c in happy_characters:
            yield c

happy_character_generator = get_happy_character_generator()

replacements = {
    'i': '\\*',
    '!': '\\*',
    's': '$',
    'a': '@',
}

def replace_char(char):
    return replacements.get(
        char,
        next(happy_character_generator)
    )

def profanity_filter(message):
    bad_words_re = load_bad_words_re()
    bad_words = bad_words_re.findall(message)
    for word in bad_words:
        new_word = ''.join([
            replace_char(c) for c in word
        ])
        message = message.replace(word, new_word, 1)

    return message


class Cute(commands.Cog):
    @commands.command(aliases=['echo', 'repeat'])
    async def say(self, ctx, *args):
        """repeat the message provided"""
        message = ' '.join(args)
        message = profanity_filter(message)
        await ctx.send(message)

    @commands.command()
    async def do(self, ctx, *args):
        'perform some action (same as bot running /me command)'
        await ctx.send(f'_{" ".join(args)}_')

    @commands.command()
    async def greet(self, ctx, *args):
        'say hello, optionally to someone specific'
        if args:
            await ctx.send(f'Hello {" ".join(args)}!')
        else:
            await ctx.send(f'Hello!')


class Random(commands.Cog):
    random_dir = os.path.join(
        info_dir,
        'random'
    )
    random_files = os.listdir(random_dir)

    lists = dict()

    @classmethod
    def ensure_file_loaded(cls, file, name):
        if name in cls.lists:
            return
        filepath = os.path.join(cls.random_dir, file)
        with open(filepath, 'r') as fr:
            lines = fr.read().strip().split('\n')
        lines = [l.strip() for l in lines]
        cls.lists[name] = lines

    @classmethod
    def get_random_line(cls, name):
        return random.choice(cls.lists[name])

    @commands.command()
    async def house(self, ctx):
        'a random quote from House MD, from http://www.housemd-guide.com/characters/houserules.php'
        key = 'house'
        self.ensure_file_loaded('house_quotes.txt', key)
        await ctx.send(self.get_random_line(key))

    @commands.command()
    async def m8(self, ctx):
        'shake a magic 8 ball, from http://www.otcpas.com/advisor-blog/magic-8-ball-messages/'
        key = 'm8'
        self.ensure_file_loaded('m8_ball_msgs.txt', key)
        await ctx.send(self.get_random_line(key))

    @commands.command(aliases=['sw'])
    async def starwars(self, ctx):
        'star wars quotes, from https://www.starwars.com/news/40-memorable-star-wars-quotes'
        key = 'starwars'
        self.ensure_file_loaded('star_wars_quotes.txt', key)
        await ctx.send(self.get_random_line(key))

    @commands.command(aliases='doctor who'.split())
    async def drwho(self, ctx):
        'Doctor Who quotes from https://www.scarymommy.com/doctor-who-quotes/'
        key = 'drwho'
        self.ensure_file_loaded('doctor_who.txt', key)
        await ctx.send(self.get_random_line(key))


class Admin(commands.Cog):
    'commands for authorized administrators only'

    @commands.command()
    async def debug(self, ctx):
        'open a terminal debug'
        if not await authorized(ctx):
            return
        try:
            import readline
        except ImportError:
            print("failed to import readline for pdb/ipdb debugging")
        try:
            import ipdb as pdb
        except ImportError:
            import pdb
        pdb.set_trace()
        await ctx.send(f'done debugging')

    @commands.command(aliases=['mc'])
    async def message_channel(self, ctx, channel_id, *message):
        'send a message in a given channel'
        if not await authorized(ctx):
            return
        channel_id = int(channel_id)
        await bot.wait_until_ready()
        channel = bot.get_channel(channel_id)
        await channel.send(' '.join(message))

    @commands.command(aliases=['rs'])
    async def restart(self, ctx):
        'restart the bot'
        if not await authorized(ctx):
            return

        await ctx.send('restarting...')
        os.system('./bot.py')

    @commands.command(aliases=['off'])
    async def offline(self, ctx):
        if not await authorized(ctx):
            return

        await bot.change_presence(status=Status.offline)
        await ctx.send('status set to offline')

    @commands.command(aliases=['on'])
    async def online(self, ctx):
        if not await authorized(ctx):
            return

        await bot.change_presence(status=Status.online)
        await ctx.send('status set to online')

    @commands.command()
    async def todo(self, ctx, *new_todo):
        '''view or add TODO items

        without any argument, lists existing TODOs.
        with an argument, add a TODO to the list
        '''
        if not await authorized(ctx):
            return

        todo_file = os.path.join(
            os.path.dirname(__file__),
            'info',
            'todos.txt'
        )
        if not os.path.exists(todo_file):
            with open(todo_file, 'a') as fa:
                print('', end='', file=fa)

        new_todo = ' '.join(new_todo)
        if new_todo:
            with open(todo_file, 'a') as fa:
                print(new_todo, file=fa)
            await ctx.send(f'"{new_todo}" added!')
        else:
            with open(todo_file, 'r') as fr:
                await ctx.send(f'TODOs:\n{fr.read()}')


class Utilities(commands.Cog):
    @commands.command()
    async def suggest(self, ctx):
        'make a suggestion to the bot creator'
        await bot.wait_until_ready()
        owner = await get_owner()
        await owner.send(
            f'user <@!{ctx.author.id}> says: {ctx.message.content}'
        )


class Information(commands.Cog):
    @commands.command()
    async def weather(self, ctx, zipcode):
        'get the weather for a given zip code'
        if not zipcode.isnumeric() or len(zipcode) != 5:
            await ctx.send("invalid zipcode")
            return
        await bot.wait_until_ready()
        resp = requests.get(f'https://wttr.in/{zipcode}')
        short = resp.text
        # short = '└'.join(short.split('└', 2)[:2])
        for color_code in set(re.findall(r'\x1b[^m]+m', short)):
            short = short.replace(color_code, '')

        longest_line = 0
        chars = list()
        for line in short.strip().split('\n'):
            chars.append(list())
            longest_line = max(longest_line, len(line))
            for c in line:
                chars[-1].append(c)
        for lst in chars:
            lst.extend(['']*(longest_line-len(lst)))

        array = np.array(chars)

        days = [
            'today',
            'tomorrow',
            'the day after tomorrow',
        ]
        times_of_day = 'morning noon evening night'.split()
        this_window = ''
        for day, col in zip(days, range(3)):
            col *= 10
            for tod, row in zip(times_of_day, range(4)):
                row *= 32
                window = '\n'.join([''.join(l) for l in array[11-1+col:16+col, 2+row:29+row]])
                window = f'{day} {tod}\n```{window}```\n'
                if len(this_window) + len(window) > 2000:
                    await ctx.send(this_window)
                    this_window = window
                else:
                    this_window += window

        # final send
        await ctx.send(this_window)
        await ctx.send(f'credits `https://wttr.in` `https://twitter.com/igor_chubin`')


@tasks.loop(hours=1)
async def called_every_10s():
    message_channel = bot.get_channel(774145104365617203)
    await message_channel.send("Your message")

@called_every_10s.before_loop
async def before():
    await bot.wait_until_ready()
    print("Finished waiting")

if __name__ == '__main__':
    # called_every_10s.start()
    bot.add_cog(Admin(bot))
    bot.add_cog(Utilities(bot))
    bot.add_cog(Information(bot))
    bot.add_cog(Cute(bot))
    bot.add_cog(Random(bot))
    bot.run(TOKEN)
