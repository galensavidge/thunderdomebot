import discord
import os
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime

DATABASE_URL = os.environ['DATABASE_URL']

def create_guild_tables(guild_id):
    database = Database()
    table_name = "messages_{}".format(guild_id)
    cursor = database.get_cursor()

    cursor.execute("SELECT to_regclass('{}')".format(table_name))
    table_exists = cursor.fetchone()[0]
    if not table_exists:
        cursor.execute("CREATE TABLE {} (message_id BIGINT, author_id BIGINT, emoji VARCHAR(128), "
                        "count INT, sendtime TIMESTAMP, updatetime TIMESTAMP)".format(table_name))
        database.commit()

        print("Successfully created table ", table_name)

        cursor.close()

def sql_string(object):
    return "\'{}\'".format(str(object))

class Database():
    connection = None

    def __init__(self):
        if self.connection is None:
            self.connection = psycopg2.connect(DATABASE_URL, sslmode='require')

    def commit(self):
        self.connection.commit()

    def get_cursor(self):
        return self.connection.cursor(cursor_factory=DictCursor)

    def close(self):
        self.connection.close()


class Table():

    def __init__(self):
        self.db = Database()


class Messages(Table):

    def update_message_in_db(self, message: discord.Message):
        '''Updates all database rows for the passed message'''

        count_list = {}
        for reaction in message.reactions:
            emoji = sql_string(reaction.emoji) # The emoji rendered as a string; ID could also be used, maybe
            count = reaction.count
            if reaction.me:
                count -= 1              # Remove self reactions
            if count > 0:
                count_list[emoji] = count
        
        if len(count_list) > 0:
            for emoji in count_list.keys():
                self.write_to_db(message.id, message.author.id, emoji, count_list[emoji], message.created_at, message.guild.id)
        else:
            cursor = self.db.get_cursor()
            cursor.execute("DELETE FROM messages_{} WHERE message_id = {}".format(message.guild.id, message.id)) # Delete if the message has no reactions
            cursor.close()
            

    def write_to_db(self, message_id: int, author_id: int, emoji: str, count: int, time_sent: datetime, guild_id: int):
        '''Writes one row to the message database'''

        time_now = sql_string(datetime.utcnow())
        sendtime = sql_string(time_sent)
        table_name = "messages_{}".format(guild_id)

        cursor = self.db.get_cursor()
        cursor.execute("SELECT emoji FROM {} WHERE message_id = {} AND emoji = {}".format(table_name, message_id, emoji))
        entry = cursor.fetchone()
        if entry is not None:
            if count > 0:
                cursor.execute("UPDATE {} SET count = {}, sendtime = {}, updatetime = {} WHERE message_id = {} AND emoji = {}" \
                                                                                .format(table_name, count, sendtime, time_now, message_id, emoji))
            else:
                cursor.execute("DELETE FROM {} WHERE message_id = {} AND emoji = {}".format(table_name, message_id, emoji))
        elif count > 0:
                cursor.execute("INSERT into {} (message_id, author_id, emoji, count, sendtime, updatetime) values ({}, {}, {}, {}, {}, {})" \
                                                                                .format(table_name, message_id, author_id, emoji, count, sendtime, time_now))
        
        cursor.close()
        self.db.commit()


    def purge_db(self, guild_id: int):
        '''Deletes all entries in a guild's database'''
        
        table_name = "messages_{}".format(guild_id)
        cursor = self.db.get_cursor()
        cursor.execute("DELETE FROM {}".format(table_name))
        cursor.close()
        self.db.commit()


    def get_last_update_time(self, guild_id: int):
        '''Returns the time the last database update occurred as a datetime object'''

        cursor = self.db.get_cursor()
        cursor.execute("SELECT MAX(updatetime) FROM messages_{}".format(guild_id))
        time = cursor.fetchone()[0]    # Postgres' default time format can be automatically converted to a datetime
        cursor.close()
        return time
