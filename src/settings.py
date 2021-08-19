from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget, QDesktopWidget

from youtube_settings import Ui_YouTubeSettings
from url_dialog import Ui_UrlDialog


class YouTubeSettings(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_YouTubeSettings()
        self.ui.setupUi(self)
        self.setWindowTitle("YouTube-Dl GUI | Settings")

        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())


class UrlDialog(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.ui = Ui_UrlDialog()
        self.ui.setupUi(self)
        self.setWindowTitle("YouTube-Dl GUI | Enter Url")

        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        qtRectangle = self.frameGeometry()
        centerPoint = QDesktopWidget().availableGeometry().center()
        qtRectangle.moveCenter(centerPoint)
        self.move(qtRectangle.topLeft())
