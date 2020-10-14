import os
import pathlib

from fbs_runtime.application_context.PyQt5 import (
    ApplicationContext as _ApplicationContext,
)
from PyQt5.QtCore import QFileSystemWatcher, QObject, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QFileDialog, QMainWindow

from buffbot.core import BuffBot, Character
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
    characterDetails = pyqtSignal(Character)
    monitoringFile = pyqtSignal(str)

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

        if self._buffbot is not None:
            self._buffbot.close()

        self.finished.emit()

    def stop(self):
        self._stopping.emit()

    def _do_create_bot(self, filename):
        filename = os.path.abspath(filename)

        # If we have an existing buffbot that is listening to a different
        # file, then we need to stop watching that file, close out our
        # existing buffbot, and set it to None so that a new one can be
        # created later.
        if self._buffbot is not None:
            if not os.path.samefile(filename, self._buffbot.filename):
                self._watcher.removePath(self._buffbot.filename)
                self._watcher.removePath(os.path.dirname(self._buffbot.filename))
                self._buffbot.close()
                self._buffbot = None

        # If we don't have a buffbot, either because we're just starting
        # or because the file has changed, then create a new one and
        # start watching the file and the directory containing that file.
        if self._buffbot is None:
            self._buffbot = BuffBot(filename=filename)
            self.characterDetails.emit(self._buffbot.character)
            self._buffbot.load()
            self._watcher.addPath(filename)
            self._watcher.addPath(os.path.dirname(filename))

        self.monitoringFile.emit(filename)

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

        # Setup our default UI values, we do this here instead of in QT Designer,
        # because QT Designer has default text that makes it easier to tell what
        # is happening when laying out the UI, but which isn't the best default
        # when first opening the application.
        self.character_name.setText("")
        self.character_server.setText("")

        # Spawn our background worker thread and schedule the worker to
        # start in it once the thread starts, and the thread to quit when
        # the worker is finished, and finally the entire app to quit wen
        # the thread exits.
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.worker.finished.connect(self.thread.quit)
        self.thread.started.connect(self.worker.start)
        self.thread.finished.connect(QApplication.instance().exit)

        # Wire the worker up to be able to pass data back into the UI.
        self.worker.characterDetails.connect(self.update_character)
        self.worker.monitoringFile.connect(self.update_statusbar)

        # Start our thread so it can start processing information.
        self.thread.start()

    def closeEvent(self, e):
        # If the thread is running, we'll tell the worker to stop, and rely on
        # the signals to have first the thread shutdown, and then the entire
        # application, and since we're relying on the signals to close the
        # application, we can ignore this event.
        #
        # However, if the thread is not running for some reason (this shouldn't)
        # ever happen, but just in case it does, we'll just process this event as
        # normal, and let Qt close our application.
        if self.thread.isRunning():
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

    def update_character(self, char):
        self.character_name.setText(char.name)
        self.character_server.setText(char.server_display)

    def update_statusbar(self, filename):
        self.statusbar.showMessage(f"Monitoring {filename}")
