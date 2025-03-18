# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MatManagerIjYHMF.ui'
##
## Created by: Qt User Interface Compiler version 5.15.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        if not Dialog.objectName():
            Dialog.setObjectName(u"Dialog")
        Dialog.resize(714, 347)
        self.b_export = QPushButton(Dialog)
        self.b_export.setObjectName(u"b_export")
        self.b_export.setGeometry(QRect(590, 300, 111, 31))

        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"MGP Exporter", None))
        self.b_export.setText(QCoreApplication.translate("Dialog", u"Export", None))
    # retranslateUi

