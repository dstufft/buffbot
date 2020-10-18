import datetime
import os
import pathlib

from fbs_runtime.application_context.PyQt5 import (
    ApplicationContext as _ApplicationContext,
)
from PyQt5 import QtSql
from PyQt5.QtCore import (
    QAbstractListModel,
    QFileSystemWatcher,
    QObject,
    QStandardPaths,
    Qt,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt5.QtWidgets import (
    QApplication,
    QDialog,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QTableWidgetItem,
)

from buffbot.core import BuffBot, Character, Spell
from buffbot.ui.generated.add_acl import Ui_AddACL
from buffbot.ui.generated.add_spell import Ui_AddSpell
from buffbot.ui.generated.main_window import Ui_MainWindow


class ApplicationContext(_ApplicationContext):
    def run(self):
        window = MainWindow()
        window.show()

        return self.app.exec_()


class Worker(QObject):

    started = pyqtSignal()
    finished = pyqtSignal()
    characterDetails = pyqtSignal(Character)
    monitoringFile = pyqtSignal(str)
    logMessage = pyqtSignal(datetime.datetime, str)

    _stopping = pyqtSignal()
    _configure = pyqtSignal(str, list, list)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._buffbot = None

    def start(self):
        self._stopping.connect(self._do_stop)
        self._configure.connect(self._do_create_bot)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._process_only)

        self._watcher = QFileSystemWatcher(self)
        self._watcher.fileChanged.connect(self._read_and_process)
        self._watcher.directoryChanged.connect(self._check_for_monitored)

        self.started.emit()

    def _do_stop(self):
        paths = self._watcher.directories() + self._watcher.files()
        if paths:
            self._watcher.removePaths(paths)
        self._timer.stop()

        if self._buffbot is not None:
            self._buffbot.close()

        self.finished.emit()

    def stop(self):
        self._stopping.emit()

    def _do_create_bot(self, filename, spells, acls):
        # If we have an existing buffbot that is listening to a different
        # file, then we need to stop watching that file, close out our
        # existing buffbot, and set it to None so that a new one can be
        # created later.
        if self._buffbot is not None:
            if (
                not os.path.samefile(filename, self._buffbot.filename)
                or self._buffbot.spells != spells
                or self._buffbot.acls != acls
            ):
                self._watcher.removePath(self._buffbot.filename)
                self._watcher.removePath(os.path.dirname(self._buffbot.filename))
                self._timer.stop()

                self._buffbot.close()
                self._buffbot = None

        # If we don't have a buffbot, either because we're just starting
        # or because the file has changed, then create a new one and
        # start watching the file and the directory containing that file.
        if self._buffbot is None:
            self._buffbot = BuffBot(
                filename=filename,
                spells=spells,
                acls=acls,
                logger=self._callback,
            )
            self.characterDetails.emit(self._buffbot.character)
            self._buffbot.load()
            self._watcher.addPath(filename)
            self._watcher.addPath(os.path.dirname(filename))
            self._timer.start(1000)

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

    def configure(self, filename, spells, acls):
        self._configure.emit(filename, spells, acls)

    def _process_only(self):
        self._buffbot.process()

    def _read_and_process(self, path):
        self._buffbot.read()
        self._buffbot.process()

    def _callback(self, line):
        self.logMessage.emit(datetime.datetime.now(), line)


