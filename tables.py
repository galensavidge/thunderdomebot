import database

def create_guild_tables(guild_id):
    table_name = "messages_{}".format(guild_id)
    cursor = database.get_cursor()

    cursor.execute("SELECT to_regclass('{}')".format(table_name))
    table_exists = cursor.fetchone()[0]
    print("The table query was " + table_exists) #DEBUG
    if not table_exists:
        cursor.execute("CREATE TABLE {} (message_id BIGINT, author_id BIGINT, emoji VARCHAR(128), "
                        "count INT, sendtime TIMESTAMP, updatetime TIMESTAMP)".format(table_name))
        database.commit()

        print("Successfully created table ", table_name)

        cursor.close()
        database.close()
