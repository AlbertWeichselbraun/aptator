"""Record and retrieve the state of installed packages."""

import sqlite3
from pathlib import Path

db_path = Path("~/.local/share/aptator/state.db").expanduser()
db_path.parent.mkdir(parents=True, exist_ok=True)

conn = sqlite3.connect(db_path)
conn.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        name TEXT PRIMARY KEY,
        installed_version TEXT NOT NULL
    )
""")


def get_installed_version(package_name: str) -> str | None:
    """Get the installed version of a package, or None if not installed."""
    row = conn.execute("SELECT installed_version FROM packages WHERE name = ?", (package_name,)).fetchone()
    return row[0] if row else None


def set_installed_version(package_name: str, version: str) -> None:
    """Set the installed version of the given package."""
    conn.execute(
        """
        INSERT INTO packages (name, installed_version)
        VALUES (?, ?)
        ON CONFLICT(name) DO UPDATE SET installed_version = excluded.installed_version
        """,
        (package_name, version),
    )
    conn.commit()
