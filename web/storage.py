import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data.db"


def _conn() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con


def init_db() -> None:
    with _conn() as con:
        con.executescript("""
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                period_from TEXT,
                period_to TEXT,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS leads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_date TEXT,
                source TEXT,               -- форма / telegram / звонок
                campaign_name TEXT,
                keyword TEXT,
                is_qualified INTEGER,      -- 1=целевой, 0=нецелевой
                rejection_reason TEXT,
                notes TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                message TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS action_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                action TEXT NOT NULL,
                details TEXT,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            );
        """)


# ── Reports ──────────────────────────────────────────────────────────────────

def save_report(title: str, content: str, period_from: str = "", period_to: str = "") -> int:
    with _conn() as con:
        cur = con.execute(
            "INSERT INTO reports (title, period_from, period_to, content) VALUES (?,?,?,?)",
            (title, period_from, period_to, content),
        )
        return cur.lastrowid


def get_reports(limit: int = 20) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT id, title, period_from, period_to, created_at FROM reports ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_report(report_id: int) -> dict | None:
    with _conn() as con:
        row = con.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    return dict(row) if row else None


# ── Leads ─────────────────────────────────────────────────────────────────────

def save_lead(
    source: str,
    is_qualified: bool,
    lead_date: str = "",
    campaign_name: str = "",
    keyword: str = "",
    rejection_reason: str = "",
    notes: str = "",
) -> int:
    with _conn() as con:
        cur = con.execute(
            """INSERT INTO leads
               (lead_date, source, campaign_name, keyword, is_qualified, rejection_reason, notes)
               VALUES (?,?,?,?,?,?,?)""",
            (lead_date or datetime.now().date().isoformat(),
             source, campaign_name, keyword,
             1 if is_qualified else 0,
             rejection_reason, notes),
        )
        return cur.lastrowid


def get_leads(limit: int = 100, qualified_only: bool | None = None) -> list[dict]:
    with _conn() as con:
        if qualified_only is None:
            rows = con.execute(
                "SELECT * FROM leads ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT * FROM leads WHERE is_qualified=? ORDER BY id DESC LIMIT ?",
                (1 if qualified_only else 0, limit),
            ).fetchall()
    return [dict(r) for r in rows]


def get_lead_stats() -> dict:
    with _conn() as con:
        total = con.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        qualified = con.execute("SELECT COUNT(*) FROM leads WHERE is_qualified=1").fetchone()[0]

        by_source = con.execute(
            "SELECT source, COUNT(*) as cnt, SUM(is_qualified) as qual FROM leads GROUP BY source"
        ).fetchall()

        by_reason = con.execute(
            "SELECT rejection_reason, COUNT(*) as cnt FROM leads WHERE is_qualified=0 AND rejection_reason!='' GROUP BY rejection_reason ORDER BY cnt DESC"
        ).fetchall()

    return {
        "total": total,
        "qualified": qualified,
        "not_qualified": total - qualified,
        "qualified_pct": round(qualified / total * 100, 1) if total > 0 else 0,
        "by_source": [dict(r) for r in by_source],
        "rejection_reasons": [dict(r) for r in by_reason],
    }


# ── Feedback ──────────────────────────────────────────────────────────────────

def save_feedback(message: str) -> int:
    with _conn() as con:
        cur = con.execute("INSERT INTO feedback (message) VALUES (?)", (message,))
        return cur.lastrowid


def get_feedback(limit: int = 50) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM feedback ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Action log ────────────────────────────────────────────────────────────────

def log_action(action: str, details: dict | None = None) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO action_log (action, details) VALUES (?,?)",
            (action, json.dumps(details or {}, ensure_ascii=False)),
        )


def get_action_log(limit: int = 100) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM action_log ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        try:
            d["details"] = json.loads(d["details"])
        except Exception:
            pass
        result.append(d)
    return result


# ── Recommendations ──────────────────────────────────────────────────────────

def save_recommendation(content: str) -> int:
    with _conn() as con:
        cur = con.execute("INSERT INTO recommendations (content) VALUES (?)", (content,))
        return cur.lastrowid


def get_recommendations(limit: int = 10) -> list[dict]:
    with _conn() as con:
        rows = con.execute(
            "SELECT * FROM recommendations ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# Инициализируем БД при импорте
init_db()
