"""SQLite transactions own project revisions and durable job transitions."""

import hashlib
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager

from .settings import Settings


class Conflict(ValueError):
    pass


class Store:
    def __init__(self, settings: Settings):
        self.settings = settings
        settings.data.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.path = settings.contained("studio.sqlite3")
        with self.connect() as db:
            db.executescript("""
              PRAGMA journal_mode=WAL;
              CREATE TABLE IF NOT EXISTS projects(id TEXT PRIMARY KEY, owner TEXT NOT NULL,
                body TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, updated REAL NOT NULL);
              CREATE TABLE IF NOT EXISTS assets(id TEXT PRIMARY KEY, owner TEXT NOT NULL,
                name TEXT NOT NULL, kind TEXT NOT NULL, size INTEGER NOT NULL,
                sha256 TEXT NOT NULL, extension TEXT NOT NULL);
              CREATE TABLE IF NOT EXISTS jobs(id TEXT PRIMARY KEY, owner TEXT NOT NULL,
                project_id TEXT NOT NULL, body TEXT NOT NULL, fingerprint TEXT NOT NULL,
                state TEXT NOT NULL CHECK(state IN ('queued','running','complete','failed','cancelled','interrupted')),
                progress REAL NOT NULL DEFAULT 0, message TEXT NOT NULL DEFAULT '', created REAL NOT NULL,
                UNIQUE(owner,fingerprint));
              CREATE INDEX IF NOT EXISTS project_owner ON projects(owner,updated);
              CREATE INDEX IF NOT EXISTS asset_owner ON assets(owner);
              CREATE INDEX IF NOT EXISTS job_queue ON jobs(state,created);
              PRAGMA user_version=1;
            """)

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def projects(self, owner):
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT id,body,revision,updated FROM projects WHERE owner=? ORDER BY updated DESC LIMIT ?",
                    (owner, self.settings.config["storage"]["projects"]),
                )
            ]

    def project(self, owner, ident):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM projects WHERE id=? AND owner=?", (ident, owner)
            ).fetchone()
            return dict(row) if row else None

    def save(self, owner, body, ident=None, revision=None):
        text = json.dumps(body, sort_keys=True)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if ident:
                result = db.execute(
                    "UPDATE projects SET body=?,revision=revision+1,updated=? WHERE id=? AND owner=? AND revision=?",
                    (text, time.time(), ident, owner, revision),
                )
                if result.rowcount != 1:
                    raise Conflict("Project changed in another session; reload before saving")
            else:
                count = db.execute(
                    "SELECT count(*) FROM projects WHERE owner=?", (owner,)
                ).fetchone()[0]
                if count >= self.settings.config["storage"]["projects"]:
                    raise ValueError("Project quota reached")
                ident = uuid.uuid4().hex
                db.execute(
                    "INSERT INTO projects(id,owner,body,updated) VALUES(?,?,?,?)",
                    (ident, owner, text, time.time()),
                )
        return self.project(owner, ident)

    def assets(self, owner):
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM assets WHERE owner=? ORDER BY rowid DESC LIMIT 1000", (owner,)
                )
            ]

    def asset(self, owner, ident):
        with self.connect() as db:
            row = db.execute(
                "SELECT * FROM assets WHERE owner=? AND id=?", (owner, ident)
            ).fetchone()
            return dict(row) if row else None

    def add_asset(self, record):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            used = db.execute(
                "SELECT coalesce(sum(size),0) FROM assets WHERE owner=?", (record[1],)
            ).fetchone()[0]
            if used + record[4] > self.settings.config["storage"]["account_bytes"]:
                raise ValueError("Account storage quota reached")
            db.execute("INSERT INTO assets VALUES(?,?,?,?,?,?,?)", record)

    def enqueue(self, owner, project, request_id):
        fingerprint = hashlib.sha256(
            (project["id"] + str(project["revision"]) + request_id).encode()
        ).hexdigest()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM jobs WHERE owner=? AND fingerprint=?", (owner, fingerprint)
            ).fetchone()
            if row:
                return dict(row)
            count = db.execute("SELECT count(*) FROM jobs WHERE owner=?", (owner,)).fetchone()[0]
            if count >= self.settings.config["storage"]["jobs"]:
                raise ValueError("Job quota reached")
            ident = uuid.uuid4().hex
            db.execute(
                "INSERT INTO jobs(id,owner,project_id,body,fingerprint,state,created) VALUES(?,?,?,?,?,'queued',?)",
                (ident, owner, project["id"], project["body"], fingerprint, time.time()),
            )
            return dict(db.execute("SELECT * FROM jobs WHERE id=?", (ident,)).fetchone())

    def jobs(self, owner):
        with self.connect() as db:
            return [
                dict(r)
                for r in db.execute(
                    "SELECT id,project_id,state,progress,message,created FROM jobs WHERE owner=? ORDER BY created DESC LIMIT 100",
                    (owner,),
                )
            ]

    def job(self, owner, ident):
        with self.connect() as db:
            row = db.execute("SELECT * FROM jobs WHERE id=? AND owner=?", (ident, owner)).fetchone()
            return dict(row) if row else None

    def next_job(self):
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute(
                "SELECT * FROM jobs WHERE state='queued' ORDER BY created LIMIT 1"
            ).fetchone()
            if not row:
                return None
            db.execute(
                "UPDATE jobs SET state='running' WHERE id=? AND state='queued'", (row["id"],)
            )
            return dict(row)

    def update_job(self, ident, state, progress, message):
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET state=?,progress=?,message=? WHERE id=? AND state!='cancelled'",
                (state, progress, message, ident),
            )

    def cancel(self, owner, ident):
        with self.connect() as db:
            return (
                db.execute(
                    "UPDATE jobs SET state='cancelled',message='Cancelled by owner' WHERE id=? AND owner=? AND state IN ('queued','running')",
                    (ident, owner),
                ).rowcount
                == 1
            )

    def recover(self):
        with self.connect() as db:
            db.execute(
                "UPDATE jobs SET state='interrupted',message='Worker stopped; previous artifacts retained. Retry as a new job.' WHERE state='running'"
            )
