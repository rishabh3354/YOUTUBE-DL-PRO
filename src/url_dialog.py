# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'url_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.0
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_UrlDialog(object):
    def setupUi(self, UrlDialog):
        UrlDialog.setObjectName("UrlDialog")
        UrlDialog.resize(498, 339)
        self.verticalLayout = QtWidgets.QVBoxLayout(UrlDialog)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label = QtWidgets.QLabel(UrlDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setObjectName("label")
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout_3 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.yt_video_link = QtWidgets.QLineEdit(UrlDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.yt_video_link.sizePolicy().hasHeightForWidth())
        self.yt_video_link.setSizePolicy(sizePolicy)
        font = QtGui.QFont()
        font.setPointSize(11)
        self.yt_video_link.setFont(font)
        self.yt_video_link.setFocusPolicy(QtCore.Qt.ClickFocus)
        self.yt_video_link.setAutoFillBackground(False)
        self.yt_video_link.setStyleSheet("QLineEdit{\n"
"\n"
"height: 30px;\n"
"border-radius:12px;\n"
"}")
        self.yt_video_link.setText("")
        self.yt_video_link.setAlignment(QtCore.Qt.AlignCenter)
        self.yt_video_link.setDragEnabled(False)
        self.yt_video_link.setPlaceholderText("Youtube Video/Playlist URL")
        self.yt_video_link.setObjectName("yt_video_link")
        self.horizontalLayout_3.addWidget(self.yt_video_link)
        self.paste_button = QtWidgets.QPushButton(UrlDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.paste_button.sizePolicy().hasHeightForWidth())
        self.paste_button.setSizePolicy(sizePolicy)
        self.paste_button.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.paste_button.setStyleSheet("QPushButton{\n"
"\n"
"border-radius:10px;\n"
"}")
        self.paste_button.setText("")
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(":/myresource/resource/icons8-clipboard-96.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.paste_button.setIcon(icon)
        self.paste_button.setIconSize(QtCore.QSize(25, 25))
        self.paste_button.setObjectName("paste_button")
        self.horizontalLayout_3.addWidget(self.paste_button)
        self.verticalLayout.addLayout(self.horizontalLayout_3)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem)
        self.horizontalLayout_21 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_21.setObjectName("horizontalLayout_21")
        self.video_vs = QtWidgets.QRadioButton(UrlDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.video_vs.sizePolicy().hasHeightForWidth())
        self.video_vs.setSizePolicy(sizePolicy)
        self.video_vs.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.video_vs.setStyleSheet("QRadioButton::indicator { width: 20px;height:20px };")
        self.video_vs.setChecked(True)
        self.video_vs.setObjectName("video_vs")
        self.horizontalLayout_21.addWidget(self.video_vs)
        self.playlist_vs = QtWidgets.QRadioButton(UrlDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.playlist_vs.sizePolicy().hasHeightForWidth())
        self.playlist_vs.setSizePolicy(sizePolicy)
        self.playlist_vs.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.playlist_vs.setStyleSheet("QRadioButton::indicator { width: 20px;height:20px };")
        self.playlist_vs.setObjectName("playlist_vs")
        self.horizontalLayout_21.addWidget(self.playlist_vs)
        self.verticalLayout.addLayout(self.horizontalLayout_21)
        spacerItem1 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem1)
        self.process = QtWidgets.QPushButton(UrlDialog)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.process.sizePolicy().hasHeightForWidth())
        self.process.setSizePolicy(sizePolicy)
        self.process.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap(":/myresource/resource/search_white.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.process.setIcon(icon1)
        self.process.setIconSize(QtCore.QSize(25, 25))
        self.process.setObjectName("process")
        self.verticalLayout.addWidget(self.process)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.verticalLayout.addItem(spacerItem2)

        self.retranslateUi(UrlDialog)
        QtCore.QMetaObject.connectSlotsByName(UrlDialog)

    def retranslateUi(self, UrlDialog):
        _translate = QtCore.QCoreApplication.translate
        UrlDialog.setWindowTitle(_translate("UrlDialog", "Form"))
        self.label.setText(_translate("UrlDialog", "<html><head/><body><p align=\"center\"><img src=\":/myresource/resource/icons8-youtube-play-button-500.png\" width=\"100\"/></p><p align=\"center\"><span style=\" font-size:14pt; font-weight:600; color:#eeeeec;\">YOUTUBE-DL PRO</span></p></body></html>"))
        self.paste_button.setToolTip(_translate("UrlDialog", "Clear and Paste"))
        self.video_vs.setText(_translate("UrlDialog", "VIDEO"))
        self.playlist_vs.setText(_translate("UrlDialog", "PLAYLIST"))
        self.process.setText(_translate("UrlDialog", "Process"))
import resource_rc
