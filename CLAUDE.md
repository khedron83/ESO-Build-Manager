# ESO Build Manager

A KDE desktop app for storing and managing Elder Scrolls Online character builds. Built with Python and PySide6, integrating naturally with KDE Plasma via Qt's system theme.

## Tech Stack

- **Python 3.11+**
- **PySide6** — UI framework (Qt6, KDE Plasma compatible)
- **SQLite via sqlite3** — local build storage (stdlib, no ORM)
- **dataclasses** — data models

No external dependencies beyond PySide6.

## Running

```bash
pip install PySide6
python main.py
```

## Project Layout

```
eso-build-manager/
├── main.py
├── requirements.txt
├── eso_build_manager/
│   ├── app.py                       # QApplication setup
│   ├── constants.py                 # ESO_CLASSES, ROLES, GEAR_SLOTS, colors, etc.
│   ├── data_loader.py               # JSON data loaders (skills, sets, CP stars)
│   ├── exporter.py                  # Build export/import (JSON + plain text)
│   ├── models/
│   │   ├── build.py                 # Build dataclass
│   │   ├── skill.py                 # Skill dataclass
│   │   └── gear.py                  # GearPiece dataclass
│   ├── storage/
│   │   └── database.py              # SQLite CRUD — builds, skills, gear
│   └── ui/
│       ├── main_window.py           # MainWindow: sidebar + sheet splitter
│       ├── build_list.py            # QTreeWidget sidebar with role categories
│       ├── build_sheet.py           # Read-only build display (default view)
│       ├── build_editor_dialog.py   # Modeless QDialog wrapping BuildEditorPanel
│       ├── build_editor.py          # BuildEditorPanel — full edit form + tabs
│       ├── skill_bar_widget.py      # Two-bar skill widget (5 active + ULT × 2)
│       ├── cp_widget.py             # Champion Points 12-slot widget with drag-drop
│       ├── gear_table_widget.py     # GearTableWidget (14 slots) + GearPagesWidget (tabs of pages)
│       ├── class_mastery_widget.py  # Class Mastery passive checkboxes (U50+)
│       └── stats_widget.py          # StatsInputWidget (built but not currently used in UI)
└── data/
    ├── skills.json                  # Skill lines: category/line/base+morphs structure
    ├── skill_ids.json               # UESP ability IDs: {line: {name: ability_id}}
    ├── sets.json                    # [{id, name}] — 709 sets for autocomplete
    ├── set_details.json             # {name: {id, type, source, bonuses[]}} — tooltip data
    └── cp_skill_ids.json            # {discipline: {star_name: ability_id}} — 118 CP stars
```

## UI Flow

```
MainWindow (QMainWindow)
├── QSplitter (horizontal)
│   ├── BuildListPanel (left, 275px fixed)       — QTreeWidget grouped by role
│   │   ├── QLineEdit search
│   │   ├── QTreeWidget — role group headers → build children
│   │   └── Buttons: Add | Duplicate | Delete | Import JSON…
│   └── BuildSheetWidget (right, default)        — read-only display
│       ├── Header: name, badges (class/role/patch), Edit button, Export menu
│       ├── Skills section (two bars)
│       ├── Champion Points section (if any filled)
│       ├── Gear section
│       ├── Stats & Buffs section (health/magicka/stamina + food + mundus)
│       └── Notes section
│
└── BuildEditorDialog (modeless QDialog, independent window)
    └── BuildEditorPanel
        ├── Row 1: name | role | content | patch
        ├── Row 2: class | subclass toggle | sub1 | sub2
        ├── Row 3: source URL / name
        └── QTabWidget
            ├── "Build"    → QSplitter: SkillBarWidget / CPWidget / GearPagesWidget
            ├── "Stats"    → attribute pts, food, mundus stone, CP notes
            ├── "Passives" → ClassMasteryWidget
            └── "Notes"    → QPlainTextEdit
```

**Key UX patterns:**
- Default view is the read-only sheet; editing opens a separate modeless window
- Edit dialog has `parent=None` so it doesn't minimize with the main window
- 400ms debounced auto-save on every field change (`QTimer` + `_blocking` flag)
- `_blocking = True` during `load_build()` prevents signals triggering spurious saves

## Data Model

### Build

