#!/usr/bin/env python3
"""ESO Build Manager — character stats viewer + build editor."""
import os, sys, subprocess, shutil, time
from datetime import datetime

from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, QSettings, QSortFilterProxyModel, Signal
from PySide6.QtGui import QAction, QColor, QFont, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout, QHBoxLayout,
    QStatusBar, QPushButton, QTabWidget, QTableView, QHeaderView,
    QSplitter, QComboBox, QLabel, QFrame, QGroupBox, QListWidget,
    QListWidgetItem, QStackedWidget, QTreeWidgetItem, QGridLayout,
    QScrollArea, QSizePolicy,
)
from eso_build_manager.app import create_app
from eso_build_manager.ui.build_list import BuildListPanel
from eso_build_manager.ui.build_sheet import BuildSheetWidget
from eso_build_manager.ui.build_editor_dialog import BuildEditorDialog
from eso_build_manager.data_loader import skill_icon_url
from eso_build_manager.icon_cache import fetch_icon
from eso_build_manager.storage import database as build_db
from eso_build_manager.models.build import Build
from eso_build_manager.models.skill import Skill
from eso_build_manager.models.gear import GearPiece
from eso_build_manager.constants import CLASS_COLORS

# Scribed skills have custom names with no UESP icon; fall back to Mages Guild grimoire book
_SCRIBING_FALLBACK_URL = skill_icon_url("Ulfsild's Contingency")
import json
import parser as lua_parser
import model

_DIR        = os.path.dirname(os.path.abspath(__file__))
LOCAL_FILE  = os.path.join(_DIR, 'LeoAltholic.lua')
WW_FILE       = os.path.join(_DIR, 'WizardsWardrobe.lua')
WORN_FILE     = os.path.join(_DIR, 'WornGear.lua')
SETS_DB_FILE  = os.path.join(_DIR, 'data', 'sets.json')


_ZEUS_SV = (
    '/home/kane/.local/share/Steam/steamapps/compatdata/306130/pfx/drive_c'
    '/users/steamuser/Documents/Elder Scrolls Online/live/SavedVariables'
)
_SYNC_FILES = ['LeoAltholic.lua', 'WizardsWardrobe.lua', 'WornGear.lua']

def _sync_from_zeus() -> None:
    # 'this_pc' mode reads save files straight off local disk instead of scp-ing
    # over the network — for when the game and the build manager are running on
    # the same machine (e.g. streaming from this PC). Set in Options…
    sync_mode = QSettings().value('sync/mode', 'zeus')
    if sync_mode == 'this_pc':
        for fname in _SYNC_FILES:
            try:
                shutil.copy(os.path.join(_ZEUS_SV, fname), os.path.join(_DIR, fname))
            except Exception:
                pass
        return
    for fname in _SYNC_FILES:
        try:
            subprocess.run(
                ['scp', '-q', f'zeus:{_ZEUS_SV}/{fname}', os.path.join(_DIR, fname)],
                timeout=8, capture_output=True,
            )
        except Exception:
            pass


def load_data() -> list[model.Character]:
    # Per character: WornGear data if that char has logged in since the rewrite, else LeoAltholic.
    chars = {}
    if os.path.exists(LOCAL_FILE):
        chars = {c.name: c for c in model.extract(lua_parser.load(open(LOCAL_FILE, encoding='utf-8').read()))}
    worn_lua = lua_parser.load(open(WORN_FILE, encoding='utf-8').read()) if os.path.exists(WORN_FILE) else {}
    for c in model.extract_from_wg(worn_lua):
        chars[c.name] = c
    return sorted(chars.values(), key=lambda c: c.name)


def load_ww_setups() -> dict[str, list[model.WWSetup]]:
    if not os.path.exists(WW_FILE):
        return {}
    with open(SETS_DB_FILE) as f:
        sets_db = {s['id']: s['name'] for s in json.load(f)}
    text = open(WW_FILE, encoding='utf-8').read()
    return model.extract_ww(lua_parser.load(text), sets_db)


def load_worn_gear() -> dict[str, dict]:
    if not os.path.exists(WORN_FILE):
        return {}
    return model.extract_worn_gear(lua_parser.load(open(WORN_FILE, encoding='utf-8').read()))


def _fmt_time(s: int) -> str:
    return f'{s//3600:,}h {(s%3600)//60}m'

def _n(v: int) -> str:
    return f'{v:,}' if v else '—'


def _fmt_updated(ts: int) -> str:
    if not ts:
        return 'Unknown'
    delta = int(time.time()) - ts
    if delta < 60:          return 'just now'
    if delta < 3600:        return f'{delta // 60}m ago'
    if delta < 86400:       return f'{delta // 3600}h ago'
    return f'{delta // 86400}d ago'


# ── table model with raw sort values ─────────────────────────────────────────

