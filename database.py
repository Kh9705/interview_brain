import aiosqlite
import config

_db_connection: aiosqlite.Connection | None = None


async def get_db() -> aiosqlite.Connection:
    """Return the shared database connection, creating it on first call."""
    global _db_connection
    if _db_connection is None:
        _db_connection = await aiosqlite.connect(config.DATABASE_URL)
        _db_connection.row_factory = aiosqlite.Row
    return _db_connection


async def init_db() -> None:
    """Create all tables if they do not already exist."""
    db = await get_db()

    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT '',
            companies TEXT NOT NULL DEFAULT '[]',
            weak_areas TEXT NOT NULL DEFAULT '[]',
            created_at TEXT NOT NULL
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS feedback (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            company TEXT NOT NULL,
            topic TEXT NOT NULL,
            result TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS mock_interviews (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            company TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT '',
            overall_score REAL NOT NULL DEFAULT 0.0,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS mock_questions (
            id TEXT PRIMARY KEY,
            interview_id TEXT NOT NULL,
            question_number INTEGER NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL DEFAULT '',
            score REAL NOT NULL DEFAULT 0.0,
            feedback TEXT NOT NULL DEFAULT '',
            FOREIGN KEY (interview_id) REFERENCES mock_interviews(id)
        )
    """)

    await db.execute("""
        CREATE TABLE IF NOT EXISTS roadmaps (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            company TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    await db.commit()


async def close_db() -> None:
    """Close the shared database connection."""
    global _db_connection
    if _db_connection is not None:
        await _db_connection.close()
        _db_connection = None
