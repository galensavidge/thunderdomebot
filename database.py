import discord
import os
import psycopg2
from psycopg2.extras import DictCursor
from datetime import datetime

DATABASE_URL = os.environ['DATABASE_URL']
db = psycopg2.connect(DATABASE_URL, sslmode='require')


def close():
    db.close()


def get_cursor():
    return db.cursor(cursor_factory=DictCursor)


def sql_string(object):
    return "\'{}\'".format(str(object))


def update_message_in_db(message: discord.Message):
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
            write_to_db(message.id, message.author.id, emoji, count_list[emoji])
    else:
        cursor = get_cursor()
        cursor.execute("DELETE FROM messages WHERE message_id = {}".format(message.id)) # Delete if the message has no reactions
        cursor.close()
        

def write_to_db(message_id: int, author_id: int, emoji: str, count: int):
    '''Writes one row to the message database'''

    time_now = sql_string(datetime.now())

    cursor = get_cursor()
    cursor.execute("SELECT emoji FROM messages WHERE message_id = {} AND emoji = {}".format(message_id, emoji))
    entry = cursor.fetchone()
    if entry is not None:
        if count > 0:
            cursor.execute("UPDATE messages SET count = {}, updatetime = {} WHERE message_id = {} AND emoji = {}".format(count, time_now, message_id, emoji))
        else:
            cursor.execute("DELETE FROM messages WHERE message_id = {} AND emoji = {}".format(message_id, emoji))
    elif count > 0:
            cursor.execute("INSERT into messages (message_id, author_id, emoji, count, updatetime) values ({}, {}, {}, {}, {})".format(message_id, author_id, emoji, count, time_now))
    
    cursor.close()
    db.commit()


def get_last_update_time():
    '''Returns the time the last database update occurred as a datetime object'''

    cursor = get_cursor()
    cursor.execute("SELECT MAX(updatetime) FROM messages")
    time = cursor.fetchone()    # Postgres defaults to ISO 8601 format (yyyy-mm-dd hh:mm:ss.uuuuuu[timezone])
    cursor.close()
    return datetime.strptime(time, "%Y-%m-%d %H-%M-%S.%f")