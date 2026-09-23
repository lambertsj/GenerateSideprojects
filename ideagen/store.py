import difflib
import json
import sqlite3
from datetime import datetime


def open_db(path: str) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.execute("""CREATE TABLE IF NOT EXISTS ideas(
        id INTEGER PRIMARY KEY, run TEXT, created TEXT, title TEXT, idea TEXT, seed TEXT,
        status TEXT, gates TEXT, competition TEXT, kill_reason TEXT, warning TEXT)""")
    return con


def add(con, run, idea, seed) -> int:
    cur = con.execute(
        "INSERT INTO ideas(run, created, title, idea, seed, status) VALUES (?,?,?,?,?,?)",
        (run, datetime.now().isoformat(timespec="seconds"), idea.get("title", "untitled"),
         json.dumps(idea, ensure_ascii=False), json.dumps(seed, ensure_ascii=False), "generated"))
    con.commit()
    return cur.lastrowid


def update(con, rid, **fields):
    for k, v in fields.items():
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        con.execute(f"UPDATE ideas SET {k}=? WHERE id=?", (v, rid))
    con.commit()


def recent_titles(con, n=80):
    return [r[0] for r in con.execute("SELECT title FROM ideas ORDER BY id DESC LIMIT ?", (n,))]


def similar_existing(con, idea, threshold=0.78):
    new = (idea.get("title", "") + " " + idea.get("description", "")).lower()
    for title, raw in con.execute("SELECT title, idea FROM ideas"):
        old = (title + " " + json.loads(raw).get("description", "")).lower()
        if difflib.SequenceMatcher(None, new, old).ratio() > threshold:
            return title
    return None
