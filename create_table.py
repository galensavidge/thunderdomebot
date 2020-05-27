import os
import psycopg2
from psycopg2.extras import DictCursor

if __name__ == "__main__":
    DATABASE_URL = os.environ['DATABASE_URL']
    db = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = db.cursor(cursor_factory=DictCursor)

    print("Creating messages table...")

    # cursor.execute("DROP TABLE messages")

    cursor.execute("CREATE TABLE messages (message_id BIGINT, author_id BIGINT, emoji VARCHAR(128), count INT, sendtime TIMESTAMP, updatetime TIMESTAMP)")
    db.commit()

    cursor.close()
    db.cose()

    print("Done!")