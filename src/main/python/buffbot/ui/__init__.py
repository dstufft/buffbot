import os
import pathlib

from fbs_runtime.application_context.PyQt5 import (
    ApplicationContext as _ApplicationContext,
)
from PyQt5.QtCore import QFileSystemWatcher, QObject, QThread, pyqtSignal
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

        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._process)
        self._watcher.directoryChanged.connect(self._check_for_monitored)

    def _do_stop(self):
        paths = self._watcher.directories() + self._watcher.files()
        if paths:
            self._watcher.removePaths(paths)

        self.finished.emit()

    def stop(self):
        self._stopping.emit()

    def _do_create_bot(self, filename):
        filename = os.path.abspath(filename)

        if self._buffbot is not None:
            if not os.path.samefile(filename, self._buffbot.filename):
                # TODO: Cleanup the exiting BuffBot.
                self._buffbot = None

        if self._buffbot is None:
            self._buffbot = BuffBot(filename=filename)
            self._watcher.addPath(filename)
            self._watcher.addPath(os.path.dirname(filename))

    def _check_for_monitored(self, path):
        # Check to see if our desired filename is currently being watched, if
        # it's not, then we'll need see if it exists on disk, and if so we'll
        # readd it back to our watching.
        if self._buffbot.filename not in self._watcher.files():
            if os.path.exists(self._buffbot.filename):
                self._watcher.addPath(self._buffbot.filename)
                self._buffbot.reload()
                self._process(self._buffbot.filename)

    def filename(self, filename):
        self._filename.emit(filename)

    def _process(self, path):
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