| Field              | Type  | Notes                                                        |
|--------------------|-------|--------------------------------------------------------------|
| `id`               | int   | SQLite rowid                                                 |
| `name`             | str   |                                                              |
| `description`      | str   | Unused in UI                                                 |
| `eso_class`        | str   | One of ESO_CLASSES                                           |
| `subclass_1/2`     | str   | Optional subclass names (same list as eso_class)             |
| `role`             | str   | Tank / Healer / MagDPS / StamDPS / Hybrid                   |
| `content`          | str   | Dungeon / Overland / PvP / Solo / Trial                      |
| `game_patch`       | str   | e.g. "U50"                                                   |
| `source`           | str   | URL or creator name (shown as hyperlink if starts with http) |
| `mundus_stone`     | str   | One of MUNDUS_STONES or empty                                |
| `food_buff`        | str   | Free text                                                    |
| `attribute_health` | int   | Points into Health (0–64)                                    |
| `attribute_magicka`| int   | Points into Magicka                                          |
| `attribute_stamina`| int   | Points into Stamina                                          |
| `champion_points`  | str   | Free-text CP notes                                           |
| `cp_slots`         | str   | JSON list[str] — 12 CP star names (4 per tree)               |
| `class_masteries`  | str   | JSON list[str] — selected Class Mastery passive names        |
| `gear_pages`        | str   | JSON list[str] — gear page names, e.g. `["Main"]` or `["Main","Trash","Boss"]` |
| `character_stats`  | str   | JSON dict — reserved, not shown in UI                        |
| `notes`            | str   |                                                              |
| `created_at/updated_at` | str | ISO 8601                                                |

### Skill

| Field      | Type | Notes                                               |
|------------|------|-----------------------------------------------------|
| `build_id` | int  | FK → Build                                          |
| `bar`      | int  | 0 = front bar, 1 = back bar                         |
| `slot`     | int  | 0–4 = active slots, 5 = ultimate                   |
| `name`     | str  | Skill name                                          |
| `notes`    | str  | Unused in UI                                        |

### GearPiece

| Field      | Type | Notes                                                          |
|------------|------|----------------------------------------------------------------|
| `build_id` | int  | FK → Build                                                     |
| `slot`     | str  | See GEAR_SLOTS                                                 |
| `set_name` | str  |                                                                |
| `weight`   | str  | Light / Medium / Heavy / — / N/A (off-hand = two-handed)       |
| `trait`    | str  | Varies by slot type (armor / weapon / jewelry trait lists)     |
| `enchant`  | str  | Free text                                                      |
| `quality`  | str  | Normal / Fine / Superior / Epic / Legendary                    |
| `page`     | int  | Index into the build's `gear_pages` list (0 = first page)     |

## Constants (`constants.py`)

```python
ESO_CLASSES   = ["Arcanist", "Dragonknight", "Necromancer", "Nightblade",
                  "Sorcerer", "Templar", "Warden"]
ROLES         = ["Healer", "Hybrid", "MagDPS", "StamDPS", "Tank"]
CONTENT_TYPES = ["Dungeon", "Overland", "PvP", "Solo", "Trial"]
GEAR_SLOTS    = ["Head", "Shoulder", "Chest", "Hands", "Waist", "Legs", "Feet",
                 "Neck", "Ring 1", "Ring 2",
                 "Main Hand", "Off Hand", "Backup Main", "Backup Off"]
ARMOR_WEIGHTS   = ["Heavy", "Light", "Medium"]
GEAR_TRAITS     = [...]   # 20 armor traits
JEWELRY_TRAITS  = [...]   # 9 jewelry traits
WEAPON_TRAITS   = [...]   # 9 weapon traits
QUALITY_TIERS   = ["Normal", "Fine", "Superior", "Epic", "Legendary"]
MUNDUS_STONES   = ["The Apprentice", ..., "The Warrior"]  # 13 stones
GAME_PATCHES    = ["U35", ..., "U50"]
ROLE_COLORS     = {role: hex_color}
CLASS_COLORS    = {class: hex_color}
QUALITY_COLORS  = {quality: hex_color}
```

## Data Files

### `skills.json`
Structured skill data from UESP. Format:
```json
[{"category": "Dragonknight", "line": "Ardent Flame", "skills": [
    {"base": "Lava Whip", "morphs": ["Flame Lash", "Molten Whip"]}
]}]
```
Used by `load_skill_names()` to build autocomplete lists. Also has `"category": "Class Mastery"` entries for U50+ class mastery passives.

### `skill_ids.json`
UESP ability IDs from the skillTree record. Format: `{line: {skill_name: ability_id}}`.
997 named skills across 71 lines including "Scribing" (12 grimoire skills).
Max-rank abilityId per named skill (morphs have rank > maxRank).

### `sets.json`
`[{"id": int, "name": str}]` — 709 sets for gear autocomplete.

### `set_details.json`
`{set_name: {"id": int, "type": str, "source": str, "bonuses": [str, ...]}}` — 711 sets.
Used for the tooltip on gear set cells (shows type, source, and per-piece bonus text).

### `cp_skill_ids.json`
`{"Craft": {star_name: ability_id}, "Warfare": {...}, "Fitness": {...}}`.
118 total CP v2 stars from UESP cp2Skills record.
Discipline mapping: id=1→Warfare, id=2→Fitness, id=3→Craft.