class CharTable(QAbstractTableModel):
    """Each cell holds (display_str, sort_value, tooltip, color|None)."""
    def __init__(self, headers: list[str], rows: list[list[tuple]],
                 col_colors: dict[int, QColor] | None = None):
        super().__init__()
        self._headers   = headers
        self._rows      = rows
        self._col_colors = col_colors or {}

    def rowCount(self, _=QModelIndex()):    return len(self._rows)
    def columnCount(self, _=QModelIndex()): return len(self._headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self._headers[section]

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid():
            return None
        cell = self._rows[index.row()][index.column()]
        if role == Qt.DisplayRole:   return cell[0]
        if role == Qt.UserRole:      return cell[1]
        if role == Qt.ToolTipRole:   return cell[2]
        if role == Qt.ForegroundRole:
            if len(cell) > 3 and cell[3]:
                return cell[3]
            return self._col_colors.get(index.column())
        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter if index.column() == 0 else Qt.AlignCenter
        return None


class SortProxy(QSortFilterProxyModel):
    def lessThan(self, left, right):
        lv = self.sourceModel().data(left,  Qt.UserRole)
        rv = self.sourceModel().data(right, Qt.UserRole)
        try:
            return (lv or 0) < (rv or 0)
        except TypeError:
            return str(lv or '') < str(rv or '')


def _cell(display, sort=None, tip=None, color=None):
    return (str(display) if display is not None else '—',
            sort if sort is not None else display,
            tip, color)


def _make_view(tbl: CharTable) -> QTableView:
    proxy = SortProxy()
    proxy.setSourceModel(tbl)

    tv = QTableView()
    tv.setModel(proxy)
    tv.setSortingEnabled(True)
    tv.setAlternatingRowColors(False)
    tv.setSelectionBehavior(QTableView.SelectRows)
    tv.verticalHeader().setVisible(False)
    tv.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
    tv.setShowGrid(False)
    tv.setWordWrap(False)
    tv.setStyleSheet("""
        QTableView { border: none; }
        QTableView::item { padding: 3px 8px; border-bottom: 1px solid rgba(128,128,128,0.12); }
        QTableView::item:selected { background: rgba(96,165,250,0.18); }
    """)

    f = QFont(); f.setPointSize(9); tv.setFont(f)

    hh = tv.horizontalHeader()
    hh.setDefaultAlignment(Qt.AlignCenter)
    hh.setSectionResizeMode(0, QHeaderView.ResizeToContents)
    for i in range(1, tbl.columnCount()):
        hh.setSectionResizeMode(i, QHeaderView.Stretch)
    hh.setStretchLastSection(False)
    hh.setStyleSheet("QHeaderView::section { border: none; border-bottom: 2px solid palette(highlight); padding: 4px 8px; }")

    tv.sortByColumn(0, Qt.SortOrder.AscendingOrder)
    return tv


# ── tab builders ──────────────────────────────────────────────────────────────

def _bio_card(c: model.Character) -> QFrame:
    card = QFrame()
    card.setStyleSheet("""
        QFrame#bioCard {
            border: 1px solid rgba(128,128,128,0.3);
            border-radius: 10px;
            background: rgba(255,255,255,0.03);
        }
        QFrame#bioCard QLabel { border: none; background: transparent; }
    """)
    card.setObjectName("bioCard")

    vbox = QVBoxLayout(card)
    vbox.setContentsMargins(16, 14, 16, 14)
    vbox.setSpacing(6)

    # Name + class badge
    top = QHBoxLayout(); top.setSpacing(8)
    name_lbl = QLabel(c.name)
    f = name_lbl.font(); f.setPointSize(f.pointSize() + 4); f.setBold(True)
    name_lbl.setFont(f)
    top.addWidget(name_lbl, 1)
    if c.class_name:
        color = CLASS_COLORS.get(c.class_name, '#556677')
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        fg = '#111' if (0.299*r + 0.587*g + 0.114*b) > 140 else '#fff'
        badge = QLabel(f'  {c.class_name}  ')
        badge.setStyleSheet(f'background:{color};color:{fg};border-radius:10px;'
                            'padding:3px 0;font-size:10px;font-weight:600;')
        badge.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)
        top.addWidget(badge)
    vbox.addLayout(top)

    # Race · Faction · Last updated
    sub_row = QHBoxLayout(); sub_row.setSpacing(8)
    sub = QLabel(f'{c.race_name}  ·  {c.faction_name}')
    sub.setStyleSheet('color: palette(placeholderText); font-size: 11px;')
    sub_row.addWidget(sub, 1)
    updated_lbl = QLabel(f'Updated {_fmt_updated(c.last_updated)}')
    updated_lbl.setStyleSheet('color: palette(placeholderText); font-size: 10px;')
    updated_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
    if c.last_updated:
        updated_lbl.setToolTip(datetime.fromtimestamp(c.last_updated).strftime('%Y-%m-%d %H:%M:%S'))
    sub_row.addWidget(updated_lbl)
    vbox.addLayout(sub_row)

    # Divider
    hr = QFrame(); hr.setFrameShape(QFrame.Shape.HLine)
    hr.setStyleSheet('QFrame { color: rgba(128,128,128,0.25); }')
    vbox.addWidget(hr)

    # Stats as key→value rows
    cp_str = f'{c.champion_points:,} CP' if c.champion_points else f'Level {c.level}'
    rows = [
        (cp_str,                       f'{_n(c.gold)} gold'),
        (f'{_n(c.ap)} AP',             f'{_n(c.telvar)} Tel Var'),
        (f'{c.skill_points_unspent} SP unspent', f'{_n(c.writ_vouchers)} vouchers'),
        (_fmt_time(c.seconds_played),  ''),
    ]
    stat_grid = QGridLayout(); stat_grid.setSpacing(2)
    for row_i, (left, right) in enumerate(rows):
        l = QLabel(left); l.setStyleSheet('font-size: 11px;')
        stat_grid.addWidget(l, row_i, 0)
        if right:
            r = QLabel(right)
            r.setStyleSheet('font-size: 11px; color: palette(placeholderText);')
            r.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            stat_grid.addWidget(r, row_i, 1)
    stat_grid.setColumnStretch(0, 1); stat_grid.setColumnStretch(1, 1)
    vbox.addLayout(stat_grid)

    return card


