import json
from typing import Optional

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag
from PySide6.QtWidgets import (
    QApplication, QCompleter, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QVBoxLayout, QWidget,
)

from eso_build_manager.data_loader import load_cp_skill_ids

_CP_TREES: list[tuple[str, list[str]]] = []


def _load_cp_trees() -> None:
    global _CP_TREES
    if _CP_TREES:
        return
    data = load_cp_skill_ids()
    order = ["Craft", "Warfare", "Fitness"]
    _CP_TREES = [(disc, sorted(data.get(disc, {}).keys())) for disc in order]

_CP_MIME = "application/x-eso-cp-slot"
_cp_drag_source: Optional["_CPSlot"] = None

_TREE_ACCENTS = {"Craft": "#4dbd74", "Warfare": "#60a5fa", "Fitness": "#f87171"}  # matches build_sheet.py


def _accent_group_box_style(accent: str) -> str:
    return f"""
        QGroupBox {{
            border: 1px solid palette(mid);
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 6px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 8px;
            padding: 0 6px;
            color: {accent};
            font-weight: bold;
            font-size: 11px;
        }}
    """


class _CPEdit(QLineEdit):
    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(_CP_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(_CP_MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        global _cp_drag_source
        if event.mimeData().hasFormat(_CP_MIME) and _cp_drag_source is not None:
            tgt: "_CPSlot" = self.parent()  # type: ignore[assignment]
            src = _cp_drag_source
            if src is not tgt:
                src_text = event.mimeData().text()
                tgt_text = self.text()
                self.setText(src_text)
                src.edit.setText(tgt_text)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class _CPHandle(QLabel):
    def __init__(self, label: str, slot: "_CPSlot"):
        super().__init__(label, slot)
        self._slot = slot
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setAcceptDrops(True)
        self._press_pos: Optional[QPoint] = None

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position().toPoint()

    def mouseReleaseEvent(self, event):
        self._press_pos = None

    def mouseMoveEvent(self, event):
        global _cp_drag_source
        if not (event.buttons() & Qt.MouseButton.LeftButton) or self._press_pos is None:
            return
        if (event.position().toPoint() - self._press_pos).manhattanLength() < QApplication.startDragDistance():
            return
        _cp_drag_source = self._slot
        mime = QMimeData()
        mime.setText(self._slot.text())
        mime.setData(_CP_MIME, b"1")
        drag = QDrag(self)
        drag.setMimeData(mime)
        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        drag.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._press_pos = None
        _cp_drag_source = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(_CP_MIME):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(_CP_MIME):
            event.acceptProposedAction()

    def dropEvent(self, event):
        global _cp_drag_source
        if event.mimeData().hasFormat(_CP_MIME) and _cp_drag_source is not None:
            src = _cp_drag_source
            if src is not self._slot:
                src_text = event.mimeData().text()
                tgt_text = self._slot.text()
                self._slot.edit.setText(src_text)
                src.edit.setText(tgt_text)
            event.acceptProposedAction()


class _CPSlot(QWidget):
    def __init__(self, label: str, stars: list[str], parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(0, 0, 0, 0)

        self.handle = _CPHandle(label, self)
        self.edit = _CPEdit()
        self.edit.setPlaceholderText("Star…")
        c = QCompleter(stars, self.edit)
        c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        c.setFilterMode(Qt.MatchFlag.MatchContains)
        c.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
        self.edit.setCompleter(c)
        self.edit.setAcceptDrops(True)

        layout.addWidget(self.handle)
        layout.addWidget(self.edit)

    def text(self) -> str:
        return self.edit.text()

    def setText(self, text: str) -> None:
        self.edit.setText(text)

    def clear(self) -> None:
        self.edit.clear()


class CPWidget(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blocking = False
        self._slots: list[_CPSlot] = []

        _load_cp_trees()

        layout = QHBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(4, 4, 4, 4)

        for tree_name, stars in _CP_TREES:
            group = QGroupBox(tree_name)
            group.setStyleSheet(_accent_group_box_style(_TREE_ACCENTS.get(tree_name, "#556677")))
            group_layout = QHBoxLayout(group)
            group_layout.setSpacing(6)
            for i in range(4):
                slot = _CPSlot("", stars)
                slot.edit.textChanged.connect(self._on_change)
                self._slots.append(slot)
                group_layout.addWidget(slot)
            layout.addWidget(group)

    def _on_change(self) -> None:
        if not self._blocking:
            self.changed.emit()

    def load(self, data: str) -> None:
        self._blocking = True
        names: list[str] = json.loads(data) if data else []
        for i, slot in enumerate(self._slots):
            slot.setText(names[i] if i < len(names) else "")
        self._blocking = False

    def get_data(self) -> str:
        return json.dumps([s.text() for s in self._slots])

    def get_slot_names(self) -> list[str]:
        return [s.text() for s in self._slots]
