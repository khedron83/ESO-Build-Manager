from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout, QInputDialog, QMessageBox, QPushButton,
    QSplitter, QTabWidget, QVBoxLayout, QWidget,
)

from eso_build_manager.models.gear import GearPiece
from eso_build_manager.models.skill import Skill
from eso_build_manager.ui.gear_table_widget import GearTableWidget
from eso_build_manager.ui.skill_bar_widget import SkillBarWidget


class _LoadoutPage(QWidget):
    """One page's skill bar + gear table, stacked."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        splitter = QSplitter(Qt.Orientation.Vertical)
        self.skill_bar = SkillBarWidget()
        self.gear_table = GearTableWidget()
        splitter.addWidget(self.skill_bar)
        splitter.addWidget(self.gear_table)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([180, 400])
        layout.addWidget(splitter)

        self.skill_bar.changed.connect(self.changed)
        self.gear_table.changed.connect(self.changed)


class LoadoutPagesWidget(QWidget):
    """Tabbed skill bar + gear table — one page per loadout (e.g. Main/Trash/Boss)."""

    changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._tabs = QTabWidget()
        self._tabs.setTabsClosable(False)
        self._tabs.tabBarDoubleClicked.connect(self._rename_page)

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.addStretch()
        add_btn = QPushButton("+ Add Page")
        add_btn.setToolTip("Add a loadout page (e.g. Trash, Boss) with its own skills and gear")
        add_btn.clicked.connect(self._add_page)
        remove_btn = QPushButton("− Remove Page")
        remove_btn.setToolTip("Remove the current loadout page")
        remove_btn.clicked.connect(self._remove_current_page)
        button_row.addWidget(add_btn)
        button_row.addWidget(remove_btn)

        layout.addLayout(button_row)
        layout.addWidget(self._tabs)

    def _new_page(self) -> _LoadoutPage:
        page = _LoadoutPage()
        page.changed.connect(self.changed)
        return page

    def _add_page(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Loadout Page", "Page name:")
        name = name.strip()
        if not ok or not name:
            return
        self._tabs.addTab(self._new_page(), name)
        self._tabs.setCurrentIndex(self._tabs.count() - 1)
        self.changed.emit()

    def _remove_current_page(self) -> None:
        if self._tabs.count() <= 1:
            QMessageBox.information(self, "Remove Loadout Page", "A build needs at least one page.")
            return
        idx = self._tabs.currentIndex()
        if QMessageBox.question(
            self, "Remove Loadout Page",
            f"Remove page '{self._tabs.tabText(idx)}'? This discards its skills and gear."
        ) != QMessageBox.StandardButton.Yes:
            return
        widget = self._tabs.widget(idx)
        self._tabs.removeTab(idx)
        widget.deleteLater()
        self.changed.emit()

    def _rename_page(self, idx: int) -> None:
        if idx < 0:
            return
        name, ok = QInputDialog.getText(
            self, "Rename Loadout Page", "Page name:", text=self._tabs.tabText(idx)
        )
        name = name.strip()
        if ok and name:
            self._tabs.setTabText(idx, name)
            self.changed.emit()

    def load(self, page_names: list[str], skills: list[Skill], gear: list[GearPiece]) -> None:
        while self._tabs.count():
            w = self._tabs.widget(0)
            self._tabs.removeTab(0)
            w.deleteLater()

        skills_by_page: dict[int, list[Skill]] = {}
        for s in skills:
            skills_by_page.setdefault(s.page, []).append(s)
        gear_by_page: dict[int, list[GearPiece]] = {}
        for g in gear:
            gear_by_page.setdefault(g.page, []).append(g)

        for i, name in enumerate(page_names or ["Main"]):
            page = self._new_page()
            page.skill_bar.load(skills_by_page.get(i, []))
            page.gear_table.load(gear_by_page.get(i, []))
            self._tabs.addTab(page, name)

    def get_page_names(self) -> list[str]:
        return [self._tabs.tabText(i) for i in range(self._tabs.count())]

    def get_skills(self, build_id: int) -> list[Skill]:
        skills = []
        for i in range(self._tabs.count()):
            page: _LoadoutPage = self._tabs.widget(i)
            for skill in page.skill_bar.get_skills(build_id):
                skill.page = i
                skills.append(skill)
        return skills

    def get_gear(self, build_id: int) -> list[GearPiece]:
        pieces = []
        for i in range(self._tabs.count()):
            page: _LoadoutPage = self._tabs.widget(i)
            for piece in page.gear_table.get_gear(build_id):
                piece.page = i
                pieces.append(piece)
        return pieces
