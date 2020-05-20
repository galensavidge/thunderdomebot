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
    write_to_db(message)


@bot.event
async def on_raw_reaction_remove(payload):
    message = await bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
    print("logged "+str(payload.emoji)+" removed from "+message.author.name)
    write_to_db(message)


@bot.event
async def on_guild_join(guild):
    await read_message_history(guild)


@bot.command(name="reactions", help="Gets the number of reactions of a specific type users have received.")
async def get_reactions(ctx, emoji: str, user=None):
    users = ctx.message.mentions
    for user in users:
        messages = read_from_db(user, emoji)
        count = 0
        for message in messages:
            for reaction in message.reactions:
                if str(reaction.emoji) == emoji:
                    count += reaction.count
                    if reaction.me:
                        count -= 1
        
        await ctx.send("User {0} has received {1} {2}".format(user.name, "no" if count == 0 else str(count), str(emoji)))


async def read_message_history(guild):
    one_day_ago = datetime.utcnow() - timedelta(days=1)     # Alternatively this could be configuarble

    for channel in guild.text_channels:
        messages_parsed = 0
        if channel.permissions_for(guild.me).read_messages:
            async for message in channel.history(after=one_day_ago):
                messages_parsed += 1
                write_to_db(message)
        print("parsed "+str(messages_parsed)+" messages in "+channel.name)
  

def write_to_db(message: discord.Message):
    message_id = message.id
    user = message.author
    reaction_list = {}
    for reaction in message.reactions:
        emoji = str(reaction.emoji) # The emoji rendered as a string; ID could also be used, maybe
        count = reaction.count
        if reaction.me:
            count -= 1              # Remove self reactions
        if count > 0:
            reaction_list[emoji] = count
    
    if len(reaction_list) > 0:
        # Write message to db
        pass
    else:
        # Remove message from db
        pass
        

async def read_from_db(guild: discord.Guild, emoji: str = None, user: discord.User = None):
    # Get messages from guild.id matching non-None emoji and user.id
    message_ids = list()
    messages = list()
    for id in message_ids:
        message = await bot.get_guild(guild.id).fetch_message(id)
        if message is not None:
            messages.append(message)

    return messages


if __name__ == "__main__":

    if os.path.exists("discord_bot_token.txt"):
        token_file = open("discord_bot_token.txt")
        token = token_file.readline()
    else:
        token = os.environ['BOT_TOKEN']
    bot.run(token)

    cursor.close()
    db.close()
