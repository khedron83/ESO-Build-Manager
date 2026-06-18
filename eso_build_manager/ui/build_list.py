from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QFont
from PySide6.QtWidgets import (
    QFileDialog, QHeaderView, QLineEdit, QMenu, QMessageBox,
    QToolButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
)

import eso_build_manager.storage.database as db
from eso_build_manager.constants import CLASS_COLORS, ROLE_COLORS
from eso_build_manager.models.build import Build

_ROLE_ORDER = ["Tank", "Healer", "DPS", "Hybrid", ""]
_CONTENT_ORDER = ["Dungeon", "Trial", "Solo", "Overland", "PvP", ""]
_ROLE_ALIAS = {"MagDPS": "DPS", "StamDPS": "DPS"}


class BuildListPanel(QWidget):
    build_selected = Signal(int)
    build_deleted = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(275)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        self._actions_btn = QToolButton()
        self._actions_btn.setText("Build Actions")
        self._actions_btn.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self._actions_btn.setSizePolicy(
            self._actions_btn.sizePolicy().horizontalPolicy(),
            self._actions_btn.sizePolicy().verticalPolicy(),
        )
        self._actions_btn.setStyleSheet("QToolButton { padding: 4px 8px; }"
                                        "QToolButton::menu-indicator { width: 12px; }")
        actions_menu = QMenu(self._actions_btn)
        actions_menu.addAction(QAction("Add Build", self, triggered=self._add))
        actions_menu.addAction(QAction("Duplicate Build", self, triggered=self._duplicate))
        actions_menu.addAction(QAction("Delete Build", self, triggered=self._delete))
        actions_menu.addSeparator()
        actions_menu.addAction(QAction("Import JSON…", self, triggered=self._import))
        self._actions_btn.setMenu(actions_menu)
        layout.addWidget(self._actions_btn)

        self._search = QLineEdit()
        self._search.setPlaceholderText("Search builds…")
        self._search.setClearButtonEnabled(True)
        self._search.textChanged.connect(self._on_search)
        layout.addWidget(self._search)

        self._tree = QTreeWidget()
        self._tree.setColumnCount(2)
        self._tree.setHeaderHidden(True)
        self._tree.setIndentation(14)
        self._tree.setAnimated(True)
        self._tree.setUniformRowHeights(False)
        self._tree.header().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._tree.header().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self._tree.setColumnWidth(1, 85)
        self._tree.setStyleSheet("""
            QTreeWidget {
                border: none;
                font-size: 13px;
            }
            QTreeWidget::item {
                padding: 3px 2px;
            }
            QTreeWidget::item:selected {
                border-radius: 4px;
            }
        """)
        self._tree.currentItemChanged.connect(self._on_item_changed)
        layout.addWidget(self._tree)

        self._all_builds: list[tuple[int, str, str, str, str]] = []
        self._build_items: dict[int, QTreeWidgetItem] = {}
        self.refresh()

    # ── Public API ────────────────────────────────────────────────────────

    def refresh(self, select_id: int | None = None) -> None:
        self._all_builds = db.list_builds_meta()
        self._rebuild_tree(self._search.text(), select_id)

    def current_build_id(self) -> int | None:
        item = self._tree.currentItem()
        if item is None:
            return None
        return item.data(0, Qt.ItemDataRole.UserRole)

    def update_current_name(self, name: str) -> None:
        item = self._tree.currentItem()
        if item and item.data(0, Qt.ItemDataRole.UserRole) is not None:
            item.setText(0, name)
            bid = item.data(0, Qt.ItemDataRole.UserRole)
            self._all_builds = [
                (i, name if i == bid else n, r, c, ct)
                for i, n, r, c, ct in self._all_builds
            ]

    # ── Tree building ─────────────────────────────────────────────────────

    def _rebuild_tree(self, filter_text: str = "", select_id: int | None = None) -> None:
        restore_id = select_id if select_id is not None else self.current_build_id()

        self._tree.blockSignals(True)
        self._tree.clear()
        self._build_items.clear()

        term = filter_text.lower().strip()
        # by_role → by_content → [(id, name, eso_class)]
        by_role: dict[str, dict[str, list]] = {r: {} for r in _ROLE_ORDER}
        for build_id, name, role, eso_class, content in self._all_builds:
            if term and term not in name.lower() and term not in (eso_class or "").lower():
                continue
            role_key = _ROLE_ALIAS.get(role, role)
            if role_key not in by_role:
                role_key = ""
            content_key = content or ""
            by_role[role_key].setdefault(content_key, []).append((build_id, name, eso_class or ""))

        for role in _ROLE_ORDER:
            by_content = by_role[role]
            total = sum(len(v) for v in by_content.values())
            if not total and term:
                continue

            label = role if role else "Other"
            color_hex = ROLE_COLORS.get(role, "#888888")

            group = QTreeWidgetItem([f"  {label}", f"({total})"])
            group.setFlags(Qt.ItemFlag.ItemIsEnabled)

            gf = QFont()
            gf.setBold(True)
            gf.setPointSize(gf.pointSize() - 1)
            group.setFont(0, gf)

            sf = QFont()
            sf.setItalic(True)
            sf.setPointSize(sf.pointSize() - 1)
            group.setFont(1, sf)

            group.setForeground(0, QColor(color_hex))
            group.setForeground(1, QColor("#666666"))

            self._tree.addTopLevelItem(group)
            group.setExpanded(True)

            # Use content sub-groups when builds span multiple content types,
            # or when any build has a named content type
            use_sub = len(by_content) > 1 or (
                len(by_content) == 1 and list(by_content)[0] != ""
            )

            for content_key in _CONTENT_ORDER:
                builds = by_content.get(content_key, [])
                if not builds:
                    continue

                if use_sub:
                    sub_label = content_key if content_key else "Other"
                    sub_item = QTreeWidgetItem([f"    {sub_label}", f"({len(builds)})"])
                    sub_item.setFlags(Qt.ItemFlag.ItemIsEnabled)
                    csf = QFont()
                    csf.setPointSize(csf.pointSize() - 1)
                    sub_item.setFont(0, csf)
                    sub_item.setFont(1, csf)
                    sub_item.setForeground(0, QColor("#888888"))
                    sub_item.setForeground(1, QColor("#555555"))
                    group.addChild(sub_item)
                    sub_item.setExpanded(True)
                    parent = sub_item
                else:
                    parent = group

                for build_id, name, eso_class in builds:
                    child = QTreeWidgetItem([f"  {name}", eso_class])
                    child.setData(0, Qt.ItemDataRole.UserRole, build_id)
                    if eso_class in CLASS_COLORS:
                        child.setForeground(1, QColor(CLASS_COLORS[eso_class]))
                    cf = QFont()
                    cf.setPointSize(cf.pointSize() - 1)
                    child.setFont(1, cf)
                    parent.addChild(child)
                    self._build_items[build_id] = child

        self._tree.blockSignals(False)

        if restore_id and restore_id in self._build_items:
            self._tree.setCurrentItem(self._build_items[restore_id])
        else:
            for bid in (b[0] for b in self._all_builds):
                if bid in self._build_items:
                    self._tree.setCurrentItem(self._build_items[bid])
                    break

    # ── Slot handlers ─────────────────────────────────────────────────────

    def _on_search(self, text: str) -> None:
        self._rebuild_tree(text)

    def _on_item_changed(self, current: QTreeWidgetItem | None, _prev) -> None:
        if current is None:
            return
        build_id = current.data(0, Qt.ItemDataRole.UserRole)
        if build_id is not None:
            self.build_selected.emit(build_id)

    def _add(self) -> None:
        build_id = db.create_build(Build())
        self.refresh(select_id=build_id)

    def _duplicate(self) -> None:
        bid = self.current_build_id()
        if bid is None:
            return
        new_id = db.duplicate_build(bid)
        self.refresh(select_id=new_id)

    def _import(self) -> None:
        import json
        path, _ = QFileDialog.getOpenFileName(
            self, "Import Build", "", "JSON files (*.json)"
        )
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            from eso_build_manager.exporter import import_build_dict
            build_id = import_build_dict(data)
            self.refresh(select_id=build_id)
        except Exception as e:
            QMessageBox.critical(self, "Import Failed", str(e))

    def _delete(self) -> None:
        bid = self.current_build_id()
        if bid is None:
            return
        item = self._tree.currentItem()
        answer = QMessageBox.question(
            self, "Delete Build",
            f'Delete "{item.text(0).strip()}"? This cannot be undone.',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            db.delete_build(bid)
            self.refresh()
            self.build_deleted.emit()
