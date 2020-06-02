import discord
import os
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime

DATABASE_URL = os.environ['DATABASE_URL']
db = psycopg2.connect(DATABASE_URL, sslmode='require')
print("Just made a db connection") #DEBUG


def close():
    db.close()

def commit():
    db.commit()

def get_cursor():
    return db.cursor(cursor_factory=DictCursor)


def sql_string(object):
    return "\'{}\'".format(str(object))


def update_message_in_db(message: discord.Message, guild_id: int):
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
            write_to_db(message.id, message.author.id, emoji, count_list[emoji], message.created_at, guild_id)
    else:
        cursor = get_cursor()
        cursor.execute("DELETE FROM {}_messages WHERE message_id = {}".format(guild_id, message.id)) # Delete if the message has no reactions
        cursor.close()
        

def write_to_db(message_id: int, author_id: int, emoji: str, count: int, time_sent: datetime, guild_id: int):
    '''Writes one row to the message database'''

    time_now = sql_string(datetime.utcnow())
    sendtime = sql_string(time_sent)
    table_name = "{}_messages".format(guild_id)

    cursor = get_cursor()
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
    db.commit()


def get_last_update_time(guild_id:int):
    '''Returns the time the last database update occurred as a datetime object'''

    cursor = get_cursor()
    cursor.execute("SELECT MAX(updatetime) FROM {}_messages".format(guild_id))
    time = cursor.fetchone()[0]    # Postgres' default time format can be automatically converted to a datetime
    cursor.close()
    return time
