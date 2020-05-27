import discord
from discord.ext import commands
from discord.ext.commands import Cog
from datetime import datetime, timedelta
import pytz

import database

class Reactions(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone("US/Pacific")

    
    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        print("logged "+str(payload.emoji)+" given to "+message.author.name)
        database.update_message_in_db(message)


    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        message = await self.bot.get_channel(payload.channel_id).fetch_message(payload.message_id)
        print("logged "+str(payload.emoji)+" removed from "+message.author.name)
        database.update_message_in_db(message)


    @Cog.listener()
    async def on_guild_join(self, guild):
        await self.read_message_history(guild)       # Read entire server message history


    async def read_message_history(self, guild, num_messages = None):
        '''Parses a server's message history, optionally stopping after num_messages of messages'''

        last_update_time = database.get_last_update_time()

        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).read_messages:
                messages_parsed = 0

                messages_since_update = await channel.history(after=last_update_time, limit=None).flatten()
                extra_messages = await channel.history(before=last_update_time, limit=num_messages).flatten()
                messages = messages_since_update + extra_messages

                for message in messages:
                    messages_parsed += 1
                    database.update_message_in_db(message)
                
                print("parsed "+str(messages_parsed)+" messages in "+channel.name)


    # Commands

    @commands.command(name="reactions", help="Gets the number of reactions of a specific type users have received.")
    async def get_reactions(self, ctx, emoji: str):
        users = ctx.message.mentions
        cursor = database.get_cursor()

        if len(users) == 0:
            users = [ctx.message.author]
        
        for user in users:
            cursor.execute("SELECT SUM(count) FROM messages WHERE author_id = {} AND emoji = {}".format(user.id, database.sql_string(emoji)))
            count = cursor.fetchone()[0]
            await ctx.send("User {0} has received {1} {2}".format(user.name, "no" if count == 0 or count is None else str(count), str(emoji)))
        
        cursor.close()


    @commands.command(name="top-messages", help="Finds the highest reacted message")
    async def get_top_messages(self, ctx, emoji: str = None, number: int = 5):
        if ctx.guild is None:
            await ctx.send("This command can only be used within a server!")
            return

        if number < 1 or number > 15:
            await ctx.send("Number of messages must be between **1** and **15**")
            return

        if emoji is None:
            sql_emoji_command = ""
        else:
            sql_emoji_command = "WHERE emoji = "+database.sql_string(emoji)+" "
        cursor = database.get_cursor()
        cursor.execute("SELECT message_id, MAX(author_id), SUM(count) as score, MAX(sendtime) as time FROM messages {}GROUP BY message_id ORDER BY score DESC, time LIMIT {}".format(sql_emoji_command, number))
        rows = cursor.fetchall()
        cursor.close()
        
        if len(rows) == 0:
            await ctx.send("No messages found with any {}".format(str(emoji)))
            return

        title = "Top {} by {}".format(str(number)+" messages" if number > 1 else "message", str(emoji) if emoji is not None else "all")
        description = ""
        listnum = 0
        emoji_text = "x"+str(emoji)+" " if emoji is not None else " "

        for row_elements in rows:
            print("Fetching message from {} with ID = {}".format(ctx.guild.get_member(row_elements[1]).name, row_elements[0]))
            listnum += 1
            for channel in ctx.guild.text_channels: # Try to get the message from each channel
                found = False
                try:
                    message = await channel.fetch_message(row_elements[0])

                    # Title
                    local_time = pytz.utc.localize(row_elements[3]).astimezone(self.timezone)
                    timestamp = local_time.strftime("%a, %b %-d %Y")
                    description += "{0}. **{1.author.name}** with {2}{3} *[{4}]({5})*\n".format(listnum, message, row_elements[2], emoji_text, timestamp, message.jump_url.strip("<>"))

                    # Body
                    if number <= 5:

                        # Text
                        message_text = message.content
                        if len(message_text) > 0:
                            text_preview = (message_text[:247]+"...") if len(message_text) > 250 else message_text
                            description += "> "+text_preview+"\n\n"

                        # Image(s)
                        for attachment in message.attachments:
                            try:
                                description += attachment.url+"\n\n"
                            except: # "If the message this attachment was attached to is deleted, then this will 404."
                                pass

                    found = True
                    break
                except discord.NotFound:
                    pass
            
            if not found:
                description += "{}. [Message deleted/not found]\n".format(listnum)  # Print this if the message was not found in any channel
        
        embed = discord.Embed(title=title, description=description)
        await ctx.send(embed=embed)


    @commands.command(name = "leaderboard")
    async def leaderboard(self, ctx, emoji: str = None, number: int = 5):
        
        if number < 1 or number > 20:
            await ctx.send("Number of messages must be between **1** and **20**")
            return

        if emoji is None:
            sql_emoji_command = ""
        else:
            sql_emoji_command = "WHERE emoji = "+database.sql_string(emoji)+" "
        cursor = database.get_cursor()
        cursor.execute("SELECT author_id, SUM(count) as score FROM messages {}GROUP BY author_id ORDER BY score DESC LIMIT {}".format(sql_emoji_command, number))
        rows = cursor.fetchall()
        cursor.close()

        if len(rows) == 0:
            await ctx.send("No users found with any {}".format(str(emoji)))
            return

        title = "Top {} by {}".format(str(number)+" users" if number > 1 else "user", str(emoji) if emoji is not None else "all")
        description = ""
        listnum = 0

        for row_elements in rows:
            user = self.bot.get_user(row_elements[0])
            score = row_elements[1]
            listnum += 1

            if user is not None:
                name = user.name
            else:
                name = "[User not found]"
            
            description += "{}. **{:<40}**{}\n".format(listnum, name, score) # Discord names can be up to 32 characters long
        
        embed = discord.Embed(title=title, description=description)
        await ctx.send(embed=embed)