## Key Implementation Notes

### Gear table — off-hand slots
`Off Hand` and `Backup Off` have weight combos with `["—", "N/A"]` (enabled).
Selecting N/A disables and clears set/trait/enchant/quality for that row.
Build sheet shows "N/A (two-handed)" in italic when weight == "N/A".

### CP widget
12 slots (4 per tree: Craft / Warfare / Fitness). Drag-and-drop between slots via
custom MIME type `application/x-eso-cp-slot` and module-level `_cp_drag_source`.
Star names loaded lazily from `cp_skill_ids.json` via `_load_cp_trees()`.

### Skill bar widget
Drag-and-drop between slots via `application/x-eso-skill-slot`.
Autocomplete uses `load_skill_names()` which merges `skills.json` base+morphs
with all keys from `skill_ids.json` (includes Scribing skills).

### Gear pages (trash/boss loadouts)
`GearPagesWidget` (in `gear_table_widget.py`) wraps a `QTabWidget` of `GearTableWidget`
instances, one per page. Page names live on `Build.gear_pages` (JSON list, default
`["Main"]`); each `GearPiece.page` is the index into that list. `+`/`−` buttons in the
tab corner add/remove pages, double-click a tab to rename. `BuildSheetWidget._gear_section`
mirrors this read-only — only shows tabs when there's more than one page, so single-page
builds (the common case) look unchanged. `exporter.py` carries `gear_pages` and per-piece
`page` through JSON export/import and text export (adds a `GEAR — {page}` header per page).

### Set tooltips
`gear_table_widget._build_tooltip(name)` reads `set_details.json` and returns HTML.
Set via `Qt.ItemDataRole.ToolTipRole` on commit in `_SetDelegate.setModelData()`.

### Database migrations
New columns are added via `ALTER TABLE ... ADD COLUMN` in a try/except loop:
```python
_migrations = [("col_name", "TYPE DEFAULT value"), ...]
for col, definition in _migrations:
    try:
        conn.execute(f"ALTER TABLE builds ADD COLUMN {col} {definition}")
    except sqlite3.OperationalError:
        pass  # column already exists
```

### Color palette rules
- Readable text: `palette(windowText)`
- Secondary/muted text: `palette(placeholderText)`
- Decorative borders only: `palette(mid)` (too dark for text in KDE dark themes)
- Avoid `palette(mid)` for any text — invisible in KDE dark theme

## Export / Import (`exporter.py`)

**JSON export** (`export_build_dict`): complete build dict with `_eso_build_manager_version: 1`.
Includes all fields, skills list, and gear list. Saved via file dialog from the Export menu.

**Text export** (`export_build_text`): human-readable plain text with sections for
Skills, Champion Points, Gear, Stats & Buffs, Notes, Source. Copied to clipboard.

**Import** (`import_build_dict`): reads exported JSON dict, creates a new build in DB.
Triggered from "Import JSON…" button in the sidebar.

## Storage

Single SQLite file at `~/.local/share/eso-build-manager/builds.db`.
Window geometry saved to `~/.config/eso-build-manager/` via `QSettings("CubicSerenity", "ESOBuildManager")`.

## Nextcloud Sync (`sync/nextcloud.py`)

Two-way WebDAV sync to `ESO-Builds/` directory on Nextcloud.

- `NextcloudSync` — thin WebDAV wrapper (MKCOL, PROPFIND, PUT, GET) using `requests` + HTTP Basic Auth.
- `sync_all(syncer)` — uploads all local builds, downloads remote-only (or remote-newer same-name) builds.
- Each build stored as `ESO-Builds/{slug}.json`; slug derived from build name (spaces→underscores, special chars stripped).
- `_sync_updated_at` field added to uploaded JSON for timestamp-based conflict resolution.

**Settings** stored under `nextcloud/` keys in `QSettings("CubicSerenity", "ESOBuildManager")`:
`nextcloud/url`, `nextcloud/username`, `nextcloud/password`, `nextcloud/verify_ssl`.

**UI**: Nextcloud menu in main window — "Sync Now" (Ctrl+Shift+S) and "Settings…". Result shown in status bar.

## TODOs

### Build editor visual polish (vs. the read-only sheet) — IN PROGRESS, items 5-11 remain
The editor (`build_editor.py` + `build_editor_dialog.py` and its child widgets) was plain,
form-heavy Qt with none of the visual language established in `build_sheet.py` (colored
section labels, badge colors from `CLASS_COLORS`/`ROLE_COLORS`/`QUALITY_COLORS`, generous
card-style spacing). Suggestions gathered from a ui-designer review, most impactful first.
**Items 1-5 are done** (verified via offscreen-rendered screenshots); **6-11 are still open**
— pick up at 6 next.

