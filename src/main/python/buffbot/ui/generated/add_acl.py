# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'gui/AddACLEntry.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_AddACL(object):
    def setupUi(self, AddACL):
        AddACL.setObjectName("AddACL")
        AddACL.resize(400, 91)
        self.widget = QtWidgets.QWidget(AddACL)
        self.widget.setGeometry(QtCore.QRect(0, 10, 391, 72))
        self.widget.setObjectName("widget")
        self.gridLayout_2 = QtWidgets.QGridLayout(self.widget)
        self.gridLayout_2.setContentsMargins(0, 0, 0, 0)
        self.gridLayout_2.setObjectName("gridLayout_2")
        self.gridLayout = QtWidgets.QGridLayout()
        self.gridLayout.setObjectName("gridLayout")
        self.label = QtWidgets.QLabel(self.widget)
        self.label.setObjectName("label")
        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)
        self.characterName = QtWidgets.QLineEdit(self.widget)
        self.characterName.setObjectName("characterName")
        self.gridLayout.addWidget(self.characterName, 0, 1, 1, 1)
        self.gridLayout_2.addLayout(self.gridLayout, 0, 0, 1, 1)
        self.buttonBox = QtWidgets.QDialogButtonBox(self.widget)
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName("buttonBox")
        self.gridLayout_2.addWidget(self.buttonBox, 1, 0, 1, 1)

        self.retranslateUi(AddACL)
        self.buttonBox.accepted.connect(AddACL.accept)
        self.buttonBox.rejected.connect(AddACL.reject)
        QtCore.QMetaObject.connectSlotsByName(AddACL)

    def retranslateUi(self, AddACL):
        _translate = QtCore.QCoreApplication.translate
        AddACL.setWindowTitle(_translate("AddACL", "Dialog"))
        self.label.setText(_translate("AddACL", "Character"))
