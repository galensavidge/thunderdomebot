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
        cursor.execute("SELECT SUM(count) FROM messages WHERE author_id = {} AND emoji = {}".format(user.id, sql_string(emoji)))
        count = cursor.fetchone()[0]
        await ctx.send("User {0} has received {1} {2}".format(user.name, "no" if count == 0 or count is None else str(count), str(emoji)))


@bot.command(name="top-messages", help="Finds the highest reacted message")
async def get_top_messages(ctx, emoji: str = None, number: int = 5):
    if ctx.guild is None:
        await ctx.send("This command can only be used within a server!")
        return

    if number < 1 or number > 10:
        await ctx.send("Number of messages must be between **1** and **10**")
        return

    if emoji is None:
        sql_emoji = ""
    else:
        sql_emoji = "WHERE emoji = "+sql_string(emoji)+" "
    cursor.execute("SELECT message_id, MAX(author_id), SUM(count) as score FROM messages {}GROUP BY message_id ORDER BY score DESC LIMIT {}".format(sql_emoji, number))
    rows = cursor.fetchall()
    
    title = "Top {} by {}".format(str(number)+" messages" if number > 1 else "message", str(emoji) if emoji is not None else "all")
    description = ""
    listnum = 0

    for row_elements in rows:
        print("Fetching message from {} with ID = {}".format(ctx.guild.get_member(row_elements[1]).name, row_elements[0]))
        listnum += 1
        for channel in ctx.guild.text_channels: # Try to get the message from each channel
            found = False
            try:
                message = await channel.fetch_message(row_elements[0])
                description += "{0}. {1.author.name}: [message link]({2}) with {3}\n".format(listnum, message, message.jump_url.strip("<>"), row_elements[2])
                if number <= 3:
                    message_text = message.content
                    text_preview = (message_text[:97]+"...") if len(message_text) > 100 else message_text
                    description += "> "+text_preview+"\n"
                found = True
                break
            except discord.NotFound:
                pass
        
        if not Found:
            description += "{}. [Message deleted/not found]\n".format(listnum)  # Print this if the message was not found in any channel
    
    embed = discord.Embed(title=title, description=description)
    await ctx.send(embed=embed)


async def read_message_history(guild, num_days = None):
    '''Parses a server's message history, optionally stopping after num_days of messages'''

    if num_days is not None:
        cutoff_time = datetime.utcnow() - timedelta(days=num_days)
    else:
        cutoff_time = datetime.min()    # Read all history

    for channel in guild.text_channels:
        messages_parsed = 0
        if channel.permissions_for(guild.me).read_messages:
            async for message in channel.history(limit=200):
                messages_parsed += 1
                update_message_in_db(message)
        print("parsed "+str(messages_parsed)+" messages in "+channel.name)
  

# Database helper functions

def sql_string(object):
    return "\'{}\'".format(str(object))


def update_message_in_db(message: discord.Message):
    '''Updates all database rows for the passed message'''

    count_list = {}
    for reaction in message.reactions:
        emoji = sql_string(reaction.emoji) # The emoji rendered as a string; ID could also be used, maybe
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
