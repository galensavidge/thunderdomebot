import discord
from discord.ext import commands
import os

from reactions import Reactions
import database


bot = commands.Bot(command_prefix="tdb!")


@bot.event
async def on_ready():
    print("ThunderDomeBot online!")
    await bot.change_presence(activity=discord.Game(name="Restarting..."), status=discord.Status.dnd)

    # if !database_exists:
    for guild in bot.guilds:
        await bot.get_cog("Reactions").read_message_history(guild, num_days=1)   # Read one day of history
    
    await bot.change_presence(activity=discord.Game(name="tdb!help | git.io/Jf27r"), status=discord.Status.online)


if __name__ == "__main__":

    if os.path.exists("discord_bot_token.txt"):
        token_file = open("discord_bot_token.txt")
        token = token_file.readline()
    else:
        token = os.environ['BOT_TOKEN']
    
    bot.add_cog(Reactions(bot))
    bot.run(token)

    database.close()
