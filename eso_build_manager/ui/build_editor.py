import json

from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QPlainTextEdit, QSpinBox, QSplitter, QTabWidget, QVBoxLayout, QWidget,
)

import eso_build_manager.storage.database as db
from eso_build_manager.constants import (
    CLASS_SKILL_LINES, CONTENT_TYPES, ESO_CLASSES, GAME_PATCHES, MUNDUS_STONES, ROLES,
)
from eso_build_manager.models.build import Build
from eso_build_manager.ui.class_mastery_widget import ClassMasteryWidget
from eso_build_manager.ui.cp_widget import CPWidget
from eso_build_manager.ui.loadout_pages_widget import LoadoutPagesWidget

def _line_to_class(line: str) -> str:
    for cls, lines in CLASS_SKILL_LINES.items():
        if line in lines:
            return cls
    return ""


_PH_CLASS = "— Class —"
_PH_ROLE = "— Role —"
_PH_CONTENT = "— Content —"
_PH_SUB1 = "— Sub 1 —"
_PH_SUB2 = "— Sub 2 —"


class BuildEditorPanel(QWidget):
    name_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_id: int | None = None
        self._blocking = False

        self._save_timer = QTimer(self)
        self._save_timer.setSingleShot(True)
        self._save_timer.setInterval(400)
        self._save_timer.timeout.connect(self._save)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(6)

        # ── Row 1: name | role | content ─────────────────────────────────
        row1 = QHBoxLayout()
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("Build name")
        font = self._name_edit.font()
        font.setPointSize(font.pointSize() + 2)
        self._name_edit.setFont(font)

        self._role_combo = QComboBox()
        self._role_combo.addItem(_PH_ROLE)
        self._role_combo.addItems(ROLES)

        self._content_combo = QComboBox()
        self._content_combo.addItem(_PH_CONTENT)
        self._content_combo.addItems(CONTENT_TYPES)

        self._patch_combo = QComboBox()
        self._patch_combo.addItems(GAME_PATCHES)
        self._patch_combo.setCurrentText("U50")
        self._patch_combo.setFixedWidth(68)

        row1.addWidget(self._name_edit, stretch=2)
        row1.addWidget(QLabel("Role:"))
        row1.addWidget(self._role_combo)
        row1.addWidget(QLabel("Content:"))
        row1.addWidget(self._content_combo)
        row1.addWidget(QLabel("Patch:"))
        row1.addWidget(self._patch_combo)

        # ── Row 2: primary class | subclass toggle | sub1 | sub2 ─────────
        row2 = QHBoxLayout()
        self._class_combo = QComboBox()
        self._class_combo.addItem(_PH_CLASS)
        self._class_combo.addItems(ESO_CLASSES)

        self._sub_check = QCheckBox("Pure Class")

        self._sub1_label = QLabel("Sub 1:")
        self._sub1_combo = QComboBox()
        self._sub1_combo.addItem(_PH_SUB1)

        self._sub2_label = QLabel("Sub 2:")
        self._sub2_combo = QComboBox()
        self._sub2_combo.addItem(_PH_SUB2)

        row2.addWidget(QLabel("Class:"))
        row2.addWidget(self._class_combo)
        row2.addSpacing(12)
        row2.addWidget(self._sub_check)
        row2.addWidget(self._sub1_label)
        row2.addWidget(self._sub1_combo)
        row2.addWidget(self._sub2_label)
        row2.addWidget(self._sub2_combo)
        row2.addStretch()

        row3 = QHBoxLayout()
        self._source_edit = QLineEdit()
        self._source_edit.setPlaceholderText("Source — e.g. https://skinny-cheeks.com/... or Alcast, Hyperiox…")
        row3.addWidget(QLabel("Source:"))
        row3.addWidget(self._source_edit, stretch=1)

        outer.addLayout(row1)
        outer.addLayout(row2)
        outer.addLayout(row3)

        # ── Tabs ──────────────────────────────────────────────────────────
        self._tabs = QTabWidget()

        # Build tab: paged Skills+Gear (Main/Trash/Boss) above CP
        self._loadout_pages = LoadoutPagesWidget()
        self._cp_widget = CPWidget()

        build_splitter = QSplitter(Qt.Orientation.Vertical)
        build_splitter.addWidget(self._loadout_pages)
        build_splitter.addWidget(self._cp_widget)
        build_splitter.setStretchFactor(0, 1)  # loadout pages: expand
        build_splitter.setStretchFactor(1, 0)  # CP: fixed
        build_splitter.setSizes([480, 100])
        self._tabs.addTab(build_splitter, "Build")

        self._tabs.addTab(self._build_stats_tab(), "Stats")

        self._mastery_widget = ClassMasteryWidget()
        self._tabs.addTab(self._mastery_widget, "Passives")

        self._notes_edit = QPlainTextEdit()
        self._notes_edit.setPlaceholderText("Notes, rotation, tips...")
        self._tabs.addTab(self._notes_edit, "Notes")

        outer.addWidget(self._tabs)

        # ── Signal wiring ─────────────────────────────────────────────────
        self._name_edit.textChanged.connect(self._on_name_changed)
        self._class_combo.currentIndexChanged.connect(self._on_primary_class_changed)
        self._sub_check.toggled.connect(self._on_subclass_toggled)
        self._sub1_combo.currentIndexChanged.connect(self._on_sub1_changed)
        self._sub2_combo.currentIndexChanged.connect(self._schedule_save)
        self._role_combo.currentIndexChanged.connect(self._schedule_save)
        self._content_combo.currentIndexChanged.connect(self._schedule_save)
        self._patch_combo.currentIndexChanged.connect(self._schedule_save)
        self._source_edit.textChanged.connect(self._schedule_save)
        self._attr_health.valueChanged.connect(self._schedule_save)
        self._attr_magicka.valueChanged.connect(self._schedule_save)
        self._attr_stamina.valueChanged.connect(self._schedule_save)
        self._food_edit.textChanged.connect(self._schedule_save)
        self._mundus_combo.currentIndexChanged.connect(self._schedule_save)
        self._cp_notes.textChanged.connect(self._schedule_save)
        self._loadout_pages.changed.connect(self._schedule_save)
        self._cp_widget.changed.connect(self._schedule_save)
        self._mastery_widget.changed.connect(self._schedule_save)
        self._notes_edit.textChanged.connect(self._schedule_save)

        self._sub_check.setChecked(True)   # default: Pure Class, sub combos greyed
        self._set_sub_enabled(False)
        self.setEnabled(False)

    def _build_stats_tab(self) -> QWidget:
        w = QWidget()
        layout = QFormLayout(w)
        layout.setSpacing(10)

        self._attr_health = QSpinBox()
        self._attr_health.setRange(0, 64)
        self._attr_health.setSuffix(" pts")
        self._attr_magicka = QSpinBox()
        self._attr_magicka.setRange(0, 64)
        self._attr_magicka.setSuffix(" pts")
        self._attr_stamina = QSpinBox()
        self._attr_stamina.setRange(0, 64)
        self._attr_stamina.setSuffix(" pts")

        layout.addRow("Health:", self._attr_health)
        layout.addRow("Magicka:", self._attr_magicka)
        layout.addRow("Stamina:", self._attr_stamina)

        self._food_edit = QLineEdit()
        self._food_edit.setPlaceholderText("e.g. Solitude Salmon-Millet Soup")
        layout.addRow("Food / Drink:", self._food_edit)

        self._mundus_combo = QComboBox()
        self._mundus_combo.addItem("— None —")
        self._mundus_combo.addItems(MUNDUS_STONES)
        layout.addRow("Mundus Stone:", self._mundus_combo)

        self._cp_notes = QPlainTextEdit()
        self._cp_notes.setPlaceholderText("Total CP, allocation strategy notes...")
        self._cp_notes.setMaximumHeight(100)
        layout.addRow("CP Notes:", self._cp_notes)

        return w

    # ── Public API ────────────────────────────────────────────────────────

    def load_build(self, build_id: int) -> None:
        self._save_timer.stop()
        build = db.get_build(build_id)
        if build is None:
            return

        self._current_id = build_id
        self._blocking = True

        self._name_edit.setText(build.name)
        self._load_combo(self._class_combo, build.eso_class, _PH_CLASS)
        self._load_combo(self._role_combo, build.role, _PH_ROLE)
        self._load_combo(self._content_combo, build.content, _PH_CONTENT)
        self._patch_combo.setCurrentText(build.game_patch or "U50")
        self._source_edit.setText(build.source)

        has_sub = bool(build.subclass_1 or build.subclass_2)
        self._sub_check.setChecked(not has_sub)
        self._rebuild_sub_combos(build.eso_class, build.subclass_1, build.subclass_2)
        self._set_sub_enabled(has_sub)

        self._attr_health.setValue(build.attribute_health)
        self._attr_magicka.setValue(build.attribute_magicka)
        self._attr_stamina.setValue(build.attribute_stamina)
        self._food_edit.setText(build.food_buff)
        idx = self._mundus_combo.findText(build.mundus_stone or "")
        self._mundus_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self._cp_notes.setPlainText(build.champion_points)
        self._mastery_widget.load(build.eso_class, build.class_masteries)
        self._notes_edit.setPlainText(build.notes)
        self._cp_widget.load(build.cp_slots)
        gear_pages = json.loads(build.gear_pages) if build.gear_pages else ["Main"]
        self._loadout_pages.load(gear_pages, db.get_skills(build_id), db.get_gear(build_id))

        self._blocking = False
        self.setEnabled(True)

    def clear(self) -> None:
        self._current_id = None
        self.setEnabled(False)

    # ── Slot handlers ─────────────────────────────────────────────────────

    def _on_name_changed(self, text: str) -> None:
        if not self._blocking:
            self.name_changed.emit(text)
            self._schedule_save()

    def _on_primary_class_changed(self) -> None:
        if not self._blocking:
            primary = self._combo_text(self._class_combo)
            sub1 = self._combo_text(self._sub1_combo)
            sub2 = self._combo_text(self._sub2_combo)
            self._rebuild_sub_combos(primary, sub1, sub2)
            self._mastery_widget.set_class(primary)
            self._schedule_save()

    def _on_sub1_changed(self) -> None:
        if not self._blocking:
            primary = self._combo_text(self._class_combo)
            sub1 = self._combo_text(self._sub1_combo)
            sub2 = self._combo_text(self._sub2_combo)
            sub1_cls = _line_to_class(sub1)
            exc2 = {c for c in [primary, sub1_cls] if c}
            self._populate_subclass_combo(self._sub2_combo, exc2, sub2, _PH_SUB2)
            self._schedule_save()

    def _on_subclass_toggled(self, checked: bool) -> None:
        # checked = Pure Class → disable sub combos; unchecked → enable
        self._set_sub_enabled(not checked)
        if not checked:
            primary = self._combo_text(self._class_combo)
            self._rebuild_sub_combos(primary, "", "")
        else:
            self._sub1_combo.blockSignals(True)
            self._sub2_combo.blockSignals(True)
            self._sub1_combo.setCurrentIndex(0)
            self._sub2_combo.setCurrentIndex(0)
            self._sub1_combo.blockSignals(False)
            self._sub2_combo.blockSignals(False)
        if not self._blocking:
            self._schedule_save()

    # ── Helpers ───────────────────────────────────────────────────────────

    def _set_sub_enabled(self, enabled: bool) -> None:
        for w in (self._sub1_label, self._sub1_combo, self._sub2_label, self._sub2_combo):
            w.setEnabled(enabled)

    def _populate_subclass_combo(
        self, combo: QComboBox, excluded_classes: set, current_val: str, placeholder: str
    ) -> None:
        """Fill combo with skill lines from non-excluded classes, grouped by class."""
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(placeholder)
        for cls, lines in CLASS_SKILL_LINES.items():
            if cls in excluded_classes:
                continue
            idx = combo.count()
            combo.addItem(f"· {cls}")
            combo.model().item(idx).setEnabled(False)
            for line in lines:
                combo.addItem(line)
        idx = combo.findText(current_val)
        combo.setCurrentIndex(idx if idx >= 0 else 0)
        combo.blockSignals(False)

    def _rebuild_sub_combos(self, primary: str, sub1_val: str, sub2_val: str) -> None:
        exc1 = {primary} if primary else set()
        self._populate_subclass_combo(self._sub1_combo, exc1, sub1_val, _PH_SUB1)
        sub1_cls = _line_to_class(sub1_val)
        exc2 = exc1 | ({sub1_cls} if sub1_cls else set())
        self._populate_subclass_combo(self._sub2_combo, exc2, sub2_val, _PH_SUB2)

    def _schedule_save(self) -> None:
        if not self._blocking and self._current_id is not None:
            self._save_timer.start()

    def _save(self) -> None:
        if self._current_id is None:
            return
        use_sub = not self._sub_check.isChecked()  # Pure Class checked → no subclasses
        build = Build(
            id=self._current_id,
            name=self._name_edit.text().strip() or "New Build",
            eso_class=self._combo_text(self._class_combo),
            subclass_1=self._combo_text(self._sub1_combo) if use_sub else "",
            subclass_2=self._combo_text(self._sub2_combo) if use_sub else "",
            role=self._combo_text(self._role_combo),
            content=self._combo_text(self._content_combo),
            game_patch=self._patch_combo.currentText(),
            source=self._source_edit.text().strip(),
            attribute_health=self._attr_health.value(),
            attribute_magicka=self._attr_magicka.value(),
            attribute_stamina=self._attr_stamina.value(),
            food_buff=self._food_edit.text().strip(),
            mundus_stone=self._combo_text(self._mundus_combo),
            champion_points=self._cp_notes.toPlainText().strip(),
            cp_slots=self._cp_widget.get_data(),
            class_masteries=self._mastery_widget.get_data(),
            gear_pages=json.dumps(self._loadout_pages.get_page_names()),
            notes=self._notes_edit.toPlainText(),
        )
        db.update_build(build)
        db.save_skills(self._current_id, self._loadout_pages.get_skills(self._current_id))
        db.save_gear(self._current_id, self._loadout_pages.get_gear(self._current_id))

    @staticmethod
    def _load_combo(combo: QComboBox, value: str, placeholder: str) -> None:
        if not value:
            combo.setCurrentText(placeholder)
            return
        idx = combo.findText(value)
        combo.setCurrentIndex(idx if idx >= 0 else 0)

    @staticmethod
    def _combo_text(combo: QComboBox) -> str:
        text = combo.currentText()
        return "" if text.startswith("—") else text
