from typing import Optional

from PySide6.QtCore import QMimeData, QPoint, Qt, Signal
from PySide6.QtGui import QDrag, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCompleter, QFrame, QGroupBox, QHBoxLayout,
    QLabel, QLineEdit, QVBoxLayout, QWidget,
)

from eso_build_manager.data_loader import load_skill_names, skill_icon_url
from eso_build_manager.icon_cache import fetch_icon
from eso_build_manager.models.skill import Skill

_ICON_SIZE = 80

_SKILL_NAMES: list[str] = []
_SLOT_MIME = "application/x-eso-skill-slot"
_drag_source: Optional["_SkillSlot"] = None


def _get_skill_names() -> list[str]:
    global _SKILL_NAMES
    if not _SKILL_NAMES:
        _SKILL_NAMES = load_skill_names()
    return _SKILL_NAMES


def _make_completer(parent) -> QCompleter:
    c = QCompleter(_get_skill_names(), parent)
    c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
    c.setFilterMode(Qt.MatchFlag.MatchContains)
    c.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
    return c


_BAR_ACCENTS = ["#4a9eff", "#f97316"]  # Front Bar, Back Bar — matches build_sheet.py


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


class _SkillEdit(QLineEdit):
    """QLineEdit that accepts slot-drag drops from other skill slots."""

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(_SLOT_MIME):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(_SLOT_MIME):
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event):
        global _drag_source
        if event.mimeData().hasFormat(_SLOT_MIME) and _drag_source is not None:
            tgt_slot: "_SkillSlot" = self.parent()  # type: ignore[assignment]
            src_slot = _drag_source
            if src_slot is not tgt_slot:
                src_text = event.mimeData().text()
                tgt_text = self.text()
                self.setText(src_text)
                src_slot.edit.setText(tgt_text)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)


class _IconHandle(QLabel):
    """Icon display that doubles as the drag handle for its parent slot."""

    def __init__(self, slot_label: str, slot: "_SkillSlot"):
        super().__init__(slot)
        self._slot = slot
        self._slot_label = slot_label
        self._has_icon = False
        self.setFixedSize(_ICON_SIZE, _ICON_SIZE)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self.setAcceptDrops(True)
        self._press_pos: Optional[QPoint] = None
        self._show_placeholder()

    def _show_placeholder(self) -> None:
        self._has_icon = False
        self.clear()
        self.setText(self._slot_label)
        self.setStyleSheet(
            "color: palette(placeholderText); font-size: 10px; font-weight: bold;"
            " border: 1px dashed palette(mid); border-radius: 4px;"
        )

    def set_icon(self, px: QPixmap) -> None:
        if px.isNull():
            self._show_placeholder()
        else:
            self._has_icon = True
            self.setText("")
            self.setStyleSheet(
                "border: 1px solid palette(mid); border-radius: 4px; background: palette(base);"
            )
            self.setPixmap(px.scaled(
                _ICON_SIZE, _ICON_SIZE,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            ))

    # ── drag source ───────────────────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._press_pos = event.position().toPoint()

    def mouseReleaseEvent(self, event):
        self._press_pos = None

    def mouseMoveEvent(self, event):
        global _drag_source
        if not (event.buttons() & Qt.MouseButton.LeftButton) or self._press_pos is None:
            return
        if (event.position().toPoint() - self._press_pos).manhattanLength() < QApplication.startDragDistance():
            return

        _drag_source = self._slot
        mime = QMimeData()
        mime.setText(self._slot.text())
        mime.setData(_SLOT_MIME, b"1")

        drag = QDrag(self)
        drag.setMimeData(mime)
        if self._has_icon and not self.pixmap().isNull():
            drag.setPixmap(self.pixmap())
            drag.setHotSpot(QPoint(_ICON_SIZE // 2, _ICON_SIZE // 2))

        self.setCursor(Qt.CursorShape.ClosedHandCursor)
        drag.exec(Qt.DropAction.MoveAction)
        self.setCursor(Qt.CursorShape.OpenHandCursor)
        self._press_pos = None
        _drag_source = None

    # ── drop target ───────────────────────────────────────────────────────

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(_SLOT_MIME):
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(_SLOT_MIME):
            event.acceptProposedAction()

    def dropEvent(self, event):
        global _drag_source
        if event.mimeData().hasFormat(_SLOT_MIME) and _drag_source is not None:
            src_slot = _drag_source
            if src_slot is not self._slot:
                src_text = event.mimeData().text()
                tgt_text = self._slot.text()
                self._slot.edit.setText(src_text)
                src_slot.edit.setText(tgt_text)
            event.acceptProposedAction()


class _SkillSlot(QWidget):
    """Icon handle (drag source/target) + autocomplete line edit for one slot."""

    def __init__(self, label_text: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(0, 0, 0, 0)

        self.icon_handle = _IconHandle(label_text, self)
        layout.addWidget(self.icon_handle, 0, Qt.AlignmentFlag.AlignHCenter)

        self.edit = _SkillEdit()
        self.edit.setPlaceholderText(label_text)
        self.edit.setCompleter(_make_completer(self.edit))
        self.edit.setAcceptDrops(True)
        self.edit.textChanged.connect(self._update_icon)

        layout.addWidget(self.edit)

    def _update_icon(self, name: str) -> None:
        name = name.strip()
        if not name:
            self.icon_handle.set_icon(QPixmap())
            return
        url = skill_icon_url(name)
        if url is None:
            self.icon_handle.set_icon(QPixmap())
            return
        fetch_icon(url, self.icon_handle.set_icon)

    def text(self) -> str:
        return self.edit.text()

    def setText(self, text: str) -> None:
        self.edit.setText(text)

    def clear(self) -> None:
        self.edit.clear()


class SkillBarWidget(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blocking = False
        self._slots: dict[tuple[int, int], _SkillSlot] = {}

        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(8, 8, 8, 8)

        for bar_idx, bar_name in enumerate(["Front Bar", "Back Bar"]):
            group = QGroupBox(bar_name)
            group.setStyleSheet(_accent_group_box_style(_BAR_ACCENTS[bar_idx]))
            bar_layout = QHBoxLayout(group)
            bar_layout.setSpacing(6)

            for slot_idx in range(6):
                if slot_idx == 5:
                    sep = QFrame()
                    sep.setFrameShape(QFrame.Shape.VLine)
                    sep.setFrameShadow(QFrame.Shadow.Sunken)
                    bar_layout.addWidget(sep)

                label_text = f"Slot {slot_idx + 1}" if slot_idx < 5 else "Ultimate"
                slot = _SkillSlot(label_text)
                slot.edit.textChanged.connect(self._on_change)
                self._slots[(bar_idx, slot_idx)] = slot
                bar_layout.addWidget(slot)

            layout.addWidget(group)

        layout.addStretch()

    def _on_change(self):
        if not self._blocking:
            self.changed.emit()

    def load(self, skills: list[Skill]) -> None:
        self._blocking = True
        for slot in self._slots.values():
            slot.clear()
        for skill in skills:
            key = (skill.bar, skill.slot)
            if key in self._slots:
                self._slots[key].setText(skill.name)
        self._blocking = False

    def get_skills(self, build_id: int) -> list[Skill]:
        return [
            Skill(build_id=build_id, bar=bar, slot=slot_idx, name=slot.text().strip())
            for (bar, slot_idx), slot in self._slots.items()
            if slot.text().strip()
        ]
