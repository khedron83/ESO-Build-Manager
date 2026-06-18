from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QDialog, QVBoxLayout

from eso_build_manager.ui.build_editor import BuildEditorPanel


class BuildEditorDialog(QDialog):
    name_changed = Signal(str)

    def __init__(self, build_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Build")
        self.setMinimumSize(980, 700)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._editor = BuildEditorPanel()
        self._editor.name_changed.connect(self.name_changed)
        self._editor.load_build(build_id)
        layout.addWidget(self._editor)
