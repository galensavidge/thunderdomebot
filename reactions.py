import discord
from discord.ext import commands
from discord.ext.commands import Cog
import pytz

import database


class Reactions(Cog):
    def __init__(self, bot):
        self.bot = bot
        self.timezone = pytz.timezone("US/Pacific")
        self.messages = database.Messages()

    @Cog.listener()
    async def on_raw_reaction_add(self, payload):
        message = await self.bot.get_channel(payload.channel_id
                                             ).fetch_message(payload.message_id
                                                             )
        if not message.author.bot:
            print("logged " + str(payload.emoji) + " given to " +
                  message.author.name)
            self.messages.update_message_in_db(message)

    @Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        message = await self.bot.get_channel(payload.channel_id
                                             ).fetch_message(payload.message_id
                                                             )
        if not message.author.bot:
            print("logged " + str(payload.emoji) + " removed from " +
                  message.author.name)
            self.messages.update_message_in_db(message)

    @Cog.listener()
    async def on_guild_join(self, guild):
        database.create_guild_tables(guild.id)
        await self.read_message_history(guild
                                        )  # Read entire server message history

    async def read_message_history(self, guild, num_messages: int = None):
        """Parses a server's message history

        Optionally stops after num_messages messages.
        """

        last_update_time = self.messages.get_last_update_time(guild.id)

        for channel in guild.text_channels:
            if channel.permissions_for(guild.me).read_messages:
                messages_parsed = 0

                messages_since_update = await channel.history(
                    after=last_update_time, limit=None).flatten()
                extra_messages = await channel.history(
                    before=last_update_time, limit=num_messages).flatten()
                messages = messages_since_update + extra_messages

                for message in messages:
                    messages_parsed += 1
                    if not message.author.bot:
                        self.messages.update_message_in_db(message)

                print("parsed " + str(messages_parsed) + " messages in " +
                      channel.name)

    # Commands
    @commands.command(
        name="reactions",
        help="Find out how many reactions you've received",
    )
    async def get_reactions(self, ctx: discord.ext.commands.Context,
                            emoji: str = None):
        users = ctx.message.mentions
        cursor = self.messages.db.get_cursor()

        if len(users) == 0:
            users = [ctx.message.author]

        for user in users:
            query = (f"SELECT SUM(count) FROM messages_{ctx.guild.id} WHERE "
                     f"author_id = {user.id}")
            if emoji is not None:
                query += f" AND emoji = {database.sql_string(emoji)}"
            cursor.execute(query)
            count = cursor.fetchone()[0]
            await ctx.send("{0} has received {1} {2}".format(
                user.name,
                "no" if count == 0 or count is None else str(count),
                "reactions" if emoji is None else str(emoji),
            ))

        cursor.close()

    @commands.command(name="top-messages",
                      help="Finds the messages with the most reactions")
    async def get_top_messages(self, ctx: discord.ext.commands.Context,
                               emoji: str = None, number: int = 5):
        if ctx.guild is None:
            await ctx.send("This command can only be used within a server!")
            return

        if number < 1 or number > 15:
            await ctx.send(
                "Number of messages must be between **1** and **15**")
            return

        if emoji is None:
            sql_emoji_command = ""
        else:
            sql_emoji_command = "WHERE emoji = " + database.sql_string(
                emoji) + " "
        cursor = self.messages.db.get_cursor()
        cursor.execute(
            "SELECT message_id, MAX(author_id), SUM(count) as score, "
            "MAX(sendtime) as time FROM messages_{} {}GROUP BY message_id "
            "ORDER BY score DESC, time DESC LIMIT {}"
            .format(ctx.guild.id, sql_emoji_command, number))
        rows = cursor.fetchall()
        cursor.close()

        if len(rows) == 0:
            await ctx.send("No messages found with any {}".format(str(emoji)))
            return

        title = "Top {} by {}".format(
            str(number) + " messages" if number > 1 else "message",
            str(emoji) if emoji is not None else "all reactions",
        )
        description = ""
        listnum = 0
        emoji_text = "x" + str(emoji) + " " if emoji is not None else " "

        for row_elements in rows:
            member_name = ctx.guild.get_member(row_elements[1]).name
            message_id = row_elements[0]
            num_reactions = row_elements[2]
            print(f"Fetching message from {member_name} "
                  f"with ID = {message_id}")
            listnum += 1

            # Try to get the message from each channel
            message = None
            for channel in ctx.guild.text_channels:
                try:
                    message = await channel.fetch_message(message_id)
                    break
                except discord.NotFound:
                    pass

            if message is None:
                # Print this if the message was not found in any channel
                description += f"{listnum}. [Message deleted/not found]\n"
            else:
                author_name = message.author.name

                # Title
                local_time = pytz.utc.localize(row_elements[3]).astimezone(
                    self.timezone)
                timestamp = local_time.strftime("%A, %B %-d %Y")
                description += (f"{listnum}. **{author_name}** with "
                                f"{num_reactions}{emoji_text}\n")

                # Body
                if number <= 5:
                    # Text
                    message_text = message.content
                    if len(message_text) > 0:
                        text_preview = ((message_text[:247] +
                                         "...") if len(message_text) > 250
                                        else message_text)
                        description += "> " + text_preview + "\n\n"

                    # Image(s)
                    for attachment in message.attachments:
                        # "If the message this attachment was attached to
                        # is deleted, then this will 404."
                        description += attachment.url + "\n\n"

                # Timestamp/link
                description += "*[{}]({})*\n\n".format(
                    timestamp, message.jump_url.strip("<>"))

        embed = discord.Embed(title=title, description=description)
        await ctx.send(embed=embed)

    @commands.command(name="leaderboard")
    async def leaderboard(self, ctx: discord.ext.commands.Context,
                          emoji: str = None, number: int = 5):
        if number < 1 or number > 20:
            await ctx.send(
                "Number of messages must be between **1** and **20**")
            return

        if emoji is None:
            sql_emoji_command = ""
        else:
            sql_emoji_command = "WHERE emoji = " + database.sql_string(
                emoji) + " "
        cursor = self.messages.db.get_cursor()
        cursor.execute(
            "SELECT author_id, SUM(count) as score FROM messages_{} {}"
            "GROUP BY author_id ORDER BY score DESC LIMIT {}"
            .format(ctx.guild.id, sql_emoji_command, number))
        rows = cursor.fetchall()
        cursor.close()

        if len(rows) == 0:
            await ctx.send("No users found with any {}".format(str(emoji)))
            return

        title = "Top {} by {}".format(
            str(number) + " users" if number > 1 else "user",
            str(emoji) if emoji is not None else "all reactions",
        )
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
            # Discord names can be up to 32 characters long
            description += "{}. **{:<40}**{}\n".format(listnum, name, score)

        embed = discord.Embed(title=title, description=description)
        await ctx.send(embed=embed)
