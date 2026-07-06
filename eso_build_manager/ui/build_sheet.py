import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QClipboard, QGuiApplication, QPixmap
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QMenu,
    QMessageBox, QPushButton, QScrollArea, QSizePolicy, QTabWidget, QVBoxLayout, QWidget,
)

from eso_build_manager.data_loader import skill_icon_url
from eso_build_manager.icon_cache import fetch_icon

_SHEET_ICON_SIZE = 48

import eso_build_manager.storage.database as db
from eso_build_manager.constants import (
    CLASS_COLORS, ROLE_COLORS,
)


def _rgba(hex_color: str, alpha: float) -> str:
    r, g, b = int(hex_color[1:3], 16), int(hex_color[3:5], 16), int(hex_color[5:7], 16)
    return f"rgba({r},{g},{b},{alpha})"


class _Badge(QLabel):
    def __init__(self, text: str, color: str = "#555566", parent=None):
        super().__init__(f"  {text}  ", parent)
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        fg = "#111111" if (0.299 * r + 0.587 * g + 0.114 * b) > 140 else "#ffffff"
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: {fg};
                border-radius: 10px;
                padding: 3px 0px;
                font-weight: 600;
                font-size: 11px;
            }}
        """)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)


class _SkillCard(QFrame):
    def __init__(self, slot_label: str, skill_name: str = "", accent: str = "#4a9eff",
                 show_icon: bool = False, parent=None):
        super().__init__(parent)
        filled = bool(skill_name.strip())

        if filled:
            self.setStyleSheet(f"""
                QFrame {{
                    border: 2px solid {accent};
                    border-radius: 6px;
                    background-color: {_rgba(accent, 0.07)};
                }}
                QLabel {{ border: none; background: transparent; }}
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid palette(mid);
                    border-radius: 6px;
                    background-color: transparent;
                }
                QLabel { border: none; background: transparent; }
            """)

        self.setMinimumWidth(70)
        self.setFixedHeight(100 if show_icon else 52)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(4, 6, 4, 6)
        vbox.setSpacing(4)

        self._icon_lbl: QLabel | None = None
        if show_icon:
            self._icon_lbl = QLabel()
            self._icon_lbl.setFixedSize(_SHEET_ICON_SIZE, _SHEET_ICON_SIZE)
            self._icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            # No box shown until an icon actually loads
            self._icon_lbl.setStyleSheet("background: transparent;")
            vbox.addWidget(self._icon_lbl, 0, Qt.AlignmentFlag.AlignHCenter)

        lbl_slot = QLabel(slot_label)
        lbl_slot.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_slot.setStyleSheet(
            f"color: {accent}; font-size: 9px; font-weight: bold; letter-spacing: 1px;"
            if filled else
            "color: palette(placeholderText); font-size: 9px; letter-spacing: 1px;"
        )

        lbl_name = QLabel(skill_name.strip() if filled else "—")
        lbl_name.setWordWrap(True)
        lbl_name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl_name.setStyleSheet(
            "font-size: 11px; font-weight: 500;"
            if filled else
            "font-size: 11px; color: palette(placeholderText);"
        )

        vbox.addWidget(lbl_slot)
        vbox.addWidget(lbl_name, 1)

        if show_icon and filled:
            url = skill_icon_url(skill_name.strip()) or skill_icon_url("Ulfsild's Contingency")
            if url:
                fetch_icon(url, self._set_icon)

    def _set_icon(self, px: QPixmap) -> None:
        if self._icon_lbl and not px.isNull():
            self._icon_lbl.setStyleSheet(
                "border: 1px solid palette(mid); border-radius: 3px; background: palette(base);"
            )
            self._icon_lbl.setPixmap(px.scaled(
                _SHEET_ICON_SIZE, _SHEET_ICON_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))


class _GearCard(QFrame):
    def __init__(self, slot: str, piece, parent=None):
        super().__init__(parent)
        filled = piece and piece.set_name.strip()
        two_hand = piece and piece.weight == "N/A"

        if filled:
            self.setStyleSheet("""
                QFrame {
                    border: 1px solid palette(mid);
                    border-radius: 6px;
                    background-color: rgba(255,255,255,0.03);
                }
                QLabel { border: none; background: transparent; }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    border: 1px dashed palette(mid);
                    border-radius: 6px;
                    background-color: transparent;
                }
                QLabel { border: none; background: transparent; }
            """)

        self.setMinimumWidth(110)
        self.setMinimumHeight(72)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(8, 6, 8, 6)
        vbox.setSpacing(2)

        slot_lbl = QLabel(slot.upper())
        slot_lbl.setStyleSheet(
            "color: palette(placeholderText); font-size: 9px; font-weight: bold; letter-spacing: 1px;"
        )
        vbox.addWidget(slot_lbl)

        if two_hand:
            na = QLabel("N/A  (two-handed)")
            na.setStyleSheet("color: palette(placeholderText); font-size: 10px; font-style: italic;")
            vbox.addWidget(na)
        elif filled:
            # Epic is the common case (most endgame gear) — only flag qualities
            # worth calling out, so the sheet isn't a wall of one color.
            _QUALITY_COLOR = {
                "Legendary": "#e5a623", "Mythic": "#d4a017",
                "Superior": "#0070dd", "Fine": "#1eff00", "Normal": "#c0c0c0",
            }
            q_color = _QUALITY_COLOR.get(piece.quality, "")
            set_lbl = QLabel(piece.set_name)
            set_lbl.setWordWrap(True)
            set_lbl.setStyleSheet(
                f"font-size: 12px; font-weight: 600; color: {q_color};" if q_color
                else "font-size: 12px; font-weight: 600;"
            )
            vbox.addWidget(set_lbl)

            details = "  ·  ".join(p for p in [piece.weight, piece.trait] if p)
            if details:
                det = QLabel(details)
                det.setStyleSheet("color: palette(placeholderText); font-size: 10px;")
                vbox.addWidget(det)

            enchant = piece.enchant.removeprefix("Maximum ").strip()
            if enchant:
                enc = QLabel(enchant)
                enc.setStyleSheet("color: palette(placeholderText); font-size: 10px; font-style: italic;")
                vbox.addWidget(enc)
        else:
            empty = QLabel("—")
            empty.setStyleSheet("color: palette(placeholderText); font-size: 12px;")
            vbox.addWidget(empty)

        vbox.addStretch()


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setStyleSheet("""
        QLabel {
            color: palette(windowText);
            font-size: 10px;
            font-weight: bold;
            letter-spacing: 3px;
            padding-bottom: 4px;
            border-bottom: 2px solid palette(highlight);
        }
    """)
    return lbl


class BuildSheetWidget(QWidget):
    edit_requested = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_id: int | None = None
        self._save_callback = None

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._inner = QWidget()
        self._vbox = QVBoxLayout(self._inner)
        self._vbox.setContentsMargins(28, 24, 28, 24)
        self._vbox.setSpacing(28)
        scroll.setWidget(self._inner)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

        self._placeholder = QLabel("Select a build from the sidebar.")
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setStyleSheet("color: palette(placeholderText); font-size: 15px;")
        self._vbox.addStretch()
        self._vbox.addWidget(self._placeholder)
        self._vbox.addStretch()

    # ── Public API ────────────────────────────────────────────────────────

    def load_build(self, build_id: int) -> None:
        self._build_id = build_id
        self._save_callback = None
        build = db.get_build(build_id)
        if not build:
            return
        skills = db.get_skills(build_id)
        gear = db.get_gear(build_id)
        self._rebuild(build, skills, gear)

    def load_direct(self, build, skills, gear, *, save_callback=None) -> None:
        """Display a transient build (e.g. armory) without a DB id."""
        self._build_id = None
        self._save_callback = save_callback
        self._rebuild(build, skills, gear, save_callback=save_callback)

    def clear(self) -> None:
        self._build_id = None
        self._save_callback = None
        self._clear_inner()
        self._vbox.addStretch()
        self._placeholder.show()
        self._vbox.addWidget(self._placeholder)
        self._vbox.addStretch()

    # ── Export actions ────────────────────────────────────────────────────

    def _export_json(self) -> None:
        if self._build_id is None:
            return
        from eso_build_manager.exporter import export_build_dict
        import json
        build = __import__("eso_build_manager.storage.database", fromlist=["get_build"]).get_build(self._build_id)
        default_name = (build.name if build else "build").replace(" ", "_") + ".json"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Build", default_name, "JSON files (*.json)"
        )
        if not path:
            return
        data = export_build_dict(self._build_id)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        QMessageBox.information(self, "Export", f"Build saved to:\n{path}")

    def _export_text(self) -> None:
        if self._build_id is None:
            return
        from eso_build_manager.exporter import export_build_text
        text = export_build_text(self._build_id)
        QGuiApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copied", "Build summary copied to clipboard.")

    # ── Internal helpers ──────────────────────────────────────────────────

    def _clear_inner(self) -> None:
        while self._vbox.count():
            item = self._vbox.takeAt(0)
            if w := item.widget():
                if w is not self._placeholder:
                    w.deleteLater()

    def _rebuild(self, build, skills, gear, *, save_callback=None) -> None:
        self._placeholder.hide()
        self._clear_inner()

        self._vbox.addWidget(self._build_header(build, save_callback=save_callback))

        gear_pages = json.loads(build.gear_pages) if build.gear_pages else ["Main"]
        self._vbox.addWidget(self._loadout_section(skills, gear, gear_pages))

        cp_slots = json.loads(build.cp_slots) if build.cp_slots else []
        if any(s.strip() for s in cp_slots):
            self._vbox.addWidget(self._cp_section(cp_slots))

        self._vbox.addWidget(self._stats_section(build))

        if build.notes.strip():
            self._vbox.addWidget(self._notes_section(build.notes))

        self._vbox.addStretch()

    # ── Section builders ──────────────────────────────────────────────────

    def _build_header(self, build, *, save_callback=None) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(12)

        # Name row
        top = QHBoxLayout()
        name_lbl = QLabel(build.name)
        f = name_lbl.font()
        f.setPointSize(f.pointSize() + 10)
        f.setBold(True)
        name_lbl.setFont(f)
        top.addWidget(name_lbl, 1)

        if save_callback:
            save_btn = QPushButton("⬆  Save as Build")
            save_btn.setFixedWidth(130)
            save_btn.setFixedHeight(32)
            save_btn.clicked.connect(save_callback)
            top.addWidget(save_btn, 0, Qt.AlignmentFlag.AlignVCenter)
        else:
            edit_btn = QPushButton("✎  Edit")
            edit_btn.setFixedWidth(95)
            edit_btn.setFixedHeight(32)
            edit_btn.clicked.connect(lambda: self.edit_requested.emit(self._build_id))
            top.addWidget(edit_btn, 0, Qt.AlignmentFlag.AlignVCenter)

            export_btn = QPushButton("⬇  Export")
            export_btn.setFixedWidth(95)
            export_btn.setFixedHeight(32)
            export_menu = QMenu(export_btn)
            export_menu.addAction("Save JSON file…", self._export_json)
            export_menu.addAction("Copy build summary", self._export_text)
            export_btn.setMenu(export_menu)
            top.addWidget(export_btn, 0, Qt.AlignmentFlag.AlignVCenter)

        vbox.addLayout(top)

        # Badge row
        badge_row = QHBoxLayout()
        badge_row.setSpacing(8)
        if build.eso_class:
            badge_row.addWidget(_Badge(build.eso_class, CLASS_COLORS.get(build.eso_class, "#556677")))
        if build.subclass_1:
            badge_row.addWidget(_Badge(build.subclass_1, "#445566"))
        if build.subclass_2:
            badge_row.addWidget(_Badge(build.subclass_2, "#445566"))
        if build.role:
            badge_row.addWidget(_Badge(build.role, ROLE_COLORS.get(build.role, "#556677")))
        if build.content:
            badge_row.addWidget(_Badge(build.content, "#446655"))
        if build.game_patch:
            badge_row.addWidget(_Badge(build.game_patch, "#334455"))
        has_attrs = any([build.attribute_health, build.attribute_magicka, build.attribute_stamina])
        if has_attrs:
            badge_row.addStretch()
            for label, val, color in [
                ("HP", build.attribute_health, "#f87171"),
                ("Mag", build.attribute_magicka, "#60a5fa"),
                ("Stam", build.attribute_stamina, "#4ade80"),
            ]:
                sep = QLabel("·"); sep.setStyleSheet("color:palette(placeholderText);margin:0 2px;")
                v = QLabel(f"{label}: {val}")
                v.setStyleSheet(f"color:{color};font-size:11px;font-weight:bold;")
                badge_row.addWidget(sep); badge_row.addWidget(v)
        else:
            badge_row.addStretch()
        vbox.addLayout(badge_row)

        if build.source.strip():
            src = build.source.strip()
            src_lbl = QLabel()
            src_lbl.setOpenExternalLinks(True)
            if src.startswith("http"):
                src_lbl.setText(f'<a href="{src}" style="color:#60a5fa;">{src}</a>')
            else:
                src_lbl.setText(f'<span style="color:palette(windowText);">Source: {src}</span>')
            src_lbl.setStyleSheet("font-size: 12px;")
            vbox.addWidget(src_lbl)

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("QFrame { color: palette(windowText); margin: 0; }")
        vbox.addWidget(line)

        return w

    def _skills_page_widget(self, skills: list) -> QWidget:
        by_slot = {(s.bar, s.slot): s.name for s in skills}

        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(8)
        vbox.addWidget(_section_label("Skills"))

        bars = [
            (0, "Front Bar", "#4a9eff"),
            (1, "Back Bar",  "#f97316"),
        ]
        for bar_idx, bar_label, accent in bars:
            row = QHBoxLayout()
            row.setSpacing(6)

            bar_lbl = QLabel(bar_label)
            bar_lbl.setFixedWidth(68)
            bar_lbl.setStyleSheet(f"color:{accent};font-weight:bold;font-size:11px;")
            row.addWidget(bar_lbl)

            for slot in range(5):
                name = by_slot.get((bar_idx, slot), "")
                row.addWidget(_SkillCard(str(slot + 1), name, accent, show_icon=True))

            ult = by_slot.get((bar_idx, 5), "")
            row.addWidget(_SkillCard("ULT", ult, "#fbbf24", show_icon=True))

            vbox.addLayout(row)

        return w

    def _cp_section(self, slots: list[str]) -> QWidget:
        while len(slots) < 12:
            slots.append("")

        trees = [
            ("Craft",    "#4dbd74", 0),
            ("Warfare",  "#60a5fa", 4),
            ("Fitness",  "#f87171", 8),
        ]

        def _rgba(hex_color: str, alpha: float) -> str:
            r, g, b = int(hex_color[1:3],16), int(hex_color[3:5],16), int(hex_color[5:7],16)
            return f"rgba({r},{g},{b},{alpha})"

        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(8)
        vbox.addWidget(_section_label("Champion Points"))

        for tree_name, color, offset in trees:
            row = QHBoxLayout(); row.setSpacing(6)
            lbl = QLabel(tree_name)
            lbl.setFixedWidth(68)
            lbl.setStyleSheet(f"color:{color};font-weight:bold;font-size:11px;")
            row.addWidget(lbl)
            for i in range(4):
                name = slots[offset + i]
                card = QFrame()
                card.setStyleSheet(
                    f"QFrame{{border:1px solid {color};border-radius:6px;"
                    f"background:{_rgba(color,0.05)};}} "
                    "QLabel{border:none;background:transparent;}"
                )
                card.setFixedHeight(52)
                card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
                cl = QVBoxLayout(card); cl.setContentsMargins(4,4,4,4); cl.setSpacing(1)
                slot_l = QLabel(str(i + 1))
                slot_l.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                slot_l.setStyleSheet(
                    f"color:{color};font-size:8px;font-weight:bold;" if name else
                    "color:palette(placeholderText);font-size:8px;"
                )
                name_l = QLabel(name or "—")
                name_l.setWordWrap(True)
                name_l.setAlignment(Qt.AlignmentFlag.AlignHCenter)
                name_l.setStyleSheet(
                    "font-size:10px;font-weight:500;" if name else
                    "font-size:10px;color:palette(placeholderText);"
                )
                cl.addWidget(slot_l); cl.addWidget(name_l, 1)
                row.addWidget(card)
            row.addStretch()
            rw = QWidget(); rw.setLayout(row)
            vbox.addWidget(rw)

        return w

    def _gear_page_widget(self, gear: list) -> QWidget:
        by_slot = {g.slot: g for g in gear}

        _ARMOR = ["Head", "Shoulder", "Chest", "Hands", "Waist", "Legs", "Feet"]
        _JEWELRY = ["Neck", "Ring 1", "Ring 2"]
        _WEAPONS = ["Main Hand", "Off Hand", "Backup Main", "Backup Off"]

        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(12)
        vbox.addWidget(_section_label("Gear"))

        def _sub_lbl(text: str) -> QLabel:
            lbl = QLabel(text)
            lbl.setStyleSheet(
                "color: palette(placeholderText); font-size: 9px; font-weight: bold; letter-spacing: 2px;"
            )
            return lbl

        def _card_grid(slots: list, columns: int) -> QWidget:
            container = QWidget()
            grid = QGridLayout(container)
            grid.setSpacing(6)
            grid.setContentsMargins(0, 0, 0, 0)
            for i, slot in enumerate(slots):
                card = _GearCard(slot, by_slot.get(slot))
                grid.addWidget(card, i // columns, i % columns)
            for col in range(columns):
                grid.setColumnStretch(col, 1)
            return container

        vbox.addWidget(_sub_lbl("ARMOR"))
        vbox.addWidget(_card_grid(_ARMOR, 7))
        vbox.addWidget(_sub_lbl("JEWELRY"))
        vbox.addWidget(_card_grid(_JEWELRY, 3))
        vbox.addWidget(_sub_lbl("WEAPONS"))
        vbox.addWidget(_card_grid(_WEAPONS, 4))

        return w

    def _loadout_page_widget(self, skills: list, gear: list) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(20)
        vbox.addWidget(self._skills_page_widget(skills))
        vbox.addWidget(self._gear_page_widget(gear))
        return w

    def _loadout_section(self, skills: list, gear: list, page_names: list | None = None) -> QWidget:
        page_names = page_names or ["Main"]

        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(12)

        if len(page_names) <= 1:
            vbox.addWidget(self._loadout_page_widget(skills, gear))
            return w

        skills_by_page: dict = {}
        for s in skills:
            skills_by_page.setdefault(s.page, []).append(s)
        gear_by_page: dict = {}
        for g in gear:
            gear_by_page.setdefault(g.page, []).append(g)

        tabs = QTabWidget()
        for i, name in enumerate(page_names):
            tabs.addTab(
                self._loadout_page_widget(skills_by_page.get(i, []), gear_by_page.get(i, [])),
                name,
            )
        vbox.addWidget(tabs)

        return w

    def _stats_section(self, build) -> QWidget:
        food = (build.food_buff or "").strip()
        mundus = (build.mundus_stone or "").strip()
        if not food and not mundus:
            w = QWidget(); w.setFixedHeight(0); return w

        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(10)
        vbox.addWidget(_section_label("Food & Mundus"))

        row = QHBoxLayout(); row.setSpacing(32)
        for label_text, value in [("Food / Drink", food), ("Mundus Stone", mundus)]:
            if not value:
                continue
            cell = QWidget()
            cell_l = QVBoxLayout(cell)
            cell_l.setContentsMargins(0, 0, 0, 0); cell_l.setSpacing(2)
            lbl = QLabel(label_text)
            lbl.setStyleSheet("font-size:10px;font-weight:bold;letter-spacing:1px;")
            val = QLabel(value)
            val.setStyleSheet("font-size:13px;font-weight:500;")
            cell_l.addWidget(lbl); cell_l.addWidget(val)
            row.addWidget(cell)
        row.addStretch()
        vbox.addLayout(row)
        return w

    def _notes_section(self, notes: str) -> QWidget:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(10)
        vbox.addWidget(_section_label("Notes"))
        lbl = QLabel(notes.strip())
        lbl.setWordWrap(True)
        lbl.setStyleSheet("font-size: 13px; line-height: 160%;")
        vbox.addWidget(lbl)
        return w
