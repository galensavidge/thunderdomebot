import discord
import os
from discord.ext import commands
import psycopg2
from psycopg2.extras import Json, DictCursor
from datetime import datetime, timedelta

bot = commands.Bot(command_prefix="tdb!")

DATABASE_URL = os.environ['DATABASE_URL']
db = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = db.cursor(cursor_factory=DictCursor)


# Events

@bot.event
async def on_ready():
    print("Discord bot online!")

    # if !database_exists:
    for guild in bot.guilds:
        await read_message_history(guild, num_days=1)   # Read one day of history


@bot.event
async def on_raw_reaction_add(payload):
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    print("logged "+str(payload.emoji)+" given to "+message.author.name)
    update_message_in_db(message)


@bot.event
async def on_raw_reaction_remove(payload):
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    print("logged "+str(payload.emoji)+" removed from "+message.author.name)
    update_message_in_db(message)


@bot.event
async def on_guild_join(guild):
    await read_message_history(guild)       # Read entire server message history


# Commands

@bot.command(name="reactions", help="Gets the number of reactions of a specific type users have received.")
async def get_reactions(ctx, emoji: str):
    users = ctx.message.mentions
    if len(users) == 0:
        users = [ctx.message.author]
    for user in users:
        cursor.execute("SELECT SUM(count) FROM messages WHERE author_id = {} AND emoji = {}".format(user.id, emoji))
        count = cursor.fetchone()
        await ctx.send("User {0} has received {1} {2}".format(user.name, "no" if count == 0 or count is None else str(count), str(emoji)))


@bot.command(name="top", help="Finds the highest reacted message")
async def get_top(ctx, emoji: str):
    pass


async def read_message_history(guild, num_days = None):
    '''Parses a server's message history, optionally stopping after num_days of messages'''

    if num_days is not None:
        cutoff_time = datetime.utcnow() - timedelta(days=num_days)
    else:
        cutoff_time = datetime.min()    # Read all history

    for channel in guild.text_channels:
        messages_parsed = 0
        if channel.permissions_for(guild.me).read_messages:
            async for message in channel.history(after=cutoff_time):
                messages_parsed += 1
                update_message_in_db(message)
        print("parsed "+str(messages_parsed)+" messages in "+channel.name)
  

# Database helper functions

def update_message_in_db(message: discord.Message):
    '''Updates all database rows for the passed message'''

    count_list = {}
    for reaction in message.reactions:
        emoji = str(reaction.emoji) # The emoji rendered as a string; ID could also be used, maybe
        count = reaction.count
        if reaction.me:
            count -= 1              # Remove self reactions
        if count > 0:
            count_list[emoji] = count
    
    if len(count_list) > 0:
        for emoji in count_list.keys():
            write_to_db(message.id, message.author.id, emoji, count_list[emoji])
    else:
        cursor.execute("DELETE FROM messages WHERE message_id = {}".format(message.id)) # Delete if the message has no reactions
        

def write_to_db(message_id: int, author_id: int, emoji: str, count: int):
    '''Writes one row to the message database'''

    cursor.execute("SELECT emoji FROM messages WHERE message_id = {} AND emoji = {}".format(message_id, emoji))
    entry = cursor.fetchone()
    if entry is not None:
        if count > 0:
            cursor.execute("UPDATE messages SET count = {} WHERE message_id = {} AND emoji = {}".format(count, message_id, emoji))
        else:
            cursor.execute("DELETE FROM messages WHERE message_id = {} AND emoji = {}".format(message_id, emoji))
    elif count > 0:
            cursor.execute("INSERT into messages (message_id, author_id, emoji, count) values ({}, {}, {}, {})".format(message_id, author_id, emoji, count))
    
    db.commit()


if __name__ == "__main__":

    if os.path.exists("discord_bot_token.txt"):
        token_file = open("discord_bot_token.txt")
        token = token_file.readline()
    else:
        token = os.environ['BOT_TOKEN']
    bot.run(token)

    cursor.close()
    db.close()