class SpellModel(QAbstractListModel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.spells = []

    def data(self, index, role):
        if role == Qt.DisplayRole:
            spell, _ = self.spells[index.row()]
            return spell.name

    def rowCount(self, index):
        return len(self.spells)


class AddSpell(QDialog, Ui_AddSpell):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

    def _extract_spell(self):
        return Spell(
            name=self.spellName.text(),
            gem=self.spellGem.value(),
            success_message=self.spellSuccessMessage.text(),
        )

    @classmethod
    def getNewSpell(cls, parent):
        dlg = cls(parent)

        if dlg.exec_():
            return dlg._extract_spell()

        return None

    @classmethod
    def editSpell(cls, parent, spell):
        dlg = cls(parent)
        dlg.spellName.setText(spell.name)
        dlg.spellGem.setValue(spell.gem)
        dlg.spellSuccessMessage.setText(spell.success_message)

        if dlg.exec_():
            return dlg._extract_spell()

        return None


class AddAcl(QDialog, Ui_AddACL):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

    @classmethod
    def getName(cls, parent):
        dlg = cls(parent)

        if dlg.exec_():
            return dlg.characterName.text()

        return None


class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.setupUi(self)

        appdir = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation)
        config_db = os.path.join(appdir, "config.db")

        os.makedirs(os.path.dirname(config_db), exist_ok=True)

        self.db = QtSql.QSqlDatabase.addDatabase("QSQLITE")
        self.db.setDatabaseName(os.path.join(appdir, "config.db"))
        self.db.open()
        self.db.exec_(
            """ CREATE TABLE state (
                key text NOT NULL UNIQUE,
                value text NOT NULL
            )
            """
        )
        self.db.exec_(
            """ CREATE TABLE spells (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character text NOT NULL,
                    server text NOT NULL,
                    gem INTEGER NOT NULL,
                    name text NOT NULL,
                    success_message text NOT NULL
            )
            """
        )
        self.db.exec_(
            """ CREATE TABLE acls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character text NOT NULL,
                    server text NOT NULL,
                    entry text NOT NULL
            )
            """
        )

        self.filename = None
        self.char = None

        # Setup the spells models
        self.spells = QtSql.QSqlTableModel()
        self.spells.setTable("spells")
        self.spells.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.spellList.setModel(self.spells)
        self.spellList.setModelColumn(4)

        # Setup the ACL models
        self.acls = QtSql.QSqlTableModel()
        self.acls.setTable("acls")
        self.acls.setEditStrategy(QtSql.QSqlTableModel.OnFieldChange)
        self.aclList.setModel(self.acls)
        self.aclList.setModelColumn(3)

        # Setup our default UI values, we do this here instead of in QT Designer,
        # because QT Designer has default text that makes it easier to tell what
        # is happening when laying out the UI, but which isn't the best default
        # when first opening the application.
        self.setWindowTitle("BuffBot")
        self.character_name.setText("")
        self.character_server.setText("")
        self.logTable.setColumnWidth(0, 110)

        # Hookup our UI to the functions that will implement their functionality
        self.action_Open.triggered.connect(self.open_file)
        self.addSpellButton.clicked.connect(self.add_spell)
        self.editSpellButton.clicked.connect(self.edit_spell)
        self.deleteSpellButton.clicked.connect(self.delete_spell)
        self.addACLEntryButton.clicked.connect(self.add_acl)
        self.deleteACLEntryButton.clicked.connect(self.delete_acl)

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
        self.worker.started.connect(self.load_state)
        self.worker.characterDetails.connect(self.update_character)
        self.worker.monitoringFile.connect(self.update_statusbar)
        self.worker.logMessage.connect(self.update_logger)

        # Start our thread so it can start processing information.
        self.thread.start()

    def load_state(self):
        query = self.db.exec_("SELECT value FROM state WHERE key = 'last-filename'")
        if query.first():
            self.filename = query.value("value")
            self._update_worker()

    def _get_spells(self):
        spells = []
        for i in range(self.spells.rowCount()):
            record = self.spells.record(i)
            spells.append(
                Spell(
                    name=record.value("name"),
                    gem=record.value("gem"),
                    success_message=record.value("success_message"),
                )
            )

        return spells

    def _get_acls(self):
        acls = []
        for i in range(self.acls.rowCount()):
            record = self.acls.record(i)
            acls.append(record.value("entry"))

        return acls

    def _update_worker(self):
        filename = self.filename
        if filename is not None:
            spells = self._get_spells()
            acls = self._get_acls()

            self.worker.configure(filename, spells, acls)

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
            self.db.close()
            self.worker.stop()
            e.ignore()
        else:
            e.accept()

    def enable_ui(self):
        # Allow our add/edit/delete buttons to be used.
        self.addSpellButton.setEnabled(True)
        self.editSpellButton.setEnabled(True)
        self.deleteSpellButton.setEnabled(True)

        self.addACLEntryButton.setEnabled(True)
        self.deleteACLEntryButton.setEnabled(True)

    def open_file(self):
        directory = (
            os.path.dirname(self.filename)
            if self.filename is not None
            else os.fspath(pathlib.Path.home())
        )
        filename, _ = QFileDialog.getOpenFileName(
            self, "Open Log File", directory, "Log Files (*.txt)"
        )

        if filename:
            self.filename = filename
            self.db.exec_(
                f""" INSERT INTO state (key, value)
                        VALUES ('last-filename', '{self.filename}')
                        ON CONFLICT (key) DO UPDATE set value = '{self.filename}'
                """
            )
            self._update_worker()

    def update_character(self, char):
        self.char = char
        self.setWindowTitle(f"BuffBot - {char.name} ({char.server_display})")
        self.character_name.setText(char.name)
        self.character_server.setText(char.server_display)

        # Filter our spell list by the character and server that was selected, and
        # the select our spells.
        self.spells.setFilter(
            f"character = '{self.char.name}' AND server = '{self.char.server.value}'"
        )
        self.spells.select()

        self.acls.setFilter(
            f"character = '{self.char.name}' AND server = '{self.char.server.value}'"
        )
        self.acls.select()
        self._update_worker()

        self.enable_ui()

    def update_statusbar(self, filename):
        self.statusbar.showMessage(f"Monitoring {filename}")

    def update_logger(self, date, line):
        self.logTable.insertRow(0)
        self.logTable.setItem(
            0, 0, QTableWidgetItem(date.strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.logTable.setItem(0, 1, QTableWidgetItem(line))

        # We only want to keep the 500 latest entries, because we don't want our memory
        # to grow unbounded.
        for i in range(max(0, self.logTable.rowCount() - 500)):
            self.logTable.removeRow(i + 500)

    def add_spell(self):
        spell = AddSpell.getNewSpell(self)

        if spell is not None:
            record = self.spells.record()
            record.setValue("character", self.char.name)
            record.setValue("server", self.char.server.value)
            record.setValue("name", spell.name)
            record.setValue("gem", spell.gem)
            record.setValue("success_message", spell.success_message)

            self.spells.insertRecord(self.spells.rowCount(), record)
            self.spells.select()
            self._update_worker()

    def edit_spell(self):
        if self.spellList.currentIndex().row() >= 0:
            record = self.spells.record(self.spellList.currentIndex().row())
            spell = AddSpell.editSpell(
                self,
                Spell(
                    name=record.value("name"),
                    gem=record.value("gem"),
                    success_message=record.value("success_message"),
                ),
            )
            if spell is not None:
                record.setValue("name", spell.name)
                record.setValue("gem", spell.gem)
                record.setValue("success_message", spell.success_message)
                self.spells.setRecord(self.spellList.currentIndex().row(), record)
                self._update_worker()
        else:
            QMessageBox.question(
                self, "Error", "Please select a spell to edit.", QMessageBox.Ok
            )

    def delete_spell(self):
        if self.spellList.currentIndex().row() >= 0:
            self.spells.removeRow(self.spellList.currentIndex().row())
            self.spells.select()
            self._update_worker()
        else:
            QMessageBox.question(
                self, "Error", "Please select a spell to delete.", QMessageBox.Ok
            )

    def add_acl(self):
        name = AddAcl.getName(self)

        if name is not None:
            record = self.acls.record()
            record.setValue("character", self.char.name)
            record.setValue("server", self.char.server.value)
            record.setValue("entry", name)

            self.acls.insertRecord(self.acls.rowCount(), record)
            self.acls.select()
            self._update_worker()

    def delete_acl(self):
        if self.aclList.currentIndex().row() >= 0:
            print(self.acls.removeRow(self.aclList.currentIndex().row()))
            self.acls.select()
            self._update_worker()
        else:
            QMessageBox.question(
                self, "Error", "Please select a character to delete.", QMessageBox.Ok
            )
