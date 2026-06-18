import sys
from eso_build_manager.app import create_app
from eso_build_manager.ui.main_window import MainWindow


def main():
    app = create_app(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
