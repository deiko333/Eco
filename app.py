import sys
import traceback
from PyQt5.QtWidgets import QApplication, QMessageBox

from frontend.main_window import MainWindow


def install_exception_hook():
    def hook(exc_type, exc_value, exc_tb):
        text = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
        print(text, file=sys.stderr)
        try:
            box = QMessageBox()
            box.setIcon(QMessageBox.Critical)
            box.setWindowTitle("Unexpected Error")
            box.setText(f"{exc_type.__name__}: {exc_value}")
            box.setDetailedText(text)
            box.exec_()
        except Exception:
            pass

    sys.excepthook = hook


def main():
    install_exception_hook()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("EcoBalance")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
