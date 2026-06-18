import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from eso_build_manager.constants import GEAR_SLOTS
from eso_build_manager.models.build import Build
from eso_build_manager.models.gear import GearPiece
from eso_build_manager.models.skill import Skill

DB_DIR = Path.home() / ".local" / "share" / "eso-build-manager"
DB_PATH = DB_DIR / "builds.db"


def _connect() -> sqlite3.Connection:
    DB_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS builds (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL DEFAULT 'New Build',
                description TEXT DEFAULT '',
                eso_class TEXT DEFAULT '',
                subclass_1 TEXT DEFAULT '',
                subclass_2 TEXT DEFAULT '',
                role TEXT DEFAULT '',
                content TEXT DEFAULT '',
                attribute_health INTEGER DEFAULT 0,
                attribute_magicka INTEGER DEFAULT 0,
                attribute_stamina INTEGER DEFAULT 64,
                food_buff TEXT DEFAULT '',
                game_patch TEXT DEFAULT 'U50',
                source TEXT DEFAULT '',
                character_stats TEXT DEFAULT '{}',
                champion_points TEXT DEFAULT '',
                cp_slots TEXT DEFAULT '',
                class_masteries TEXT DEFAULT '',
                notes TEXT DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS skills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id INTEGER NOT NULL REFERENCES builds(id) ON DELETE CASCADE,
                bar INTEGER NOT NULL,
                slot INTEGER NOT NULL,
                name TEXT DEFAULT '',
                notes TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS gear (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                build_id INTEGER NOT NULL REFERENCES builds(id) ON DELETE CASCADE,
                slot TEXT NOT NULL,
                set_name TEXT DEFAULT '',
                weight TEXT DEFAULT '',
                trait TEXT DEFAULT '',
                enchant TEXT DEFAULT '',
                quality TEXT DEFAULT 'Epic'
            );
        """)
        _migrations = [
            ("subclass_1",    "TEXT DEFAULT ''"),
            ("subclass_2",    "TEXT DEFAULT ''"),
            ("class_masteries","TEXT DEFAULT ''"),
            ("cp_slots",      "TEXT DEFAULT ''"),
            ("game_patch",    "TEXT DEFAULT 'U50'"),
            ("source",        "TEXT DEFAULT ''"),
            ("character_stats", "TEXT DEFAULT '{}'"),
            ("mundus_stone",  "TEXT DEFAULT ''"),
        ]
        for col, definition in _migrations:
            try:
                conn.execute(f"ALTER TABLE builds ADD COLUMN {col} {definition}")
            except sqlite3.OperationalError:
                pass  # column already exists


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def list_builds() -> list[tuple[int, str]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name FROM builds ORDER BY updated_at DESC"
        ).fetchall()
        return [(r["id"], r["name"]) for r in rows]


def list_builds_meta() -> list[tuple[int, str, str, str, str]]:
    """Returns (id, name, role, eso_class, content) sorted by updated_at DESC."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT id, name, role, eso_class, content FROM builds ORDER BY updated_at DESC"
        ).fetchall()
        return [(r["id"], r["name"], r["role"], r["eso_class"], r["content"] or "") for r in rows]


def get_build(build_id: int) -> Optional[Build]:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM builds WHERE id = ?", (build_id,)
        ).fetchone()
        if row is None:
            return None
        return Build(**{k: row[k] for k in row.keys()})


def create_build(build: Build) -> int:
    now = _now()
    with _connect() as conn:
        cur = conn.execute(
            """INSERT INTO builds
               (name, description, eso_class, subclass_1, subclass_2, role, content,
                attribute_health, attribute_magicka, attribute_stamina,
                food_buff, mundus_stone, game_patch, source, character_stats,
                champion_points, cp_slots, class_masteries, notes, created_at, updated_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (build.name, build.description, build.eso_class,
             build.subclass_1, build.subclass_2,
             build.role, build.content, build.attribute_health, build.attribute_magicka,
             build.attribute_stamina, build.food_buff, build.mundus_stone,
             build.game_patch, build.source, build.character_stats,
             build.champion_points, build.cp_slots, build.class_masteries,
             build.notes, now, now),
        )
        build_id = cur.lastrowid
        _seed_gear(conn, build_id)
        return build_id


def _seed_gear(conn: sqlite3.Connection, build_id: int) -> None:
    conn.executemany(
        "INSERT INTO gear (build_id, slot) VALUES (?, ?)",
        [(build_id, slot) for slot in GEAR_SLOTS],
    )


def update_build(build: Build) -> None:
    with _connect() as conn:
        conn.execute(
            """UPDATE builds SET
               name=?, description=?, eso_class=?, subclass_1=?, subclass_2=?,
               role=?, content=?,
               attribute_health=?, attribute_magicka=?, attribute_stamina=?,
               food_buff=?, mundus_stone=?, game_patch=?, source=?, character_stats=?,
               champion_points=?, cp_slots=?, class_masteries=?, notes=?, updated_at=?
               WHERE id=?""",
            (build.name, build.description, build.eso_class,
             build.subclass_1, build.subclass_2,
             build.role, build.content, build.attribute_health, build.attribute_magicka,
             build.attribute_stamina, build.food_buff, build.mundus_stone,
             build.game_patch, build.source, build.character_stats,
             build.champion_points, build.cp_slots, build.class_masteries,
             build.notes, _now(), build.id),
        )


def delete_build(build_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM builds WHERE id = ?", (build_id,))


def duplicate_build(build_id: int) -> int:
    build = get_build(build_id)
    if build is None:
        raise ValueError(f"Build {build_id} not found")
    skills = get_skills(build_id)
    gear = get_gear(build_id)

    build.id = None
    build.name = f"{build.name} (Copy)"
    new_id = create_build(build)

    for s in skills:
        s.id = None
        s.build_id = new_id
    save_skills(new_id, skills)

    for g in gear:
        g.id = None
        g.build_id = new_id
    save_gear(new_id, gear)

    return new_id


def get_skills(build_id: int) -> list[Skill]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM skills WHERE build_id = ? ORDER BY bar, slot",
            (build_id,),
        ).fetchall()
        return [Skill(**{k: r[k] for k in r.keys()}) for r in rows]


def save_skills(build_id: int, skills: list[Skill]) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM skills WHERE build_id = ?", (build_id,))
        conn.executemany(
            "INSERT INTO skills (build_id, bar, slot, name, notes) VALUES (?,?,?,?,?)",
            [(s.build_id, s.bar, s.slot, s.name, s.notes) for s in skills],
        )


def get_gear(build_id: int) -> list[GearPiece]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM gear WHERE build_id = ? ORDER BY id", (build_id,)
        ).fetchall()
        return [GearPiece(**{k: r[k] for k in r.keys()}) for r in rows]


def save_gear(build_id: int, gear: list[GearPiece]) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM gear WHERE build_id = ?", (build_id,))
        conn.executemany(
            """INSERT INTO gear (build_id, slot, set_name, weight, trait, enchant, quality)
               VALUES (?,?,?,?,?,?,?)""",
            [(g.build_id, g.slot, g.set_name, g.weight, g.trait, g.enchant, g.quality)
             for g in gear],
        )
