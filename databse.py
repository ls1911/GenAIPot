import sqlite3
from datetime import datetime
import pandas as pd

conn = sqlite3.connect('GenAIPot.db')
c = conn.cursor()

def setup_database():
    c.execute('''
        CREATE TABLE IF NOT EXISTS connections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ip TEXT,
            timestamp TEXT,
            command TEXT,
            response TEXT
        )
    ''')
    conn.commit()

def log_interaction(ip, command, response):
    c.execute('INSERT INTO connections (ip, timestamp, command, response) VALUES (?, ?, ?, ?)',
              (ip, datetime.now().isoformat(), command, response))
    conn.commit()

def collect_honeypot_data():
    return pd.read_sql_query("SELECT * FROM connections", conn)