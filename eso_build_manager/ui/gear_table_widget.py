from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemDelegate, QComboBox, QCompleter, QHeaderView, QLineEdit,
    QStyledItemDelegate, QStyleOptionViewItem, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)

from eso_build_manager.constants import (
    ARMOR_ENCHANTS,
    ARMOR_WEIGHTS,
    GEAR_SLOTS,
    GEAR_TRAITS,
    JEWELRY_ENCHANTS,
    JEWELRY_TRAITS,
    QUALITY_TIERS,
    WEAPON_ENCHANTS,
    WEAPON_TRAITS,
    WEAPON_TYPES,
)
from eso_build_manager.data_loader import load_set_details, load_set_names
from eso_build_manager.models.gear import GearPiece

_JEWELRY_SLOTS = {"Neck", "Ring 1", "Ring 2"}
_WEAPON_SLOTS = {"Main Hand", "Off Hand", "Backup Main", "Backup Off"}
_OFFHAND_SLOTS = {"Off Hand", "Backup Off"}
_MAINHAND_SLOTS = {"Main Hand", "Backup Main"}
_NO_WEIGHT_SLOTS = _JEWELRY_SLOTS  # weapon slots handled separately

_COL_SET = 0
_COL_WEIGHT = 1
_COL_TRAIT = 2
_COL_ENCHANT = 3
_COL_QUALITY = 4

_SET_NAMES: Optional[list[str]] = None
_SET_DETAILS: Optional[dict[str, dict]] = None


def _get_set_names() -> list[str]:
    global _SET_NAMES
    if _SET_NAMES is None:
        _SET_NAMES = load_set_names()
    return _SET_NAMES


def _get_set_details() -> dict[str, dict]:
    global _SET_DETAILS
    if _SET_DETAILS is None:
        _SET_DETAILS = load_set_details()
    return _SET_DETAILS


def _build_tooltip(name: str) -> str:
    details = _get_set_details().get(name)
    if not details:
        return ""
    header = f"<b>{name}</b> &nbsp;<i>{details['type']} — {details['source']}</i>"
    bonuses = "<br>".join(details.get("bonuses", []))
    return f"{header}<br><br>{bonuses}"


