import discord
import os
from discord.ext import commands

bot = commands.Bot(command_prefix="tdb!")

@bot.event
async def on_ready():
    print("Discord bot online!")

    # if !database_exists:
    for guild in bot.guilds:
        await read_message_history(guild)

@bot.event
async def on_reaction_add(reaction, user):
    write_to_sql(reaction.message.author, reaction.emoji, 1)

@bot.event
async def on_reaction_remove(reaction, user):
    write_to_sql(reaction.message.author, reaction.emoji, -1)

@bot.event
async def on_guild_join(guild):
    await read_message_history(guild)

@bot.command(name="reactions", help="Gets the number of reactions of a specific type users have received.")
async def get_reactions(ctx, emoji: str, user=None):
    users = ctx.message.mentions
    for user in users:
        count = read_from_sql(user, emoji)
        ctx.send("User {0} has received {1} {2}", user.name, "no" if count == 0 else str(count), str(emoji))


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
                    print("user: "+user.name+" emoji: "+str(emoji)+" count: "+str(count))
                    write_to_sql(user, emoji, count)
        print("parsed "+str(messages_parsed)+" messages in "+channel.name)

def write_to_sql(user, emoji, count):
    pass

def read_from_sql(user, emoji):
    count = 0
    return count


if __name__ == "__main__":
    token_file = open("discord_bot_token.txt")
    token = token_file.readline()
    bot.run(token)
