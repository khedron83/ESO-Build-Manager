from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QLabel,
    QRadioButton,
    QVBoxLayout,
)


class OptionsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Options")
        self.setMinimumWidth(380)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        sync_group = QGroupBox("Save file source")
        sync_layout = QVBoxLayout(sync_group)

        self._zeus_radio = QRadioButton("Connect to Zeus")
        self._this_pc_radio = QRadioButton("This PC")
        sync_layout.addWidget(self._zeus_radio)
        sync_layout.addWidget(self._this_pc_radio)

        note = QLabel(
            "<small>Connect to Zeus syncs save files over the network via scp. "
            "Use This PC when the game and build manager are running on the same "
            "machine (e.g. streaming from this PC) to read save files directly "
            "from disk instead.</small>"
        )
        note.setWordWrap(True)
        sync_layout.addWidget(note)

        layout.addWidget(sync_group)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _load(self):
        mode = QSettings().value("sync/mode", "zeus")
        self._this_pc_radio.setChecked(mode == "this_pc")
        self._zeus_radio.setChecked(mode != "this_pc")

    def _save_and_accept(self):
        mode = "this_pc" if self._this_pc_radio.isChecked() else "zeus"
        QSettings().setValue("sync/mode", mode)
        self.accept()
