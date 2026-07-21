# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'maya_rename_uigJHURv.ui'
##
## Created by: Qt User Interface Compiler version 5.15.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

'''from PySide2.QtCore import (QCoreApplication, QDate, QDateTime, QMetaObject,
    QObject, QPoint, QRect, QSize, QTime, QUrl, Qt)
from PySide2.QtGui import (QBrush, QColor, QConicalGradient, QCursor, QFont,
    QFontDatabase, QIcon, QKeySequence, QLinearGradient, QPalette, QPainter,
    QPixmap, QRadialGradient)
from PySide2.QtWidgets import *'''
from PySide2 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName(u"Form")
        Form.resize(175, 59)
        self.renameButton = QtWidgets.QPushButton(Form)
        self.renameButton.setObjectName('renameButton')
        self.renameButton.setGeometry(QtCore.QRect(10, 10, 151, 41))

        self.retranslateUi(Form)

        QtCore.QMetaObject.connectSlotsByName(Form)
    # setupUi

    def retranslateUi(self, Form):
        Form.setWindowTitle(QtWidgets.QApplication.translate('Form', 'Auto Rename', None, -1))
        self.renameButton.setText(QtWidgets.QApplication.translate('Form', 'Bake Rename', None, -1))
        return
    # retranslateUi

