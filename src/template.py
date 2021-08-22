from PyQt5 import QtGui, QtCore


def set_style_for_pause_play_button(self, pause=False):
    if pause:
        self.ui.pause_button.setText("")
        icon9 = QtGui.QIcon()
        icon9.addPixmap(QtGui.QPixmap(":/myresource/resource/pause_new.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.ui.pause_button.setIcon(icon9)
        self.ui.pause_button.setIconSize(QtCore.QSize(25, 25))

    else:
        self.ui.pause_button.setText("")
        icon10 = QtGui.QIcon()
        icon10.addPixmap(QtGui.QPixmap(":/myresource/resource/play.png"), QtGui.QIcon.Normal,
                         QtGui.QIcon.Off)
        self.ui.pause_button.setIcon(icon10)
        self.ui.pause_button.setIconSize(QtCore.QSize(25, 25))