def _tab_bio(chars: list[model.Character]) -> QScrollArea:
    scroll = QScrollArea()
    scroll.setWidgetResizable(True)
    scroll.setFrameShape(QFrame.Shape.NoFrame)

    container = QWidget()
    grid = QGridLayout(container)
    grid.setContentsMargins(16, 16, 16, 16)
    grid.setSpacing(12)

    _COLS = 3
    for i, c in enumerate(chars):
        grid.addWidget(_bio_card(c), i // _COLS, i % _COLS)
    for col in range(_COLS):
        grid.setColumnStretch(col, 1)
    grid.setRowStretch(grid.rowCount(), 1)

    scroll.setWidget(container)
    return scroll


def _tab_stats(chars: list[model.Character]) -> QTableView:
    headers = ['Character',
               'Max HP', 'Max Stam', 'Max Mag',
               'HP Rec', 'Stam Rec', 'Mag Rec',
               'Spell Dmg', 'Wpn Dmg', 'Crit %',
               'Phys Res', 'Spell Res', 'Crit Res',
               'Mnt Spd', 'Mnt Stam', 'Mnt Cap']
    _HP    = QColor('#f87171')
    _STAM  = QColor('#4ade80')
    _MAG   = QColor('#60a5fa')
    _DMG   = QColor('#fb923c')
    _CRIT  = QColor('#fbbf24')
    _RES   = QColor('#94a3b8')
    _MNT   = QColor('#a78bfa')
    col_colors = {
        1: _HP,  2: _STAM,  3: _MAG,
        4: _HP,  5: _STAM,  6: _MAG,
        7: _DMG, 8: _DMG,   9: _CRIT,
        10: _RES, 11: _RES, 12: _CRIT,
        13: _MNT, 14: _STAM, 15: _MNT,
    }
    rows = []
    for c in chars:
        rows.append([
            _cell(c.name, c.name),
            _cell(f'{c.health_max:,}',       c.health_max),
            _cell(f'{c.stamina_max:,}',      c.stamina_max),
            _cell(f'{c.magicka_max:,}',      c.magicka_max),
            _cell(f'{c.health_recovery:,}',  c.health_recovery),
            _cell(f'{c.stamina_recovery:,}', c.stamina_recovery),
            _cell(f'{c.magicka_recovery:,}', c.magicka_recovery),
            _cell(f'{c.spell_damage:,}',     c.spell_damage),
            _cell(f'{c.weapon_damage:,}',    c.weapon_damage),
            _cell(f'{c.crit_chance:.1f}%',   c.crit_chance),
            _cell(f'{c.resist_physical:,}',  c.resist_physical),
            _cell(f'{c.resist_spell:,}',     c.resist_spell),
            _cell(f'{c.resist_crit:,}',      c.resist_crit),
            _cell(f'{c.mount_speed}/60',     c.mount_speed),
            _cell(f'{c.mount_stamina}/60',   c.mount_stamina),
            _cell(f'{c.mount_capacity}/60',  c.mount_capacity),
        ])
    return _make_view(CharTable(headers, rows, col_colors))


def _rank_color(rank: int) -> QColor | None:
    if rank == 0:   return QColor('#4a4a5a')
    if rank >= 50:  return QColor('#fbbf24')
    if rank >= 40:  return QColor('#d4a017')
    if rank >= 20:  return QColor('#8899aa')
    return QColor('#667788')


# Racial passives — exclude from all skill columns regardless of how the addon categorises them
_RACIAL_LINES: frozenset[str] = frozenset({
    'Argonian', 'Breton', 'Dark Elf', 'High Elf', 'Imperial',
    'Khajiit', 'Nord', 'Orc', 'Redguard', 'Wood Elf',
})

# Native skill lines per class — used to strip subclass lines from the class column
_NATIVE_CLASS_LINES: dict[str, frozenset[str]] = {
    'Dragonknight': frozenset({'Ardent Flame', 'Draconic Power', 'Earthen Heart'}),
    'Nightblade':   frozenset({'Assassination', 'Shadow', 'Siphoning'}),
    'Sorcerer':     frozenset({'Dark Magic', 'Daedric Summoning', 'Storm Calling'}),
    'Templar':      frozenset({'Aedric Spear', "Dawn's Wrath", 'Restoring Light'}),
    'Warden':       frozenset({'Animal Companions', 'Green Balance', "Winter's Embrace"}),
    'Necromancer':  frozenset({'Grave Lord', 'Bone Tyrant', 'Living Death'}),
    'Arcanist':     frozenset({'Herald of the Tome', 'Curative Runeforms', 'Soldier of Apocrypha'}),
}


def _tab_skills(chars: list[model.Character], worn_data: dict | None = None) -> QTableView:
    _NON_CLASS_ATTRS = ['skills_weapon', 'skills_armor', 'skills_ava']

    other_cols: list[str] = []
    seen: set[str] = set()
    for attr in _NON_CLASS_ATTRS:
        for c in chars:
            for s in getattr(c, attr):
                if s.name not in seen and s.name not in _RACIAL_LINES:
                    seen.add(s.name)
                    other_cols.append(s.name)

    headers = ['Character', 'Class 1', 'Class 2', 'Class 3'] + other_cols
    rows = []
    for c in chars:
        native = _NATIVE_CLASS_LINES.get(c.class_name, frozenset())
        class_lines = [s for s in c.skills_class if s.name in native]
        # Fall back to WornGear class_skills when LeoAltholic is missing native lines
        if len(class_lines) < 3 and worn_data:
            wg_lines = (worn_data.get(c.name) or {}).get('__class_skills__') or []
            if wg_lines:
                class_lines = [model.SkillLine(name=l['name'], rank=l.get('rank', 0))
                               for l in wg_lines if isinstance(l, dict) and 'name' in l]
        row = [_cell(c.name, c.name)]
        for i in range(3):
            s = class_lines[i] if i < len(class_lines) else None
            row.append(_cell(s.rank if s else '—', s.rank if s else 0,
                             s.name if s else None,
                             _rank_color(s.rank) if s else None))
        other_lookup = {s.name: s
                        for attr in _NON_CLASS_ATTRS
                        for s in getattr(c, attr)
                        if s.name not in _RACIAL_LINES}
        for n in other_cols:
            s = other_lookup.get(n)
            row.append(_cell(s.rank if s else '—', s.rank if s else 0, None,
                             _rank_color(s.rank) if s else None))
        rows.append(row)
    return _make_view(CharTable(headers, rows))


def _tab_guilds(chars: list[model.Character]) -> QTableView:
    cols: list[str] = []
    seen: set[str] = set()
    for attr in ('skills_guild', 'skills_world'):
        for c in chars:
            for s in getattr(c, attr):
                if s.name not in seen and s.name not in _RACIAL_LINES:
                    seen.add(s.name)
                    cols.append(s.name)
    headers = ['Character'] + cols
    rows = []
    for c in chars:
        lookup = {s.name: s
                  for attr in ('skills_guild', 'skills_world')
                  for s in getattr(c, attr)
                  if s.name not in _RACIAL_LINES}
        row = [_cell(c.name, c.name)]
        for n in cols:
            s = lookup.get(n)
            row.append(_cell(s.rank if s else '—', s.rank if s else 0, None,
                             _rank_color(s.rank) if s else None))
        rows.append(row)
    return _make_view(CharTable(headers, rows))


def _tab_crafting(chars: list[model.Character]) -> QTableView:
    craft_names: list[str] = []
    for c in chars:
        if c.skills_craft:
            craft_names = [s.name for s in c.skills_craft]
            break
    headers = ['Character'] + craft_names
    rows = []
    for c in chars:
        lookup = {s.name: s.rank for s in c.skills_craft}
        row = [_cell(c.name, c.name)]
        for n in craft_names:
            v = lookup.get(n)
            row.append(_cell(v if v is not None else '—', v or 0, None, _rank_color(v or 0)))
        rows.append(row)
    return _make_view(CharTable(headers, rows))


def _tab_dailies(chars: list[model.Character]) -> QTableView:
    headers = ['Character', 'Random Dungeon', 'Writs']
    done_color = QColor('#4dbd74')
    todo_color = QColor('#f87171')

    def _status_cell(done: bool):
        return _cell('Done' if done else 'Not yet', 1 if done else 0, None,
                     done_color if done else todo_color)

    rows = []
    for c in chars:
        rows.append([
            _cell(c.name, c.name),
            _status_cell(c.daily_dungeon_done),
            _status_cell(c.daily_writs_done),
        ])
    return _make_view(CharTable(headers, rows))


def _tab_champion(chars: list[model.Character]) -> QTableView:
    headers = ['Character', 'CP Total', 'Unspent'] + model.CONSTELLATIONS

    _tree_colors = {
        'Craft':   QColor('#4dbd74'),
        'Warfare': QColor('#60a5fa'),
        'Fitness': QColor('#f87171'),
    }
    col_colors = {3 + i: _tree_colors.get(name, QColor('#aaaaaa'))
                  for i, name in enumerate(model.CONSTELLATIONS)}

    rows = []
    for c in chars:
        total = c.cp_spent + c.cp_unspent
        row = [
            _cell(c.name,    c.name),
            _cell(f'{total:,}', total),
            _cell(f'{c.cp_unspent:,}', c.cp_unspent),
        ]
        for con in c.constellations:
            invested = ', '.join(str(v) for v in con.skills if v > 0)
            tip = f'{con.name} slots: [{invested}]' if invested else None
            label = f'{con.spent:,}' + (f'  ({con.unspent} free)' if con.unspent else '')
            row.append(_cell(label, con.spent, tip))
        rows.append(row)
    return _make_view(CharTable(headers, rows, col_colors))


def _tab_inventory(chars: list[model.Character]) -> QTableView:
    headers = ['Character', 'Gems Full', 'Gems Empty',
               'Lockpicks', 'Repair Kits', 'Bag Space']
    rows = []
    for c in chars:
        inv: dict[str, int] = {}
        for i in c.inventory:
            inv[i.name] = inv.get(i.name, 0) + i.count
        rows.append([
            _cell(c.name,                            c.name),
            _cell(c.soul_gems_filled,                c.soul_gems_filled),
            _cell(c.soul_gems_empty,                 c.soul_gems_empty),
            _cell(inv.get('Lockpick', '—'),          inv.get('Lockpick', 0)),
            _cell(inv.get('Equipment Repair Kit', '—'), inv.get('Equipment Repair Kit', 0)),
            _cell(f'{c.bag_used}/{c.bag_size}',      c.bag_used),
        ])
    return _make_view(CharTable(headers, rows))


def _tab_bank(chars: list[model.Character]) -> QWidget:
    # Character.currencies = on-person amounts (summable per character).
    # Character.bank_currencies = shared account/bank pool, same for every
    # character, so it's shown once rather than summed.
    preferred = ['Gold', 'Alliance Points', 'Tel Var Stones', 'Writ Vouchers', 'Undaunted Keys']
    names = {name for c in chars for name in c.currencies}
    per_char_names = [n for n in preferred if n in names] + sorted(names - set(preferred))

    global_names_set = {name for c in chars for name in c.bank_currencies}
    global_names = [n for n in preferred if n in global_names_set] + sorted(global_names_set - set(preferred))

    headers = ['Character'] + per_char_names
    rows = []
    totals = {n: 0 for n in per_char_names}
    for c in chars:
        row = [_cell(c.name, c.name)]
        for n in per_char_names:
            v = c.currencies.get(n, 0)
            row.append(_cell(_n(v), v))
            totals[n] += v
        rows.append(row)
    if per_char_names:
        rows.append([_cell('Total', '~Total')] +
                    [_cell(_n(totals[n]), totals[n]) for n in per_char_names])

    widget = QWidget()
    layout = QVBoxLayout(widget)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.addWidget(_make_view(CharTable(headers, rows)), 1)

    if global_names:
        bar = QFrame()
        bar.setStyleSheet('QFrame { border-top: 1px solid rgba(128,128,128,0.25); }')
        grid = QGridLayout(bar)
        grid.setContentsMargins(12, 10, 12, 10)
        for col, name in enumerate(global_names):
            value = next(c.bank_currencies[name] for c in chars if name in c.bank_currencies)
            lbl = QLabel(name)
            lbl.setStyleSheet('font-size: 11px; color: palette(placeholderText);')
            val = QLabel(_n(value))
            f = val.font(); f.setPointSize(f.pointSize() + 2); f.setBold(True); val.setFont(f)
            grid.addWidget(lbl, 0, col, Qt.AlignCenter)
            grid.addWidget(val, 1, col, Qt.AlignCenter)
        layout.addWidget(bar)

    return widget


# ── armory slot alias ────────────────────────────────────────────────────────
# Armory uses "Shoulders"; build-manager uses "Shoulder"
_SLOT_ALIAS = {"Shoulders": "Shoulder"}


# ── armory-aware build list ───────────────────────────────────────────────────

_ARMORY_ROLE = Qt.ItemDataRole.UserRole + 1  # stores (char_name, build_name) tuple

class ArmoryBuildListPanel(BuildListPanel):
    armory_selected = Signal(str, str)  # (char_name, build_name)

    def __init__(self, parent=None):
        self._armory_char: str = ''
        self._armory_builds: dict[str, dict] = {}
        super().__init__(parent)

    def set_armory_data(self, char_name: str, builds: dict[str, dict]) -> None:
        self._armory_char = char_name
        self._armory_builds = {k: v for k, v in builds.items() if not k.startswith('_')}
        self.refresh()

    def _rebuild_tree(self, filter_text: str = '', select_id=None) -> None:
        super()._rebuild_tree(filter_text, select_id)
        if not self._armory_builds:
            return
        group = QTreeWidgetItem([f'  Current Builds', f'({len(self._armory_builds)})'])
        group.setFlags(Qt.ItemFlag.ItemIsEnabled)
        gf = QFont(); gf.setBold(True); gf.setPointSize(gf.pointSize() - 1)
        group.setFont(0, gf)
        sf = QFont(); sf.setItalic(True); sf.setPointSize(sf.pointSize() - 1)
        group.setFont(1, sf)
        group.setForeground(0, QColor('#88aaff'))
        group.setForeground(1, QColor('#666666'))
        self._tree.insertTopLevelItem(0, group)
        group.setExpanded(True)
        for build_name in sorted(self._armory_builds):
            child = QTreeWidgetItem([f'  {build_name}', ''])
            child.setData(0, _ARMORY_ROLE, (self._armory_char, build_name))
            group.addChild(child)

    def _on_item_changed(self, current, prev) -> None:
        if current is None:
            return
        armory = current.data(0, _ARMORY_ROLE)
        if armory is not None:
            self.armory_selected.emit(*armory)
            return
        super()._on_item_changed(current, prev)


# ── builds tab ───────────────────────────────────────────────────────────────

class BuildsTab(QWidget):
    def __init__(self, chars: list[model.Character],
                 ww_setups: dict[str, list[model.WWSetup]],
                 worn_gear: dict[str, dict],
                 parent=None):
        super().__init__(parent)
        self._chars     = {c.name: c for c in chars}
        self._ww        = ww_setups
        self._worn      = worn_gear
        self._editor_dialog: BuildEditorDialog | None = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)

        # character picker row
        top = QHBoxLayout()
        top.addWidget(QLabel('Character:'))
        self._picker = QComboBox()
        for c in sorted(chars, key=lambda x: x.name):
            self._picker.addItem(c.name, c)
        self._picker.currentIndexChanged.connect(self._on_char_changed)
        top.addWidget(self._picker)
        top.addStretch()
        lay.addLayout(top)

        # live stats strip
        self._stats_strip = QLabel()
        self._stats_strip.setStyleSheet('color: #aaa; font-size: 11px; padding: 2px 4px;')
        lay.addWidget(self._stats_strip)

        line = QFrame(); line.setFrameShape(QFrame.HLine)
        lay.addWidget(line)

        # main splitter: left=builds, right=sheet+WW
        outer = QSplitter(Qt.Horizontal)
        self._build_list = ArmoryBuildListPanel()
        outer.addWidget(self._build_list)

        self._right_stack = QStackedWidget()

        self._build_sheet = BuildSheetWidget()
        self._right_stack.addWidget(self._build_sheet)

        outer.addWidget(self._right_stack)
        outer.setStretchFactor(0, 0)
        outer.setStretchFactor(1, 1)
        lay.addWidget(outer, stretch=1)

        self._build_list.build_selected.connect(self._on_build_selected)
        self._build_list.build_deleted.connect(self._on_build_deleted)
        self._build_list.armory_selected.connect(self._on_armory_selected)
        self._build_list.edit_requested.connect(self._on_edit_requested)
        self._build_sheet.edit_requested.connect(self._on_edit_requested)

        # init with first character
        self._on_char_changed(0)

    def _on_char_changed(self, _idx: int) -> None:
        char: model.Character = self._picker.currentData()
        if char is None:
            return
        self._build_list.set_class_filter(char.class_name)
        self._build_list.set_armory_data(char.name, self._worn.get(char.name, {}))
        self._update_stats_strip(char)
        self._right_stack.setCurrentIndex(0)

    def _armory_to_objects(self, build_name: str, build: dict, char
                           ) -> tuple['Build', list['Skill'], list['GearPiece']]:
        attrs = build.get('attributes', {})
        subclasses = build.get('subclasses') or []
        masteries  = build.get('masteries')  or []
        cp = build.get('cp', {})
        cp_slot_list: list[str] = []
        for discipline in ('Craft', 'Warfare', 'Fitness'):
            val = cp.get(discipline, {})
            stars = list(val.keys())[:4] if isinstance(val, dict) else []
            stars += [''] * (4 - len(stars))
            cp_slot_list.extend(stars)

        build_obj = Build(
            name=build_name,
            eso_class=char.class_name if char else '',
            attribute_health=attrs.get('health', 0),
            attribute_magicka=attrs.get('magicka', 0),
            attribute_stamina=attrs.get('stamina', 0),
            cp_slots=json.dumps(cp_slot_list),
            subclass_1=subclasses[0] if len(subclasses) > 0 else '',
            subclass_2=subclasses[1] if len(subclasses) > 1 else '',
            class_masteries=json.dumps(masteries),
        )

        skills: list[Skill] = []
        raw_skills = build.get('skills', {})
        for bar_idx, bar_name in enumerate(('Front Bar', 'Back Bar')):
            bar = raw_skills.get(bar_name, [])
            for slot_idx, item in enumerate(bar[:6]):
                name = item.get('name', item) if isinstance(item, dict) else item
                if name:
                    skills.append(Skill(build_id=0, bar=bar_idx, slot=slot_idx, name=name))

        gear: list[GearPiece] = []
        raw_gear = build.get('gear', build)  # old format: flat dict
        for slot, info in raw_gear.items():
            if not isinstance(info, dict):
                continue
            slot_mapped = _SLOT_ALIAS.get(slot, slot)
            gear.append(GearPiece(
                build_id=0, slot=slot_mapped,
                set_name=info.get('setName', ''),
                quality=info.get('quality', 'Epic'),
                enchant=info.get('enchant', '').removesuffix(' Enchantment'),
                weight=info.get('weight', ''),
                trait=info.get('trait', ''),
            ))

        return build_obj, skills, gear

    def _on_armory_selected(self, char_name: str, build_name: str) -> None:
        build = self._worn.get(char_name, {}).get(build_name, {})
        char  = self._chars.get(char_name)
        build_obj, skills, gear = self._armory_to_objects(build_name, build, char)

        def _save():
            self._on_export_armory(char_name, build_name)

        self._build_sheet.load_direct(build_obj, skills, gear, save_callback=_save)
        self._right_stack.setCurrentIndex(0)

    def _update_stats_strip(self, char: model.Character) -> None:
        self._stats_strip.setText(
            f'Live stats — '
            f'HP: {char.health_max:,}  '
            f'Stam: {char.stamina_max:,}  '
            f'Mag: {char.magicka_max:,}  '
            f'Spell Dmg: {char.spell_damage:,}  '
            f'Wpn Dmg: {char.weapon_damage:,}  '
            f'Crit: {char.crit_chance:.1f}%  '
            f'Phys Res: {char.resist_physical:,}  '
            f'Spell Res: {char.resist_spell:,}'
        )

    def _on_build_selected(self, build_id: int) -> None:
        self._build_sheet.load_build(build_id)
        self._right_stack.setCurrentIndex(0)

    def _on_build_deleted(self) -> None:
        if self._build_list.current_build_id() is None:
            self._build_sheet.clear()

    def _on_edit_requested(self, build_id: int) -> None:
        if self._editor_dialog is not None:
            if getattr(self._editor_dialog, '_build_id', None) == build_id:
                self._editor_dialog.raise_()
                self._editor_dialog.activateWindow()
                return
            self._editor_dialog.close()  # fires finished → _on_editor_closed → None
        self._editor_dialog = BuildEditorDialog(build_id, None)
        self._editor_dialog._build_id = build_id
        self._editor_dialog.name_changed.connect(self._build_list.update_current_name)
        self._editor_dialog.finished.connect(self._on_editor_closed)
        self._editor_dialog.show()

    def _on_editor_closed(self) -> None:
        self._editor_dialog = None
        bid = self._build_list.current_build_id()
        if bid is not None:
            self._build_list.refresh(select_id=bid)
            self._build_sheet.load_build(bid)

    def _on_export_armory(self, char_name: str, build_name: str) -> None:
        char = self._chars.get(char_name)
        build = self._worn.get(char_name, {}).get(build_name, {})
        # Re-read from disk for freshest weight/trait data
        try:
            fresh = load_worn_gear().get(char_name, {}).get(build_name, {})
            if fresh:
                build = fresh
        except Exception:
            pass

        build_obj, skills_out, gear_out = self._armory_to_objects(build_name, build, char)
        build_obj.name = f'{char_name} — {build_name}'

        build_id = build_db.create_build(build_obj)
        for s in skills_out:
            s.build_id = build_id
        build_db.save_skills(build_id, skills_out)
        for g in gear_out:
            g.build_id = build_id
        build_db.save_gear(build_id, gear_out)

        self._build_list.refresh(select_id=build_id)
        self._on_edit_requested(build_id)


