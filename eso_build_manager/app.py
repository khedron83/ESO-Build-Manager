import sys
from PySide6.QtWidgets import QApplication
from eso_build_manager.storage.database import init_db


def create_app(argv: list[str]) -> QApplication:
    app = QApplication(argv)
    app.setApplicationName("ESO Build Manager")
    app.setOrganizationName("CubicSerenity")
    app.setApplicationVersion("1.0.0")
    init_db()
    return app
