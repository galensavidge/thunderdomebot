import discord
from discord.ext import commands
import os

from reactions import Reactions
import database


bot = commands.Bot(command_prefix="tdb!")

github_url = "git.io/Jf27r"

@bot.event
async def on_ready():
    print("ThunderDomeBot online!")
    await bot.change_presence(activity=discord.Game(name="Restarting..."), status=discord.Status.dnd)

    # if !database_exists:
    for guild in bot.guilds:
        await bot.get_cog("Reactions").read_message_history(guild, num_messages=200)
    
    await bot.change_presence(activity=discord.Game(name="tdb!help | "+github_url), status=discord.Status.online)


@bot.command(name="github")
async def github_link(ctx):
    await ctx.send("GitHub link: <https://{}>".format(github_url))


if __name__ == "__main__":

    if os.path.exists("discord_bot_token.txt"):
        token_file = open("discord_bot_token.txt")
        token = token_file.readline()
    else:
        token = os.environ['BOT_TOKEN']
    
    bot.add_cog(Reactions(bot))
    bot.run(token)

    database.close()