class _SetDelegate(QStyledItemDelegate):
    """Autocomplete for the Set column."""

    def createEditor(self, parent, option, index):
        if index.column() == _COL_SET:
            edit = QLineEdit(parent)
            c = QCompleter(_get_set_names(), edit)
            c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            c.setFilterMode(Qt.MatchFlag.MatchContains)
            c.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            edit.setCompleter(c)
            return edit
        return super().createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        if index.column() == _COL_SET and isinstance(editor, QLineEdit):
            editor.setText(index.data() or "")
        else:
            super().setEditorData(editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == _COL_SET and isinstance(editor, QLineEdit):
            name = editor.text()
            model.setData(index, name)
            model.setData(index, _build_tooltip(name), Qt.ItemDataRole.ToolTipRole)
        else:
            super().setModelData(editor, model, index)


class GearTableWidget(QWidget):
    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._blocking = True

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget(len(GEAR_SLOTS), 5)
        self._table.setVerticalHeaderLabels(GEAR_SLOTS)
        self._table.setHorizontalHeaderLabels(["Set", "Type / Weight", "Trait", "Enchant", "Quality"])
        self._table.setItemDelegate(_SetDelegate(self._table))
        hh = self._table.horizontalHeader()
        hh.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        hh.setSectionResizeMode(_COL_WEIGHT, QHeaderView.ResizeMode.ResizeToContents)
        hh.setSectionResizeMode(_COL_QUALITY, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setDefaultSectionSize(28)

        for row, slot in enumerate(GEAR_SLOTS):
            self._table.setItem(row, _COL_SET, QTableWidgetItem(""))

            weight_combo = QComboBox()
            if slot in _OFFHAND_SLOTS:
                weight_combo.addItems(["—", "N/A"])
                weight_combo.currentIndexChanged.connect(lambda _, r=row: self._on_offhand_changed(r))
            elif slot in _MAINHAND_SLOTS:
                weight_combo.addItems([""] + WEAPON_TYPES)
            elif slot in _NO_WEIGHT_SLOTS:
                weight_combo.addItem("—")
                weight_combo.setEnabled(False)
            else:
                weight_combo.addItems([""] + ARMOR_WEIGHTS)
            weight_combo.currentIndexChanged.connect(self._on_change)
            self._table.setCellWidget(row, _COL_WEIGHT, weight_combo)

            trait_combo = QComboBox()
            if slot in _JEWELRY_SLOTS:
                trait_combo.addItems([""] + JEWELRY_TRAITS)
            elif slot in _WEAPON_SLOTS:
                trait_combo.addItems([""] + WEAPON_TRAITS)
            else:
                trait_combo.addItems([""] + GEAR_TRAITS)
            trait_combo.currentIndexChanged.connect(self._on_change)
            self._table.setCellWidget(row, _COL_TRAIT, trait_combo)

            enchant_combo = QComboBox()
            enchant_combo.setEditable(True)
            if slot in _JEWELRY_SLOTS:
                enchant_combo.addItems([""] + JEWELRY_ENCHANTS)
            elif slot in _WEAPON_SLOTS:
                enchant_combo.addItems([""] + WEAPON_ENCHANTS)
            else:
                enchant_combo.addItems([""] + ARMOR_ENCHANTS)
            c = QCompleter(enchant_combo.model(), enchant_combo)
            c.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
            c.setFilterMode(Qt.MatchFlag.MatchContains)
            c.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)
            enchant_combo.setCompleter(c)
            enchant_combo.currentTextChanged.connect(self._on_change)
            self._table.setCellWidget(row, _COL_ENCHANT, enchant_combo)

            quality_combo = QComboBox()
            quality_combo.addItems(QUALITY_TIERS)
            quality_combo.setCurrentIndex(QUALITY_TIERS.index("Epic"))
            quality_combo.currentIndexChanged.connect(self._on_change)
            self._table.setCellWidget(row, _COL_QUALITY, quality_combo)

        self._table.itemChanged.connect(self._on_change)
        layout.addWidget(self._table)
        self._blocking = False

    def _on_change(self):
        if not self._blocking:
            self.changed.emit()

    def _on_offhand_changed(self, row: int) -> None:
        weight_combo: QComboBox = self._table.cellWidget(row, _COL_WEIGHT)
        is_na = weight_combo and weight_combo.currentText() == "N/A"
        self._set_row_na(row, is_na)

    def _set_row_na(self, row: int, na: bool) -> None:
        ro_flags = Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable
        rw_flags = ro_flags | Qt.ItemFlag.ItemIsEditable
        set_item = self._table.item(row, _COL_SET)
        if set_item:
            set_item.setFlags(ro_flags if na else rw_flags)
            if na:
                set_item.setText("")
        for col in (_COL_TRAIT, _COL_ENCHANT, _COL_QUALITY):
            combo: QComboBox = self._table.cellWidget(row, col)
            if combo:
                combo.setEnabled(not na)
                if na:
                    combo.setCurrentIndex(0)

    def load(self, gear: list[GearPiece]) -> None:
        self._blocking = True
        gear_by_slot = {g.slot: g for g in gear}

        for row, slot in enumerate(GEAR_SLOTS):
            piece = gear_by_slot.get(slot)
            if piece is None:
                continue

            item = self._table.item(row, _COL_SET)
            if item:
                item.setText(piece.set_name)
                item.setToolTip(_build_tooltip(piece.set_name))

            weight_combo: QComboBox = self._table.cellWidget(row, _COL_WEIGHT)
            if weight_combo and slot not in _NO_WEIGHT_SLOTS:
                idx = weight_combo.findText(piece.weight)
                weight_combo.setCurrentIndex(idx if idx >= 0 else 0)
            if slot in _OFFHAND_SLOTS:
                self._set_row_na(row, piece.weight == "N/A")

            trait_combo: QComboBox = self._table.cellWidget(row, _COL_TRAIT)
            if trait_combo:
                idx = trait_combo.findText(piece.trait)
                trait_combo.setCurrentIndex(idx if idx >= 0 else 0)

            enchant_combo: QComboBox = self._table.cellWidget(row, _COL_ENCHANT)
            if enchant_combo:
                idx = enchant_combo.findText(piece.enchant)
                if idx >= 0:
                    enchant_combo.setCurrentIndex(idx)
                else:
                    enchant_combo.setCurrentText(piece.enchant)

            quality_combo: QComboBox = self._table.cellWidget(row, _COL_QUALITY)
            if quality_combo:
                idx = quality_combo.findText(piece.quality)
                quality_combo.setCurrentIndex(idx if idx >= 0 else QUALITY_TIERS.index("Epic"))

        self._blocking = False

    def get_gear(self, build_id: int) -> list[GearPiece]:
        pieces = []
        for row, slot in enumerate(GEAR_SLOTS):
            set_item = self._table.item(row, _COL_SET)
            weight_combo: QComboBox = self._table.cellWidget(row, _COL_WEIGHT)
            trait_combo: QComboBox = self._table.cellWidget(row, _COL_TRAIT)
            enchant_combo: QComboBox = self._table.cellWidget(row, _COL_ENCHANT)
            quality_combo: QComboBox = self._table.cellWidget(row, _COL_QUALITY)

            pieces.append(GearPiece(
                build_id=build_id,
                slot=slot,
                set_name=set_item.text() if set_item else "",
                weight=weight_combo.currentText() if (weight_combo and (weight_combo.isEnabled() or slot in _OFFHAND_SLOTS)) else "",
                trait=trait_combo.currentText() if trait_combo else "",
                enchant=enchant_combo.currentText() if enchant_combo else "",
                quality=quality_combo.currentText() if quality_combo else "Epic",
            ))
        return pieces
