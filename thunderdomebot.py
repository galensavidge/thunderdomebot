import os

import discord
from discord import Intents
from discord.ext import commands

import database
import reactions
from tetris import tetris

intents = Intents.all()
bot: commands.Bot = commands.Bot(intents=intents, command_prefix="tdb!")

github_url = "git.io/Jf27r"


@bot.event
async def on_ready():
    print("ThunderDomeBot online!")
    await bot.change_presence(
        activity=discord.Game(name="Restarting..."), status=discord.Status.dnd
    )

    # if !database_exists:
    for guild in bot.guilds:
        print(f"Parsing messages from {guild.name}...")
        database.create_guild_tables(guild.id)
        await bot.get_cog("Reactions").read_message_history(guild,
                                                            num_messages=200)

    await bot.change_presence(
        activity=discord.Game(name="tdb!help | " + github_url),
        status=discord.Status.online,
    )


@bot.command(name="github")
async def github_link(ctx):
    await ctx.send("GitHub link: <https://{}>".format(github_url))


if __name__ == "__main__":

    if os.path.exists("discord_bot_token.txt"):
        token_file = open("discord_bot_token.txt")
        token = token_file.readline()
    else:
        token = os.environ["BOT_TOKEN"]

    db = database.Database()
    bot.add_cog(reactions.Reactions(bot))
    bot.add_cog(tetris.TetrisCog(bot))
    bot.run(token)

    db.close()
