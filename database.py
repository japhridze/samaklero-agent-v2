import sqlite3
import os

DB_PATH = "clients.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id TEXT UNIQUE NOT NULL,
            page_token TEXT NOT NULL,
            sheet_id TEXT NOT NULL,
            company_name TEXT,
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_client(page_id, page_token, sheet_id, company_name=""):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO clients 
        (page_id, page_token, sheet_id, company_name)
        VALUES (?, ?, ?, ?)
    ''', (page_id, page_token, sheet_id, company_name))
    conn.commit()
    conn.close()

def get_client(page_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM clients WHERE page_id = ? AND active = 1', (page_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            "id": row[0],
            "page_id": row[1],
            "page_token": row[2],
            "sheet_id": row[3],
            "company_name": row[4],
            "active": row[5]
        }
    return None

def get_all_clients():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, page_id, company_name, active, created_at FROM clients')
    rows = c.fetchall()
    conn.close()
    return rows

def delete_client(page_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE clients SET active = 0 WHERE page_id = ?', (page_id,))
    conn.commit()
    conn.close()

init_db()