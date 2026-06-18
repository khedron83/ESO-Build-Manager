from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QCloseEvent
from PySide6.QtWidgets import QLabel, QMainWindow, QMessageBox, QSplitter

from eso_build_manager.ui.build_editor_dialog import BuildEditorDialog
from eso_build_manager.ui.build_list import BuildListPanel
from eso_build_manager.ui.build_sheet import BuildSheetWidget
from eso_build_manager.ui.settings_dialog import NextcloudSettingsDialog


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ESO Build Manager")
        self.setMinimumSize(960, 620)

        self._settings = QSettings("CubicSerenity", "ESOBuildManager")
        geometry = self._settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        else:
            self.resize(1300, 780)

        self._build_list = BuildListPanel()
        self._build_sheet = BuildSheetWidget()
        self._editor_dialog: BuildEditorDialog | None = None

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._build_list)
        splitter.addWidget(self._build_sheet)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        self.setCentralWidget(splitter)

        self._status_label = QLabel("No build selected")
        self.statusBar().addWidget(self._status_label)

        self._build_list.build_selected.connect(self._on_build_selected)
        self._build_list.build_deleted.connect(self._on_build_deleted)
        self._build_sheet.edit_requested.connect(self._on_edit_requested)

        self._setup_menu()

        build_id = self._build_list.current_build_id()
        if build_id is not None:
            self._on_build_selected(build_id)

    def _setup_menu(self):
        nc_menu = self.menuBar().addMenu("Nextcloud")

        sync_action = QAction("Sync Now", self)
        sync_action.setShortcut("Ctrl+Shift+S")
        sync_action.triggered.connect(self._sync_now)
        nc_menu.addAction(sync_action)

        nc_menu.addSeparator()

        settings_action = QAction("Settings…", self)
        settings_action.triggered.connect(self._open_nc_settings)
        nc_menu.addAction(settings_action)

        help_menu = self.menuBar().addMenu("Help")
        about_action = QAction("About ESO Build Manager…", self)
        about_action.triggered.connect(self._about)
        help_menu.addAction(about_action)

    def _on_build_selected(self, build_id: int) -> None:
        self._build_sheet.load_build(build_id)
        self._status_label.setText(f"Build #{build_id}")

    def _on_build_deleted(self) -> None:
        if self._build_list.current_build_id() is None:
            self._build_sheet.clear()
            self._status_label.setText("No build selected")

    def _on_edit_requested(self, build_id: int) -> None:
        if self._editor_dialog is not None:
            self._editor_dialog.raise_()
            self._editor_dialog.activateWindow()
            return

        self._editor_dialog = BuildEditorDialog(build_id, None)
        self._editor_dialog.name_changed.connect(self._build_list.update_current_name)
        self._editor_dialog.finished.connect(self._on_editor_closed)
        self._editor_dialog.show()

    def _on_editor_closed(self) -> None:
        self._editor_dialog = None
        build_id = self._build_list.current_build_id()
        if build_id is not None:
            self._build_list.refresh(select_id=build_id)
            self._build_sheet.load_build(build_id)

    def _about(self):
        from eso_build_manager.constants import APP_VERSION
        QMessageBox.about(
            self,
            "About ESO Build Manager",
            f"<b>ESO Build Manager</b> v{APP_VERSION}<br><br>"
            "A desktop application for managing Elder Scrolls Online<br>"
            "character builds, with Nextcloud sync support.<br><br>"
            "Built with Python &amp; PySide6.<br>"
            "&copy; CubicSerenity",
        )

    def _open_nc_settings(self):
        dlg = NextcloudSettingsDialog(self)
        dlg.exec()

    def _sync_now(self):
        from eso_build_manager.sync.nextcloud import NextcloudSyncError, sync_all

        client = NextcloudSettingsDialog.get_sync_client()
        if client is None:
            QMessageBox.information(
                self,
                "Nextcloud Sync",
                "Configure your Nextcloud server under Nextcloud → Settings first.",
            )
            return

        self._status_label.setText("Syncing…")
        self.statusBar().repaint()

        try:
            uploaded, downloaded, errors = sync_all(client)
        except NextcloudSyncError as e:
            QMessageBox.warning(self, "Sync Failed", str(e))
            self._status_label.setText("Sync failed.")
            return

        if downloaded:
            self._build_list.refresh()

        parts = []
        if uploaded:
            parts.append(f"{uploaded} uploaded")
        if downloaded:
            parts.append(f"{downloaded} downloaded")
        summary = ", ".join(parts) if parts else "nothing to sync"
        self._status_label.setText(f"Sync done: {summary}.")

        if errors:
            QMessageBox.warning(
                self,
                "Sync Warnings",
                "Sync completed with errors:\n\n" + "\n".join(errors),
            )

    def closeEvent(self, event: QCloseEvent) -> None:
        self._settings.setValue("geometry", self.saveGeometry())
        super().closeEvent(event)
