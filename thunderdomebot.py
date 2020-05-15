import discord
import os
from discord.ext import commands

bot = commands.Bot(command_prefix="tdb!")

database = {}

@bot.event
async def on_ready():
    print("Discord bot online!")

    # if !database_exists:
    for guild in bot.guilds:
        await read_message_history(guild)

@bot.event
async def on_reaction_add(reaction, user):
    write_to_db(reaction.message.author, reaction.emoji, 1)

@bot.event
async def on_reaction_remove(reaction, user):
    write_to_db(reaction.message.author, reaction.emoji, -1)

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
            async for message in channel.history(limit=None):
                messages_parsed += 1
                for reaction in message.reactions:
                    user = message.author
                    emoji = reaction.emoji
                    count = reaction.count
                    write_to_db(user, str(emoji), count)
        print("parsed "+str(messages_parsed)+" messages in "+channel.name)

def write_to_db(user, emoji: str, count):
    if user in database:
        sub_db = database[user]
        if emoji in sub_db:
            new_count = sub_db.get(emoji) + count
        else:
            new_count = count
        
        if new_count > 0:
            sub_db[emoji] = new_count
        else:
            del sub_db[emoji]
    else:
        if count > 0:
            database[user] = {emoji : count}
        

def read_from_db(user, emoji: str):
    if user in database:
        sub_db = database[user]
        if emoji in sub_db:
            return sub_db[emoji]
        else:
            print("no record of "+emoji+" for the user!")
    else:
        print("user not in database!")
    
    return 0


if __name__ == "__main__":
    token_file = open("discord_bot_token.txt")
    token = token_file.readline()
    bot.run(token)
