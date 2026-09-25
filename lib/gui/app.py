from __future__ import annotations

ERROR = 'The Pathview+ GUI requires the optional GUI dependencies.\n\nInstall them with:\n\n    pip install "pathview-plus[gui]"'


def main(argv=None):
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print(ERROR)
        return 1
    from .main_window import create_window

    app = QApplication(argv or [])
    win = create_window()
    win.show()
    return app.exec()
