# Copyright (C) 2024 Nucleon Cyber. All rights reserved.
#
# This file is part of GenAIPot.
#
# GenAIPot is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# GenAIPot is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with GenAIPot. If not, see <http://www.gnu.org/licenses/>.
#
# For more information, visit: www.nucleon.sh or send email to contact[@]nucleon.sh
#

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