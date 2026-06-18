import json
from typing import Optional

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QCheckBox, QLabel, QVBoxLayout, QWidget

from eso_build_manager.data_loader import load_class_masteries

_MASTERIES: Optional[dict[str, list[str]]] = None


def _get_masteries() -> dict[str, list[str]]:
    global _MASTERIES
    if _MASTERIES is None:
        _MASTERIES = load_class_masteries()
    return _MASTERIES


class ClassMasteryWidget(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes: list[QCheckBox] = []
        self._current_class = ""

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        self._info = QLabel()
        self._info.setWordWrap(True)
        layout.addWidget(self._info)

        self._cb_layout = QVBoxLayout()
        self._cb_layout.setSpacing(6)
        layout.addLayout(self._cb_layout)
        layout.addStretch()

        self._rebuild("", [])

    def set_class(self, class_name: str) -> None:
        if class_name == self._current_class:
            return
        selected = self.get_selected()
        self._current_class = class_name
        self._rebuild(class_name, selected)

    def load(self, class_name: str, data: str) -> None:
        selected = json.loads(data) if data else []
        self._current_class = class_name
        self._rebuild(class_name, selected)

    def get_selected(self) -> list[str]:
        return [cb.text() for cb in self._checkboxes if cb.isChecked()]

    def get_data(self) -> str:
        return json.dumps(self.get_selected())

    def _rebuild(self, class_name: str, selected: list[str]) -> None:
        for cb in self._checkboxes:
            self._cb_layout.removeWidget(cb)
            cb.deleteLater()
        self._checkboxes.clear()

        passives = _get_masteries().get(class_name, [])
        if not passives:
            self._info.setText(
                "No class selected, or no Class Mastery passives found.\n\n"
                "Class Mastery passives (Update 50+) require a pure class — "
                "no subclasses selected."
            )
            return

        self._info.setText(
            f"{class_name} — Class Mastery Passives\n"
            "Only available when playing pure class (Subclass unchecked)."
        )
        for name in sorted(passives):
            cb = QCheckBox(name)
            cb.setChecked(name in selected)
            cb.toggled.connect(self.changed)
            self._checkboxes.append(cb)
            self._cb_layout.addWidget(cb)
