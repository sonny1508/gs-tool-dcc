# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'MatManagerKJNnqU.ui'
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
        Dialog.resize(696, 691)
        self.formLayout = QFormLayout(Dialog)
        self.formLayout.setObjectName(u"formLayout")
        self.formLayout.setHorizontalSpacing(6)
        self.filterLineEdit = QLineEdit(Dialog)
        self.filterLineEdit.setObjectName(u"filterLineEdit")
        self.filterLineEdit.setEnabled(True)
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filterLineEdit.sizePolicy().hasHeightForWidth())
        
        self.menuBar = QMenuBar()
        self.editMenu = QMenu('Edit')
        self.helpMenu = QMenu('Help')
        # self.menuBar.addMenu(self.editMenu)
        # self.menuBar.addMenu(self.helpMenu)
        
        self.formLayout.setMenuBar(self.menuBar)
        
        self.filterLineEdit.setSizePolicy(sizePolicy)
        self.filterLineEdit.setMinimumSize(QSize(0, 0))
        self.filterLineEdit.setMaximumSize(QSize(16777215, 16777215))
        self.filterLineEdit.setMouseTracking(False)
        
        self.formLayout.setWidget(0, QFormLayout.SpanningRole, self.filterLineEdit)

        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setSpacing(6)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox = QGroupBox(Dialog)
        self.groupBox.setObjectName(u"groupBox")
        self.groupBox.setMinimumSize(QSize(0, 150))
        font = QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.Weight(75)
        self.groupBox.setFont(font)
        self.radioMaterial = QRadioButton(self.groupBox)
        self.radioMaterial.setObjectName(u"radioMaterial")
        self.radioMaterial.setGeometry(QRect(10, 30, 161, 17))
        self.radioMaterial.setChecked(True)
        self.radioSmartMaterial = QRadioButton(self.groupBox)
        self.radioSmartMaterial.setObjectName(u"radioSmartMaterial")
        self.radioSmartMaterial.setGeometry(QRect(10, 60, 161, 17))
        self.radioAlpha = QRadioButton(self.groupBox)
        self.radioAlpha.setObjectName(u"radioAlpha")
        self.radioAlpha.setGeometry(QRect(10, 90, 161, 17))
        self.radioBrush = QRadioButton(self.groupBox)
        self.radioBrush.setObjectName(u"radioBrush")
        self.radioBrush.setGeometry(QRect(10, 120, 161, 17))

        self.verticalLayout.addWidget(self.groupBox)

        self.line = QFrame(Dialog)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.treeView = QTreeView(Dialog)
        self.treeView.setObjectName(u"treeView")
        self.treeView.setEnabled(True)
        self.treeView.setMaximumSize(QSize(180, 16777215))
        self.treeView.setWordWrap(True)
        self.treeView.setHeaderHidden(True)
        self.treeView.setRootIsDecorated(False)  # This removes the expand/collapse indicators
        self.treeView.setIndentation(0)  # Remove indentation
        self.treeView.setItemsExpandable(False)  # Disable expansion
        self.treeView.setExpandsOnDoubleClick(False)
        self.treeView.header().setMinimumSectionSize(50)
        self.treeView.header().setStretchLastSection(False)

        self.verticalLayout.addWidget(self.treeView)


        self.formLayout.setLayout(1, QFormLayout.LabelRole, self.verticalLayout)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.listWidget = QListWidget(Dialog)
        self.listWidget.setObjectName(u"listWidget")
        self.listWidget.setAutoFillBackground(True)
        self.listWidget.setIconSize(QSize(128, 128))
        self.listWidget.setMovement(QListView.Static)
        self.listWidget.setResizeMode(QListView.Adjust)
        self.listWidget.setViewMode(QListView.IconMode)
        self.listWidget.setUniformItemSizes(True)
        self.listWidget.setWordWrap(True)
        self.listWidget.setSortingEnabled(True)

        self.horizontalLayout.addWidget(self.listWidget)


        self.formLayout.setLayout(1, QFormLayout.FieldRole, self.horizontalLayout)


        self.retranslateUi(Dialog)

        QMetaObject.connectSlotsByName(Dialog)
    # setupUi

    def retranslateUi(self, Dialog):
        Dialog.setWindowTitle(QCoreApplication.translate("Dialog", u"Material Manager", None))
#if QT_CONFIG(tooltip)
        self.filterLineEdit.setToolTip("")
#endif // QT_CONFIG(tooltip)
#if QT_CONFIG(whatsthis)
        self.filterLineEdit.setWhatsThis("")
#endif // QT_CONFIG(whatsthis)
        self.filterLineEdit.setText("")
        self.filterLineEdit.setPlaceholderText(QCoreApplication.translate("Dialog", u"Filter By Name...", None))
        self.groupBox.setTitle(QCoreApplication.translate("Dialog", u"Asset Type:", None))
        self.radioMaterial.setText(QCoreApplication.translate("Dialog", u"Materials", None))
        self.radioSmartMaterial.setText(QCoreApplication.translate("Dialog", u"Smart Materials", None))
        self.radioAlpha.setText(QCoreApplication.translate("Dialog", u"Alpha", None))
        self.radioBrush.setText(QCoreApplication.translate("Dialog", u"Brush", None))
    # retranslateUi

