from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_Rename_list_Form(object):
    def setupUi(self, Rename_list_Form):
        if not Rename_list_Form.objectName():
            Rename_list_Form.setObjectName("Rename_list_Form")
        Rename_list_Form.resize(201, 256)
        Rename_list_Form.setMaximumSize(QSize(201, 256))
        self.listView = QListView(Rename_list_Form)
        self.listView.setObjectName("listView")
        self.listView.setGeometry(QRect(10, 40, 181, 171))
        self.pushButton_rename_list = QPushButton(Rename_list_Form)
        self.pushButton_rename_list.setObjectName("pushButton_rename_list")
        self.pushButton_rename_list.setGeometry(QRect(10, 220, 181, 31))
        self.label = QLabel(Rename_list_Form)
        self.label.setObjectName("label")
        self.label.setGeometry(QRect(10, 10, 181, 20))

        self.retranslateUi(Rename_list_Form)

        QMetaObject.connectSlotsByName(Rename_list_Form)
    # setupUi

    def retranslateUi(self, Rename_list_Form):
        Rename_list_Form.setWindowTitle(QCoreApplication.translate("Rename_list_Form", "Rename", None))
        self.pushButton_rename_list.setText(QCoreApplication.translate("Rename_list_Form", "Rename", None))
        self.label.setText(QCoreApplication.translate("Rename_list_Form", "Namespace is not support to transfer.", None))
    # retranslateUi

