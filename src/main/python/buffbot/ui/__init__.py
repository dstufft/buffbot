import os
import pathlib

from fbs_runtime.application_context.PyQt5 import (
    ApplicationContext as _ApplicationContext,
)
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow

from buffbot.core import BuffBot
from buffbot.ui.generated.main_window import Ui_MainWindow

# Configuration
# Log File Location
#  - Parse: Character Name, Server Name
# Spells to Cast?
#   - Gem #
#   - Success Message
# Access List for Commands?


class ApplicationContext(_ApplicationContext):
    def run(self):
        window = MainWindow()
        window.show()

        return self.app.exec_()


class Worker(QObject):

    finished = pyqtSignal()

    _stopping = pyqtSignal()
    _filename = pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._buffbot = None

    def start(self):
        self._stopping.connect(self._do_stop)
        self._filename.connect(self._do_create_bot)

        # TODO: Change this from a timer, to a QFileSystemWatcherClass
        #       which will let this respond to events, rather than poll
        #       the file.
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.process)
        self._timer.start(0)

    def _do_stop(self):
        self._timer.stop()
        self.finished.emit()

    def stop(self):
        self._stopping.emit()

    def _do_create_bot(self, filename):
        if self._buffbot is not None:
            if not os.path.samefile(filename, self._buffbot.filename):
                # TODO: Cleanup the exiting BuffBot.
                self._buffbot = None

        if self._buffbot is None:
            self._buffbot = BuffBot(filename=filename)

    def filename(self, filename):
        self._filename.emit(filename)

    def process(self):
        # If there's no active BuffBot, then we skip this process
        if self._buffbot is None:
            return

        self._buffbot.process()


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)
        self.action_Open.triggered.connect(self.open_file)

        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.thread.started.connect(self.worker.start)
        self.thread.start()

    def closeEvent(self, e):
        if self.thread.isRunning():
            self.thread.finished.connect(QApplication.instance().exit)
            self.worker.stop()

            e.ignore()
        else:
            e.accept()

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Log File", os.fspath(pathlib.Path.home()), "Log Files (*.txt)"
        )

        if filename:
            self.worker.filename(filename)
