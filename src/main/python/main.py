import sys

from PyQt5.QtWidgets import QApplication

from buffbot.ui import MainWindow

APP_NAME = "BuffBot"
APP_VERSION = "0.2.2"

if __name__ == "__main__":
    app = QApplication([])
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)

    window = MainWindow(APP_NAME, APP_VERSION)
    window.show()

    sys.exit(app.exec_())
