import os
import psycopg2
from psycopg2.extras import DictCursor

if __name__ == "__main__":
    DATABASE_URL = os.environ['DATABASE_URL']
    db = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = db.cursor(cursor_factory=DictCursor)

    cursor.execute("IF (EXISTS (SELECT * FROM IMFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = messages)) BEGIN DROP TABLE messages END")

    cursor.execute("CREATE TABLE messages (message_id BIGINT, author_id BIGINT, emoji VARCHAR(128), count INT)")
    db.commit()