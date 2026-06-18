import json

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDoubleSpinBox, QFormLayout, QGridLayout, QGroupBox,
    QLabel, QProgressBar, QSpinBox, QVBoxLayout, QWidget,
)

# (key, display label, cap value, cap label, is_percent)
_CAPPED_STATS = [
    ("phys_resist",  "Physical Resistance", 33_000, "Armor Cap",   False),
    ("spell_resist", "Spell Resistance",    33_000, "Armor Cap",   False),
    ("phys_pen",     "Physical Penetration",18_200, "Trial Boss",  False),
    ("spell_pen",    "Spell Penetration",   18_200, "Trial Boss",  False),
    ("weapon_crit",  "Weapon Critical",        100, "Crit Cap",    True),
    ("spell_crit",   "Spell Critical",          100, "Crit Cap",    True),
    ("crit_resist",  "Critical Resistance",  33_000, "PvP Cap",    False),
]

_PLAIN_STATS = [
    ("max_health",    "Max Health"),
    ("max_magicka",   "Max Magicka"),
    ("max_stamina",   "Max Stamina"),
    ("weapon_damage", "Weapon Damage"),
    ("spell_damage",  "Spell Damage"),
]

_DEFAULT: dict[str, float] = {k: 0 for k, *_ in _CAPPED_STATS + _PLAIN_STATS}


def _cap_color(ratio: float) -> str:
    if ratio >= 1.0:
        return "#4dbd74"   # green
    if ratio >= 0.8:
        return "#eab308"   # yellow
    return "#f87171"       # red


def _cap_icon(ratio: float) -> str:
    if ratio >= 1.0:
        return "✓"
    if ratio >= 0.8:
        return "⚠"
    return "✗"


class StatsInputWidget(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blocking = False
        self._inputs: dict[str, QSpinBox | QDoubleSpinBox] = {}
        self._cap_bars: dict[str, QProgressBar] = {}
        self._cap_labels: dict[str, QLabel] = {}

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(12)

        # ── Resources & Damage (no caps) ──────────────────────────────────
        plain_box = QGroupBox("Resources & Damage")
        plain_form = QFormLayout(plain_box)
        plain_form.setSpacing(6)
        for key, label in _PLAIN_STATS:
            spin = QSpinBox()
            spin.setRange(0, 999_999)
            spin.setSingleStep(100)
            spin.setGroupSeparatorShown(True)
            spin.valueChanged.connect(self._on_change)
            self._inputs[key] = spin
            plain_form.addRow(label + ":", spin)
        outer.addWidget(plain_box)

        # ── Capped Stats ──────────────────────────────────────────────────
        cap_box = QGroupBox("Capped Stats")
        cap_grid = QGridLayout(cap_box)
        cap_grid.setSpacing(6)
        cap_grid.setColumnMinimumWidth(0, 160)
        cap_grid.setColumnMinimumWidth(1, 90)
        cap_grid.setColumnStretch(2, 1)
        cap_grid.setColumnMinimumWidth(3, 140)

        for row, (key, label, cap, cap_lbl, is_pct) in enumerate(_CAPPED_STATS):
            name_lbl = QLabel(label + ":")
            cap_grid.addWidget(name_lbl, row, 0)

            if is_pct:
                spin = QDoubleSpinBox()
                spin.setRange(0.0, 100.0)
                spin.setDecimals(1)
                spin.setSuffix(" %")
                spin.setSingleStep(0.5)
            else:
                spin = QSpinBox()
                spin.setRange(0, 999_999)
                spin.setSingleStep(500)
                spin.setGroupSeparatorShown(True)
            spin.valueChanged.connect(self._on_change)
            self._inputs[key] = spin
            cap_grid.addWidget(spin, row, 1)

            bar = QProgressBar()
            bar.setRange(0, 100)
            bar.setValue(0)
            bar.setTextVisible(False)
            bar.setFixedHeight(10)
            bar.setStyleSheet("""
                QProgressBar { border: 1px solid #3a3a4a; border-radius: 4px; background: #1e1e2e; }
                QProgressBar::chunk { border-radius: 3px; background: #4dbd74; }
            """)
            self._cap_bars[key] = bar
            cap_grid.addWidget(bar, row, 2)

            status_lbl = QLabel(f"0 / {cap:,}  —  {cap_lbl}")
            status_lbl.setStyleSheet("font-size: 11px;")
            self._cap_labels[key] = status_lbl
            cap_grid.addWidget(status_lbl, row, 3)

        outer.addWidget(cap_box)

    # ── Public API ────────────────────────────────────────────────────────

    def load(self, data: str) -> None:
        self._blocking = True
        stats = json.loads(data) if data else {}
        for key, widget in self._inputs.items():
            val = stats.get(key, 0)
            if isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(val))
            else:
                widget.setValue(int(val))
        self._blocking = False
        self._update_all_caps()

    def get_data(self) -> str:
        return json.dumps({
            k: w.value() for k, w in self._inputs.items()
        })

    # ── Internals ─────────────────────────────────────────────────────────

    def _on_change(self) -> None:
        if not self._blocking:
            self._update_all_caps()
            self.changed.emit()

    def _update_all_caps(self) -> None:
        for key, label, cap, cap_lbl, is_pct in _CAPPED_STATS:
            widget = self._inputs[key]
            value = widget.value()
            ratio = min(value / cap, 1.0) if cap > 0 else 0.0
            pct = int(ratio * 100)

            bar = self._cap_bars[key]
            bar.setValue(pct)
            color = _cap_color(ratio)
            bar.setStyleSheet(f"""
                QProgressBar {{
                    border: 1px solid #3a3a4a;
                    border-radius: 4px;
                    background: #1e1e2e;
                }}
                QProgressBar::chunk {{
                    border-radius: 3px;
                    background: {color};
                }}
            """)

            lbl = self._cap_labels[key]
            icon = _cap_icon(ratio)
            if ratio >= 1.0:
                if is_pct:
                    text = f"{icon} At cap  ({cap_lbl}: {cap}%)"
                else:
                    text = f"{icon} At cap  ({cap_lbl}: {cap:,})"
            else:
                gap = cap - value
                if is_pct:
                    text = f"{icon} {gap:.1f}% to {cap_lbl}  ({cap}%)"
                else:
                    text = f"{icon} {gap:,.0f} to {cap_lbl}  ({cap:,})"
            lbl.setText(text)
            lbl.setStyleSheet(f"font-size: 11px; color: {color};")
