from PySide6.QtCore import QSettings
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
)

from eso_build_manager.sync.nextcloud import NextcloudSync, NextcloudSyncError


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(420)
        self._build_ui()
        self._load()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        layout.addWidget(self._build_sync_group())
        layout.addWidget(self._build_nextcloud_group())

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _build_sync_group(self) -> QGroupBox:
        group = QGroupBox("Save file source")
        sync_layout = QVBoxLayout(group)

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

        return group

    def _build_nextcloud_group(self) -> QGroupBox:
        group = QGroupBox("Nextcloud")
        layout = QVBoxLayout(group)

        form = QFormLayout()

        self._url = QLineEdit()
        self._url.setPlaceholderText("https://cloud.example.com")
        form.addRow("Server URL:", self._url)

        self._user = QLineEdit()
        self._user.setPlaceholderText("your-username")
        form.addRow("Username:", self._user)

        self._pwd = QLineEdit()
        self._pwd.setEchoMode(QLineEdit.EchoMode.Password)
        self._pwd.setPlaceholderText("app password (recommended)")
        form.addRow("Password:", self._pwd)

        self._verify_ssl = QCheckBox("Verify SSL certificate")
        self._verify_ssl.setChecked(True)
        form.addRow("", self._verify_ssl)

        layout.addLayout(form)

        note = QLabel(
            "<small>Use an <b>app password</b> (Nextcloud → Settings → Security) "
            "rather than your account password. Builds are synced to "
            "<b>ESO-Builds/</b> in your Nextcloud files.</small>"
        )
        note.setWordWrap(True)
        layout.addWidget(note)

        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self._test)
        layout.addWidget(test_btn)

        self._status = QLabel()
        layout.addWidget(self._status)

        return group

    def _load(self):
        s = QSettings()

        mode = s.value("sync/mode", "zeus")
        self._this_pc_radio.setChecked(mode == "this_pc")
        self._zeus_radio.setChecked(mode != "this_pc")

        self._url.setText(s.value("nextcloud/url", ""))
        self._user.setText(s.value("nextcloud/username", ""))
        self._pwd.setText(s.value("nextcloud/password", ""))
        self._verify_ssl.setChecked(s.value("nextcloud/verify_ssl", True, type=bool))

    def _save_and_accept(self):
        if self._url.text().strip() and not self._user.text().strip():
            QMessageBox.warning(self, "Missing", "Nextcloud username is required if a server URL is set.")
            return

        s = QSettings()
        s.setValue("sync/mode", "this_pc" if self._this_pc_radio.isChecked() else "zeus")
        s.setValue("nextcloud/url", self._url.text().strip())
        s.setValue("nextcloud/username", self._user.text().strip())
        s.setValue("nextcloud/password", self._pwd.text())
        s.setValue("nextcloud/verify_ssl", self._verify_ssl.isChecked())
        self.accept()

    def _test(self):
        url = self._url.text().strip()
        user = self._user.text().strip()
        pwd = self._pwd.text()
        if not url or not user:
            self._status.setText("Fill in URL and username first.")
            return
        try:
            NextcloudSync(url, user, pwd, verify_ssl=self._verify_ssl.isChecked()).test_connection()
            self._status.setText("Connected successfully.")
            self._status.setStyleSheet("color: green;")
        except NextcloudSyncError as e:
            self._status.setText(str(e))
            self._status.setStyleSheet("color: red;")
        except Exception as e:
            self._status.setText(f"Error: {e}")
            self._status.setStyleSheet("color: red;")

    @staticmethod
    def get_sync_client() -> NextcloudSync | None:
        s = QSettings()
        url = s.value("nextcloud/url", "")
        user = s.value("nextcloud/username", "")
        pwd = s.value("nextcloud/password", "")
        verify_ssl = s.value("nextcloud/verify_ssl", True, type=bool)
        if url and user:
            return NextcloudSync(url, user, pwd, verify_ssl=verify_ssl)
        return None
