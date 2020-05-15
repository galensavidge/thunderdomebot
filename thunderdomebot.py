import discord
import os
from discord.ext import commands

bot = commands.Bot(command_prefix="tdb!")

@bot.event
async def on_ready():
    print("Discord bot online!")

    # if !database_exists:
    #    for guild in bot.guilds:
    #       read_message_history(guild)

@bot.event
async def on_reaction_add(reaction, user):
    write_to_sql(reaction.message.author, reaction.emoji, 1)

@bot.event
async def on_reaction_remove(reaction, user):
    write_to_sql(reaction.message.author, reaction.emoji, -1)

@bot.event
async def on_guild_join(guild):
    read_message_history(guild)

@bot.command(name="reactions", help="Gets the number of reactions a user has received. Defaults to self if no user is provided.")
async def get_reactions(ctx, emoji: str, user=None):
    users = ctx.mentions
    for user in users:
        count = read_from_sql(user, emoji)
        ctx.send("User {0} has received {1} {2}", user.name, "no" if count == 0 else str(count), str(emoji))


async def read_message_history(guild):
    for channel in guild.channels:
        for message in channel.history:
            for reaction in message.reactions:
                user = message.author
                emoji = reaction.emoji
                count = reaction.count
                write_to_sql(user, emoji, count)

def write_to_sql(user, emoji, count):
    pass

def read_from_sql(user, emoji):
    count = 0
    return count


if __name__ == "__main__":
    token_file = open("discord_bot_token.txt")
    token = token_file.readline()
    bot.run(token)
