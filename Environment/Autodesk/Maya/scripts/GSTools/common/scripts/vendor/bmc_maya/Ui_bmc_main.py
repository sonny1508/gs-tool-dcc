from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(300, 150)
        MainWindow.setMinimumSize(QSize(300, 150))
        MainWindow.setMaximumSize(QSize(300, 150))
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.label_file_path = QLabel(self.centralwidget)
        self.label_file_path.setObjectName("label_file_path")
        self.label_file_path.setGeometry(QRect(20, 10, 211, 21))
        self.label_file_path.setStyleSheet("background-color: rgb(130, 130, 130);")
        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName("label_4")
        self.label_4.setGeometry(QRect(20, 50, 41, 21))
        self.label_4.setAlignment(Qt.AlignCenter)
        self.pushButton_open_file_dialog = QPushButton(self.centralwidget)
        self.pushButton_open_file_dialog.setObjectName("pushButton_open_file_dialog")
        self.pushButton_open_file_dialog.setGeometry(QRect(240, 10, 51, 21))
        self.pushButton_open_file_dialog.setStyleSheet("background-color: rgb(130, 130, 130);\n"
        

"color: rgb(0, 17, 255);")
        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName("groupBox")
        self.groupBox.setGeometry(QRect(10, 0, 281, 111))
        self.pushButton_SEND = QPushButton(self.groupBox)
        self.pushButton_SEND.setObjectName("pushButton_SEND")
        self.pushButton_SEND.setGeometry(QRect(8, 45, 275, 51))
        self.pushButton_SEND.setStyleSheet("font: 10pt \"MS Shell Dlg 2\";\n"
"color: rgb(255, 0, 0);")
        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName("groupBox_2")
        self.groupBox_2.setGeometry(QRect(10, 0, 281, 111))
        self.groupBox_2.setMaximumSize(QSize(221, 300))
        MainWindow.setCentralWidget(self.centralwidget)
        self.groupBox_2.raise_()
        self.groupBox.raise_()
        self.label_file_path.raise_()
        self.label_4.raise_()
        self.pushButton_open_file_dialog.raise_()
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName("menubar")
        self.menubar.setGeometry(QRect(0, 0, 240, 21))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.retranslateUi(MainWindow)
        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", "Maya to Blender", None))
        self.label_file_path.setText("")
        #self.label_4.setText(QCoreApplication.translate("MainWindow", "User:", None))
        #self.pushButton_save_setting.setText(QCoreApplication.translate("MainWindow", "Save Setting", None))
        self.pushButton_open_file_dialog.setText("")
        #self.groupBox.setTitle(QCoreApplication.translate("MainWindow", "Action", None))
        self.pushButton_SEND.setText(QCoreApplication.translate("MainWindow", "SEND", None))
        #self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", "Setting", None))
     
    # retranslateUi

