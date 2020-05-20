import discord
import os
from discord.ext import commands
import psycopg2
from psycopg2.extras import Json, DictCursor

bot = commands.Bot(command_prefix="tdb!")

database = {}
DATABASE_URL = os.environ['DATABASE_URL']
db = psycopg2.connect(DATABASE_URL, sslmode='require')
cursor = db.cursor(cursor_factory=DictCursor)

@bot.event
async def on_ready():
    print("Discord bot online!")

    # if !database_exists:
    for guild in bot.guilds:
        await read_message_history(guild)

@bot.event
async def on_raw_reaction_add(payload):
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    print("logged "+str(payload.emoji)+" given to "+message.author.name)
    write_to_db(message.author, str(payload.emoji), 1)

@bot.event
async def on_raw_reaction_remove(payload):
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    print("logged "+str(payload.emoji)+" removed from "+message.author.name)
    write_to_db(message.author, str(payload.emoji), -1)

@bot.event
async def on_guild_join(guild):
    await read_message_history(guild)

@bot.command(name="reactions", help="Gets the number of reactions of a specific type users have received.")
async def get_reactions(ctx, emoji: str, user=None):
    users = ctx.message.mentions
    for user in users:
        count = read_from_db(user, emoji)
        await ctx.send("User {0} has received {1} {2}".format(user.name, "no" if count == 0 else str(count), str(emoji)))


async def read_message_history(guild):
    for channel in guild.text_channels:
        messages_parsed = 0
        if channel.permissions_for(guild.me).read_messages:
            async for message in channel.history(limit=100):
                messages_parsed += 1
                for reaction in message.reactions:
                    user = message.author
                    emoji = reaction.emoji
                    count = reaction.count
                    write_to_db(user, str(emoji), count)
        print("parsed "+str(messages_parsed)+" messages in "+channel.name)

def write_to_db(user, emoji: str, count):
    cursor.execute("SELECT emoji FROM reactions WHERE id = {}".format(user.id))
    emojis = cursor.fetchone()
    if emojis is not None:
        if emoji in emojis:
            new_count = emojis.get(emoji) + count
        else:
            new_count = count

        if new_count > 0:
            emojis[emoji] = new_count
        else:
            del emojis[emoji]

        cursor.execute("UPDATE reactions SET emoji = {} WHERE id = {}".format(emojis, user.id))
    else:
        if count > 0:
            cursor.execute("INSERT into reactions (id, emoji) values ({}, {})".format(user.id, Json({emoji:count})))
        

def read_from_db(user, emoji: str):
    cursor.execute("SELECT emoji FROM reactions WHERE id = {}".format(user.id))
    emoji_dict = cursor.fetchone()

    if emoji_dict is not None:
        if emoji in emoji_dict:
            return emoji_dict[emoji]
        else:
            print("no record of " + emoji + " for the user!")
    else:
        print("user not in database!")

    return 0


if __name__ == "__main__":

    cursor.execute("CREATE TABLE reactions (id NUM PRIMARY KEY, emoji JSONB);")

    if os.path.exists("discord_bot_token.txt"):
        token_file = open("discord_bot_token.txt")
        token = token_file.readline()
        bot.run(token)
    else:
        token = os.environ['BOT_TOKEN']
    bot.run(token)

    cursor.close()
    db.close()