# ── main window ───────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('ESO Build Manager')

        self._settings = QSettings('CubicSerenity', 'ESOBuildManager')
        if geo := self._settings.value('geometry'):
            self.restoreGeometry(geo)
        else:
            self.resize(1300, 820)

        central = QWidget()
        lay = QVBoxLayout(central)
        lay.setContentsMargins(4, 4, 4, 4)
        lay.setSpacing(4)
        self.setCentralWidget(central)

        self._setup_menu()

        self._tabs = QTabWidget()
        lay.addWidget(self._tabs)

        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._reload()

    def _setup_menu(self):
        # File
        self._reload_action = QAction('&Reload Data', self)
        self._reload_action.setShortcut('Ctrl+R')
        self._reload_action.setStatusTip('Sync save files (see Settings…) and reload character data')
        self._reload_action.triggered.connect(self._reload)
        file_menu = self.menuBar().addMenu('&File')
        file_menu.addAction(self._reload_action)
        file_menu.addSeparator()
        file_menu.addAction(QAction('&Settings…', self, triggered=self._open_settings))
        file_menu.addSeparator()
        file_menu.addAction(QAction('E&xit', self, triggered=self.close))

        # Nextcloud
        nc_menu = self.menuBar().addMenu('&Nextcloud')
        sync_action = QAction('Sync Now', self)
        sync_action.setShortcut('Ctrl+Shift+S')
        sync_action.triggered.connect(self._sync_now)
        nc_menu.addAction(sync_action)

        # Help
        help_menu = self.menuBar().addMenu('&Help')
        help_menu.addAction(QAction('About…', self, triggered=self._about))

    def closeEvent(self, event):
        self._settings.setValue('geometry', self.saveGeometry())
        super().closeEvent(event)

    def _sync_now(self):
        from eso_build_manager.sync.nextcloud import NextcloudSyncError, sync_all
        from eso_build_manager.ui.settings_dialog import SettingsDialog

        client = SettingsDialog.get_sync_client()
        if client is None:
            QMessageBox.information(
                self, 'Nextcloud Sync',
                'Configure your Nextcloud server under File → Settings… first.',
            )
            return

        self._status.showMessage('Syncing…')
        QApplication.processEvents()
        try:
            uploaded, downloaded, errors = sync_all(client)
        except NextcloudSyncError as e:
            QMessageBox.warning(self, 'Sync Failed', str(e))
            self._status.showMessage('Sync failed.')
            return

        parts = []
        if uploaded:  parts.append(f'{uploaded} uploaded')
        if downloaded: parts.append(f'{downloaded} downloaded')
        self._status.showMessage('Sync done: ' + (', '.join(parts) if parts else 'nothing to sync') + '.')

        if errors:
            QMessageBox.warning(self, 'Sync Warnings',
                                'Sync completed with errors:\n\n' + '\n'.join(errors))

    def _open_settings(self):
        from eso_build_manager.ui.settings_dialog import SettingsDialog
        SettingsDialog(self).exec()

    def _about(self):
        QMessageBox.about(self, 'About ESO Build Manager',
            '<b>ESO Build Manager</b><br><br>'
            'Character data viewer and build manager for Elder Scrolls Online.<br><br>'
            'Built with Python &amp; PySide6.<br>'
            '&copy; CubicSerenity')

    def _reload(self):
        self._reload_action.setEnabled(False)
        self._status.showMessage('Loading…')
        QApplication.processEvents()
        try:
            _sync_from_zeus()
            chars     = sorted(load_data(), key=lambda c: c.name)
            ww_data   = load_ww_setups()
            worn_data = load_worn_gear()
            cur = self._tabs.currentIndex()
            self._tabs.clear()
            self._tabs.addTab(_tab_bio(chars),                        'Bio')
            self._tabs.addTab(_tab_dailies(chars),                    'Dailies')
            self._tabs.addTab(_tab_stats(chars),                      'Stats')
            self._tabs.addTab(_tab_skills(chars, worn_data),           'Skills')
            self._tabs.addTab(_tab_guilds(chars),                     'Guilds')
            self._tabs.addTab(_tab_crafting(chars),                   'Crafting')
            self._tabs.addTab(_tab_champion(chars),                   'Champion')
            self._tabs.addTab(_tab_inventory(chars),                  'Inventory')
            self._tabs.addTab(_tab_bank(chars),                       'Bank')
            self._tabs.addTab(BuildsTab(chars, ww_data, worn_data),   'Builds')
            self._tabs.setCurrentIndex(max(cur, 0))
            self._status.showMessage(f'{len(chars)} characters loaded.')
        except Exception as e:
            import traceback; traceback.print_exc()
            self._status.showMessage(f'Error: {e}')
        finally:
            self._reload_action.setEnabled(True)


if __name__ == '__main__':
    app = create_app(sys.argv)
    app.setStyle('Fusion')
    win = MainWindow()
    win.showMaximized()
    sys.exit(app.exec())
