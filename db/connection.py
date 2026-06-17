import os
from contextlib import contextmanager

import psycopg2
from dotenv import load_dotenv

load_dotenv()


@contextmanager
def get_db_connection():
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        yield conn
    finally:
        conn.close()