1. ✅ DONE — Wrapped the top metadata rows (name/role/content/patch/class/subclass/source) in
   a `QFrame` header card (`palette(alternateBase)` background, `palette(mid)` border, rounded
   corners, 14/12px padding) with a closing `HLine` before the tabs, matching
   `build_sheet.py::_build_header`. See `build_editor.py` `__init__` (the `header_card`/
   `header_layout` block right after `outer = QVBoxLayout(self)`).
2. ✅ DONE — Name field bumped to hero-title weight: `+10pt` and `setBold(True)` on
   `self._name_edit`'s font in `build_editor.py` (was `+2pt`, not bold).
3. ✅ DONE — `skill_bar_widget.py` ("Front Bar"/"Back Bar") and `cp_widget.py`
   ("Craft"/"Warfare"/"Fitness") `QGroupBox` titles are now colored via a per-file
   `_accent_group_box_style(accent)` helper (`QGroupBox::title` selector only, so the
   accent color doesn't cascade into child widgets) using the same hex values
   `build_sheet.py` uses for these labels (bars: `#4a9eff`/`#f97316`; CP trees:
   `#4dbd74`/`#60a5fa`/`#f87171`).
4. ✅ DONE — Class/Role combos in `build_editor.py` now get a 3px colored left border via
   `_accent_combo_style(color)`, driven by `CLASS_COLORS`/`ROLE_COLORS.get(...)`. Wired through
   `_update_class_accent()`/`_update_role_accent()`, called on `currentIndexChanged` (in
   addition to the existing save/rebuild handlers — these two are unconditional, unlike the
   `_blocking`-guarded handlers, so the accent still updates during `load_build()`) and
   explicitly from `load_build()` right after the combos are populated. Placeholder state
   (`_PH_CLASS`/`_PH_ROLE`) resolves to no color match → stylesheet cleared → default look.
5. ✅ DONE — Gear table's Quality column (`gear_table_widget.py`) now colors the selected
   `QComboBox` text per `QUALITY_COLORS`, via a `_style_quality_combo(combo)` helper called on
   `currentIndexChanged` and after programmatic `setCurrentIndex` in `load()`.
6. Give CP slot handles a positional label (`cp_widget.py`) — currently always `""`, unlike
   the skill bar's "Slot 1"–"Ultimate" labels.
7. Give `class_mastery_widget.py`'s empty-state text ("No class selected...") a card/banner
   treatment — it's often the entire tab content and currently just one gray paragraph.
8. Double-check empty skill-slot placeholder contrast (`1px dashed palette(mid)` in
   `skill_bar_widget.py`) in KDE dark theme; consider `palette(midlight)` or a faint "+" affordance.
9. Move loadout pages' "+ Add / − Remove" buttons into `QTabWidget.setCornerWidget(...)`
   instead of a floating row above the tabs (`loadout_pages_widget.py:52-64`).
10. The modeless editor dialog has a static "Edit Build" title regardless of which build is
    open, and autosave is completely silent. Add a live title (`"Edit — {name}"`) and a small
    transient "Saved" indicator; also check whether reopening a build already being edited
    creates a second competing window instead of raising the existing one.
11. Style splitter handles (Loadout/CP in `build_editor.py`, skill bar/gear table in
    `loadout_pages_widget.py`) — default 1px handles give no visible resize affordance.

### Android app sync sees 0 builds despite desktop having builds on the server
`eso-build-manager-expo` can't use PROPFIND (Android platform limitation, see that repo's
CLAUDE.md), so it tracks synced files via a `_index.json` manifest instead of listing the
directory. This desktop app's `NextcloudSync`/`sync_all()` was never updated to read or write
that manifest — it only does real PROPFIND directory listing. Net effect: builds uploaded by
desktop are invisible to Android (not in `_index.json`), and Android reports `↓ 0` even when
the server has plenty of `.json` files sitting in `ESO-Builds/`. Fix is to make `sync_all()`
also populate/update `_index.json` on every upload, so both apps agree on the manifest instead
of desktop implicitly relying on PROPFIND alone.

### Gear card quality coloring reported still wrong after the Epic-color fix
Removed Epic from `_QUALITY_COLOR` in `build_sheet.py` (`_GearCard`) since virtually all
endgame gear is Epic quality and coloring 100% of items the same purple wasn't useful signal —
verified via offscreen render that Epic now shows plain text and Legendary still gets its gold
highlight. User reported "not fixed" immediately after, but this was in the same live session
as an earlier false alarm that turned out to be a stale, not-yet-restarted process (see the
Add/Remove Page button episode). Re-check after a full app restart before assuming the
`_QUALITY_COLOR` edit itself is wrong — if it's still off after a clean restart, the actual
cause is unconfirmed and needs fresh investigation, not a repeat of this fix.
