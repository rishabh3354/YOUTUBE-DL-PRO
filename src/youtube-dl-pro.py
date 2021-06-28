import json
import os
import shutil
import sys
import webbrowser
from copy import deepcopy
from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import QUrl, QSettings
from PyQt5.QtGui import QDesktopServices, QIcon, QPixmap, QFont
from PyQt5.QtWidgets import QMainWindow, QApplication, QMessageBox, QFileDialog, QStyle, QCheckBox, QLineEdit
from account_threads import SaveLocalInToken, RefreshButtonThread
from accounts import get_user_data_from_local, days_left, ApplicationStartupTask, check_for_local_token
from helper import process_html_data, check_internet_connection, check_default_location, process_html_data_playlist, \
    get_thumbnail_path_from_local, safe_string, get_local_download_data, save_after_delete
from youtube_script import get_initial_download_dir
from template import set_style_for_pause_play_button, selected_download_button_css
from ui_main_trial import Ui_MainWindow
from youtube_threads import ProcessYtV, DownloadVideo, NetSpeedThread, ProcessYtVPlayList, GetPlaylistVideos, \
    DownloadVideoPlayList, FileSizeThread, FileSizeThreadSingleVideo
from helper import FREQUENCY_MAPPER

PRODUCT_NAME = "YOUTUBE_DL"
THEME_PATH = '/snap/youtube-dl-pro/current/'


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.setStyleSheet(open(THEME_PATH + 'dark.qss', 'r').read())
        self.settings = QSettings("warlordsoft", "youtube-dl-pro")
        self.is_plan_active = True
        self.delete_source_file = True
        self.one_time_congratulate = True

        #  init net speed settings
        self.net_frequency = 1.0
        self.speed_unit = "MB/s | KB/s | B/s"
        self.default_frequency()

        self.Default_loc = get_initial_download_dir()
        self.Default_loc_playlist = get_initial_download_dir()
        self.ui.download_path_edit_2.setText(self.Default_loc + "/YOUTUBE_DL")
        self.ui.download_path_edit_playlist.setText(self.Default_loc_playlist + "/YOUTUBE_DL")

        # download tab default item to show
        self.show_default_type = self.Default_loc
        self.speed = "0.0"
        self.unit = "B/s"

        self.load_settings()
        self.show()

        # Video functionality ==================================================
        # init
        self.is_hd_plus = False
        self.stop = False
        self.hide_show_play_pause_button(hide=True)
        self.pause = False
        # self.home_page()
        self.counter = 0

        # signal and slots =====

        # pause delete
        self.ui.pause_button.clicked.connect(self.pause_button_pressed)
        self.ui.delete_button.clicked.connect(self.trigger_delete_action)
        # miscellaneous
        self.ui.yt_video_link.textChanged.connect(self.decide_video_or_playlist)
        self.ui.paste_button.clicked.connect(self.paste_button_clicked)
        self.ui.download_button_2.clicked.connect(self.download_action)
        self.ui.hd_radio_button_2.clicked.connect(self.enable_hd_button_message)
        self.ui.download_path_button_2.clicked.connect(self.open_download_path)
        self.ui.select_format_obj_2.currentTextChanged.connect(self.check_for_audio_only)
        self.ui.select_quality_obj_2.currentIndexChanged.connect(self.show_file_size)
        self.ui.select_format_obj_2.currentIndexChanged.connect(self.show_file_size)
        self.ui.select_fps_obj_2.currentIndexChanged.connect(self.show_file_size)

        # tab widget index change
        self.ui.tabWidget.currentChanged.connect(self.tab_widget_changed)

        # playlist functionality ======================================================

        # init
        self.is_hd_plus_playlist = False
        self.play_list_counter = 1
        self.total_obj = list()

        # signal and slots
        self.ui.select_videos_playlist_2.currentIndexChanged.connect(self.show_video_thumbnail)
        self.ui.download_button_playlist_2.clicked.connect(self.download_action_playlist)
        self.ui.select_type_playlist_2.currentIndexChanged.connect(self.check_for_audio_only_playlist)
        self.ui.select_quality_playlist_2.currentIndexChanged.connect(self.check_for_audio_only_playlist)
        self.ui.hd_radio_button_playlist_2.clicked.connect(self.enable_hd_button_playlist)
        self.ui.download_path_button_playlist.clicked.connect(self.open_download_path_playlist)

        # Downloads functionality ======================================================

        # init
        self.all_videos = True
        self.all_playlist = False

        # signal and slots
        self.ui.open_videos.clicked.connect(self.show_downloads_folder)
        self.ui.play_video.clicked.connect(self.play_videos_from_downloads)
        self.ui.details_video.clicked.connect(self.details_video_from_downloads)
        self.ui.delete_videos.clicked.connect(self.delete_video_from_downloads)
        self.ui.listWidget.itemDoubleClicked.connect(self.play_videos_from_downloads)
        self.ui.search_videos.textChanged.connect(self.search_videos)
        self.ui.search_videos.cursorPositionChanged.connect(self.clear_search_bar_on_edit)
        self.ui.all_videos.clicked.connect(self.set_all_videos)
        self.ui.all_playlist.clicked.connect(self.set_all_playlist)
        self.ui.clear_history.clicked.connect(self.clear_all_history)

        # Accounts/About functionality ======================================================

        # init
        ApplicationStartupTask(PRODUCT_NAME).create_free_trial_offline()
        self.ui.error_message.clear()
        self.ui.error_message.setStyleSheet("color:red;")
        self.ui.account_progress_bar.setVisible(False)
        self.my_plan()

        # signal and slots
        self.ui.warlordsoft_button.clicked.connect(self.redirect_to_warlordsoft)
        self.ui.donate_button.clicked.connect(self.redirect_to_paypal_donation)
        self.ui.rate_button.clicked.connect(self.redirect_to_rate_snapstore)
        self.ui.feedback_button.clicked.connect(self.redirect_to_feedback_button)
        self.ui.purchase_licence_2.clicked.connect(self.purchase_licence_2)
        self.ui.refresh_account_2.clicked.connect(self.refresh_account_2)
        self.ui.ge_more_apps.clicked.connect(self.ge_more_apps)

        # Select theme ========================================================================
        self.set_icon_on_line_edit()

        # net speed settings
        self.ui.horizontalSlider_2.valueChanged.connect(self.change_frequency_net)
        self.ui.comboBox_3.currentIndexChanged.connect(self.change_net_speed_unit)

        self.ui.progress_bar.setFixedHeight(20)
        self.ui.account_progress_bar.setFixedHeight(5)
        self.ui.progress_bar.setFont(QFont('Ubuntu', 11))
        self.ui.progress_bar.setVisible(False)
        self.ui.tabWidget.setCurrentIndex(0)

    def tab_widget_changed(self, index):
        if index == 3:
            self.get_user_download_data()
        if index == 4:
            try:
                net_speed_thread = self.net_speed_thread.isRunning()
            except Exception as e:
                net_speed_thread = False
                pass
            if not net_speed_thread:
                self.start_net_speed_thread()

    def set_icon_on_line_edit(self):
        self.ui.yt_video_link.addAction(QIcon(":/myresource/resource/link_1.png"), QLineEdit.LeadingPosition)
        self.ui.search_videos.addAction(QIcon(":/myresource/resource/search_white.png"), QLineEdit.LeadingPosition)
        self.ui.yt_video_link.setTextMargins(5, 0, 0, 0)
        self.ui.search_videos.setTextMargins(5, 0, 0, 0)

    def decide_video_or_playlist(self):
        if self.ui.video_vs.isChecked():
            self.ytv_link_clicked()
        else:
            self.ytv_link_clicked_playlist()

    def default_frequency(self):
        self.ui.horizontalSlider_2.setValue(4)
        self.ui.label_16.setText("1.0 Sec")

    def change_net_speed_unit(self):
        self.speed_unit = self.ui.comboBox_3.currentText()
        try:
            self.net_speed_thread.terminate()
            self.start_net_speed_thread()
        except Exception as e:
            pass

    def change_frequency_net(self):
        self.net_frequency = FREQUENCY_MAPPER.get(self.ui.horizontalSlider_2.value(), 4)
        self.ui.label_16.setText(str(self.net_frequency) + " Sec")
        try:
            self.net_speed_thread.terminate()
            self.start_net_speed_thread()
        except Exception as e:
            pass

    def start_net_speed_thread(self):
        self.net_speed_thread = NetSpeedThread(self.net_frequency, self.speed_unit)
        self.net_speed_thread.change_value.connect(self.setProgress_net_speed)
        self.net_speed_thread.start()

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        self.settings.setValue("hd_radio_button", self.ui.hd_radio_button_2.isChecked())
        self.settings.setValue("hd_radio_button_playlist", self.ui.hd_radio_button_playlist_2.isChecked())
        self.settings.setValue("delete_source_file_check", self.delete_source_file)
        self.settings.setValue("default_loc", self.Default_loc)
        self.settings.setValue("default_loc_playlist", self.Default_loc_playlist)
        self.settings.setValue("net_speed_unit", self.ui.comboBox_3.currentText())
        self.settings.setValue("net_frequency", self.ui.horizontalSlider_2.value())
        #  one time congratulate
        self.settings.setValue("one_time_congratulate", self.one_time_congratulate)
        # save window state
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())

    def load_settings(self):
        if self.settings.contains("hd_radio_button"):
            self.ui.hd_radio_button_2.setChecked(json.loads(self.settings.value("hd_radio_button").lower()))
        if self.settings.contains("hd_radio_button_playlist"):
            self.ui.hd_radio_button_playlist_2.setChecked(
                json.loads(self.settings.value("hd_radio_button_playlist").lower()))
        if self.settings.contains("delete_source_file_check"):
            self.delete_source_file = json.loads(self.settings.value("delete_source_file_check").lower())
        if self.settings.contains("default_loc"):
            self.Default_loc = self.settings.value("default_loc")
            self.ui.download_path_edit_2.setText(self.Default_loc + "/YOUTUBE_DL")
        if self.settings.contains("default_loc_playlist"):
            self.Default_loc_playlist = self.settings.value("default_loc_playlist")
            self.ui.download_path_edit_playlist.setText(self.Default_loc_playlist + "/YOUTUBE_DL")

        if self.settings.contains("net_speed_unit"):
            self.speed_unit = self.settings.value("net_speed_unit")
            self.ui.comboBox_3.setCurrentText(self.speed_unit)
        if self.settings.contains("net_frequency"):
            self.net_frequency = FREQUENCY_MAPPER.get(int(self.settings.value("net_frequency")), 4)
            self.ui.horizontalSlider_2.setValue(int(self.settings.value("net_frequency")))
            self.ui.label_16.setText(
                str(FREQUENCY_MAPPER.get(int(self.settings.value("net_frequency")), "1.0")) + " Sec")

        #  one time congratulate
        if self.settings.contains("one_time_congratulate"):
            self.one_time_congratulate = json.loads(self.settings.value("one_time_congratulate"))

        # load window state
        if self.settings.contains("geometry"):
            self.restoreGeometry(self.settings.value("geometry"))
        if self.settings.contains("windowState"):
            self.restoreState(self.settings.value("windowState", ""))

    def show_file_size(self):
        try:
            file_size_single_video_thread_status = self.file_size_single_video_thread.isRunning()
        except Exception as e:
            file_size_single_video_thread_status = False
        if not file_size_single_video_thread_status:
            if self.ui.select_quality_obj_2.currentText() not in ["", None, 'Select Quality']:
                self.file_size_single_video_thread = FileSizeThreadSingleVideo(self)
                self.file_size_single_video_thread.get_size_of_single_video_file.connect(
                    self.set_file_size_single_video)
                self.file_size_single_video_thread.start()

    def set_file_size_single_video(self, size):
        if size:
            self.ui.video_size_5.setText(f"Size: {size}")

    def file_download_success_dialog(self, title, folder_path, play_path):
        self.msg = QMessageBox()
        self.msg.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.msg.setStyleSheet("background-color:rgba(0, 57, 96, 1);color:white;")
        self.msg.setIcon(QMessageBox.Information)
        self.msg.setText(title)
        self.msg.setInformativeText("")
        close = self.msg.addButton(QMessageBox.Yes)
        show_in_downloads = self.msg.addButton(QMessageBox.Yes)
        play = self.msg.addButton(QMessageBox.Yes)
        open_folder = self.msg.addButton(QMessageBox.Yes)
        open_folder.setText('Open Folder')
        show_in_downloads.setText('Show Downloads')
        play.setText('Play')
        close.setText('Close')
        play.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_MediaPlay)))
        close.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_BrowserStop)))
        open_folder.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_DirIcon)))
        show_in_downloads.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_DirOpenIcon)))
        self.msg.exec_()
        try:
            if self.msg.clickedButton() == open_folder:
                QDesktopServices.openUrl(QUrl(folder_path))
            elif self.msg.clickedButton() == play:
                QDesktopServices.openUrl(QUrl(play_path))
            elif self.msg.clickedButton() == show_in_downloads:
                self.show_downloads_page()
            elif self.msg.clickedButton() == close:
                pass
        except Exception as e:
            pass

    def account_page(self):
        self.ui.tabWidget.setCurrentIndex(5)

    def show_downloads_page(self):
        self.ui.tabWidget.setCurrentIndex(3)
        self.get_user_download_data()

    def pause_button_pressed(self):
        try:
            video_thread_running = self.process_ytv_thread.isRunning()
        except Exception as e:
            video_thread_running = False
        try:
            playlist_thread_running = self.process_ytv_play_list_thread.isRunning()
        except Exception as e:
            playlist_thread_running = False

        if video_thread_running:
            if self.pause:
                self.process_ytv_thread.resume()
                set_style_for_pause_play_button(self, pause=True)
                self.pause = False
            else:
                self.process_ytv_thread.pause()
                set_style_for_pause_play_button(self, pause=False)
                self.pause = True
        elif playlist_thread_running:
            if self.pause:
                self.process_ytv_play_list_thread.resume()
                set_style_for_pause_play_button(self, pause=True)
                self.pause = False
            else:
                self.process_ytv_play_list_thread.pause()
                set_style_for_pause_play_button(self, pause=False)
                self.pause = True

    def trigger_delete_action(self):
        try:
            self.msg = QMessageBox()
            self.msg.setWindowFlag(QtCore.Qt.FramelessWindowHint)
            self.msg.setStyleSheet("background-color:rgba(0, 57, 96, 1);color:white;")
            self.msg.setIcon(QMessageBox.Information)
            self.msg.setText("Are you sure want to stop on-going task?")
            yes_button = self.msg.addButton(QMessageBox.Yes)
            no_button = self.msg.addButton(QMessageBox.No)
            self.msg.exec_()
            if self.msg.clickedButton() == yes_button:
                self.delete_button_pressed()
            if self.msg.clickedButton() == no_button:
                pass
        except Exception as e:
            self.popup_message(title="Error while deleting the task!", message="", error=True)
            pass

    def delete_button_pressed(self):
        try:
            video_thread_running = self.process_ytv_thread.isRunning()
        except Exception as e:
            video_thread_running = False
        try:
            playlist_thread_running = self.process_ytv_play_list_thread.isRunning()
        except Exception as e:
            playlist_thread_running = False

        try:
            if video_thread_running:
                self.process_ytv_thread.kill()
                self.progress_bar_disable()
                self.hide_show_play_pause_button(hide=True)
                self.process_ytv_thread.terminate()
            elif playlist_thread_running:
                self.process_ytv_play_list_thread.kill()
                self.progress_bar_disable()
                self.hide_show_play_pause_button(hide=True)
                self.process_ytv_play_list_thread.terminate()
        except Exception as e:
            pass

    def popup_message(self, title, message, error=False):
        self.msg = QMessageBox()
        self.msg.setWindowFlag(QtCore.Qt.FramelessWindowHint)
        self.msg.setStyleSheet("background-color:rgba(0, 57, 96, 1);color:white;")
        if error:
            self.msg.setIcon(QMessageBox.Warning)
        else:
            self.msg.setIcon(QMessageBox.Information)
        self.msg.setText(title)
        self.msg.setInformativeText(message)
        self.msg.setStandardButtons(QMessageBox.Ok)
        self.msg.exec_()

    def progress_bar_enable(self):
        self.ui.progress_bar.setVisible(True)
        self.ui.progress_bar.setRange(0, 0)

    def progress_bar_disable(self):
        self.ui.progress_bar.setVisible(False)
        self.ui.progress_bar.setRange(0, 1)

    def setProgress_net_speed(self, value):
        self.ui.internet_speed_2.setText(value[0][0])
        self.ui.indicator_2.setText(value[0][1])
        self.ui.internet_2.setText(value[1])
        self.speed = value[0][0]
        self.unit = value[0][1]

    def open_download_path(self):
        folder_loc = QFileDialog.getExistingDirectory(self, "Select Downloads Directory",
                                                      self.Default_loc,
                                                      QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if folder_loc:
            if check_default_location(folder_loc):
                self.ui.download_path_edit_2.setText(folder_loc + "/YOUTUBE_DL")
                self.Default_loc = folder_loc
            else:
                self.popup_message(title="Download Path Invalid", message="Download Path Must Inside Home Directory")
                return False

    def check_for_audio_only(self):
        if self.ui.select_format_obj_2.currentText() == "AUDIO - MP3":
            self.ui.select_fps_obj_2.setEnabled(False)
            self.ui.select_quality_obj_2.setEnabled(False)
        else:
            self.ui.select_fps_obj_2.setEnabled(True)
            self.ui.select_quality_obj_2.setEnabled(True)

    def enable_hd_button_message(self):
        if self.ui.hd_radio_button_2.isChecked():
            if self.check_your_plan():
                message = "On Enabling HD+ feature, YouTube videos will be available in more Quality formats. " \
                          "\n\nINFO: For 2k, 4k, 8k Quality videos, system will auto use WEBM(.mkv) video format."
                self.popup_message(title="HD+ Quality Feature (Pro Feature)", message=message)
                self.is_hd_plus = True
                self.ytv_link_clicked()
            else:
                self.is_hd_plus = False
                self.ui.hd_radio_button_2.setChecked(False)
        else:
            self.is_hd_plus = False
            self.ytv_link_clicked()

    def hide_show_play_pause_button(self, hide=True):
        self.ui.pause_button.setVisible(not hide)
        self.ui.delete_button.setVisible(not hide)

    def ytv_link_clicked(self):
        data = self.ui.yt_video_link.text()
        if data != "":
            if data.startswith("http://www.youtube.com/") or data.startswith(
                    "https://www.youtube.com/") or data.startswith("https://youtube.com/"):
                if check_internet_connection():
                    try:
                        is_running = self.process_ytv_thread.isRunning()
                    except Exception as e:
                        is_running = False
                    try:
                        is_playlist_fetch_running = self.get_videos_list.isRunning()
                    except Exception as e:
                        is_playlist_fetch_running = False
                    try:
                        is_playlist_download_running = self.process_ytv_play_list_thread.isRunning()
                    except Exception as e:
                        is_playlist_download_running = False
                    try:
                        is_playlist_process = self.process_ytv_playlist_thread.isRunning()
                    except Exception as e:
                        is_playlist_process = False
                    if not is_running and not is_playlist_fetch_running and not is_playlist_download_running and not is_playlist_process:
                        self.progress_bar_enable()
                        if self.ui.hd_radio_button_2.isChecked():
                            self.is_hd_plus = True
                        self.ui.select_format_obj_2.clear()
                        self.ui.select_quality_obj_2.clear()
                        self.ui.select_fps_obj_2.clear()
                        try:
                            net_speed_thread = self.net_speed_thread.isRunning()
                        except Exception as e:
                            net_speed_thread = False
                            pass
                        if not net_speed_thread:
                            self.start_net_speed_thread()
                        self.process_ytv_thread = ProcessYtV(self.ui.yt_video_link.text(), self.is_hd_plus,
                                                             self.Default_loc)
                        self.process_ytv_thread.change_value.connect(self.setProgressVal)
                        self.process_ytv_thread.start()
                    else:
                        self.popup_message(title="Task Already In Queue",
                                           message="Please wait for the Running task to finish!")
                else:
                    self.popup_message(title="No internet connection", message="Please check your internet connection!")

    def paste_button_clicked(self):
        self.ui.yt_video_link.clear()
        self.ui.yt_video_link.setText(QApplication.clipboard().text())

    def setProgressVal(self, yt_data):
        self.progress_bar_disable()
        if yt_data.get("status"):
            self.yt = yt_data.get("yt")
            self.title = yt_data.get("title")
            self.length = yt_data.get("length")
            thumbnail_path, title, length = process_html_data(yt_data, self.Default_loc)
            self.ui.textBrowser_thumbnail_9.setPixmap(QPixmap(thumbnail_path))
            self.ui.video_title_5.setText(title)
            self.ui.video_length_5.setText(f"Length: {length}")

            if yt_data.get("length") == 'Length: 00m:00s':
                self.popup_message(title="Live youtube Video Detected!",
                                   message="Live youtube Video cannot be downloaded.")
            all_format, all_quality, all_fps = yt_data.get("quality_data")
            self.ui.select_quality_obj_2.addItems(all_quality)
            self.ui.select_format_obj_2.addItems(all_format)
            self.ui.select_fps_obj_2.addItems(all_fps)
            self.ui.select_quality_obj_2.setCurrentIndex(0)
            self.ui.select_format_obj_2.setCurrentIndex(0)
            self.ui.select_fps_obj_2.setCurrentIndex(0)
            self.ui.tabWidget.setCurrentIndex(1)
        else:
            self.popup_message(title="Invalid Youtube Url", message="Please check your YT video url !")
            # self.popup_message(title="Video cannot be downloaded right now! (Schedule maintenance)",
            #                    message="Youtube always change their backend server, we are fixing our application in order to download videos for you.\n\n"
            #                            "Youtube-dl is in schedule maintenance. Don't worry we are pushing new updates for Youtube-dl soon.\nThanks\nSorry for inconvenience")

    def download_action(self):
        context = dict()
        context["quality"] = (str(self.ui.select_quality_obj_2.currentText()).split(" ")[0]).lower()
        try:
            is_running = self.process_ytv_thread.isRunning()
        except Exception as e:
            is_running = False
        try:
            is_playlist_fetch_running = self.get_videos_list.isRunning()
        except Exception as e:
            is_playlist_fetch_running = False
        try:
            is_playlist_download_running = self.process_ytv_play_list_thread.isRunning()
        except Exception as e:
            is_playlist_download_running = False

        if is_running or is_playlist_fetch_running or is_playlist_download_running:
            self.popup_message(title="Task Already In Queue", message="Please wait for the Running task to finish!")
        else:
            if context["quality"] not in ['select', '', None] and not is_running \
                    and not is_playlist_fetch_running and not is_playlist_download_running:
                context["formats"] = (str(self.ui.select_format_obj_2.currentText()).split(" ")[2]).lower()
                context["fps"] = int(str(self.ui.select_fps_obj_2.currentText()).split(" ")[0])
                context["url"] = self.ui.yt_video_link.text()
                context["is_hd_plus"] = self.is_hd_plus
                if self.ui.select_format_obj_2.currentText() == "VIDEO - MP4" or self.ui.select_format_obj_2.currentText() == "VIDEO - WEBM":
                    context["type"] = "video"
                if self.ui.select_format_obj_2.currentText() == "AUDIO - MP3" or self.ui.select_format_obj_2.currentText() == "AUDIO - MP3":
                    context["type"] = "audio"
                self.progress_bar_enable()
                self.ui.progress_bar.setRange(0, 100)
                context["location"] = self.Default_loc
                context["yt"] = self.yt
                context["main_obj"] = self
                self.counter = 0
                self.all_videos = True
                self.all_playlist = False
                self.process_ytv_thread = DownloadVideo(context)
                self.process_ytv_thread.change_value.connect(self.tc_process_download)
                self.process_ytv_thread.finished.connect(self.tc_finished_downloading_thread)
                self.process_ytv_thread.converting_videos.connect(self.tc_converting_videos)
                self.process_ytv_thread.error.connect(self.tc_error_on_downloading)
                self.process_ytv_thread.no_error.connect(self.tc_no_error)
                self.process_ytv_thread.after_kill.connect(self.tc_after_kill)
                self.process_ytv_thread.start()
            else:
                self.popup_message(title="Invalid Youtube Url", message="Please check your video link !")

    def tc_process_download(self, value_dict):
        if not value_dict.get("is_killed"):
            display_status = "({0}%) Completed: {1} of {2}               " \
                             "Speed: @{3}{4}".format(value_dict.get("progress"),
                                                     value_dict.get("downloaded"),
                                                     value_dict.get("total_size"),
                                                     self.speed,
                                                     self.unit)

            self.ui.progress_bar.setRange(0, 100)
            self.ui.progress_bar.setFormat(display_status)
            self.ui.progress_bar.setValue(value_dict.get("progress"))
        else:
            self.progress_bar_disable()

    def tc_finished_downloading_thread(self, json_data):
        if not json_data.get("is_killed"):
            self.hide_show_play_pause_button(hide=True)
            self.progress_bar_disable()
            try:
                self.download_page()
            except Exception as e:
                pass
            folder_path = json_data.get("file_path")
            play_path = json_data.get("play_path")
            if self.counter == 0:
                self.counter += 1
                message = f"Download Success\n\n{json_data.get('title')}"
                self.file_download_success_dialog(message, folder_path, play_path)

    def tc_converting_videos(self, value_dict):
        if value_dict.get("progress") % 2 == 0:
            if value_dict.get("type") == "audio":
                self.ui.progress_bar.setFormat("Converting audio to mp3 ...")
            else:
                self.ui.progress_bar.setFormat("Merging audio video ...")
        elif value_dict.get("progress") % 2 != 0:
            self.ui.progress_bar.resetFormat()
            self.ui.progress_bar.setRange(0, 100)
            self.ui.progress_bar.setValue(value_dict.get("progress"))

    def tc_error_on_downloading(self, error_dict):
        if error_dict.get("error") == "File Already Exists":
            file_path = error_dict.get("file_path")
            play_path = error_dict.get("play_path")
            title = error_dict.get("title")
            message = f"File Already Exists!\n\n{title}"
            if file_path and play_path:
                self.file_download_success_dialog(message, file_path, play_path)
            else:
                self.popup_message(title="File Already Exists", message=error_dict.get("error"))
        else:
            self.popup_message(title="Error Occurred", message=error_dict.get("error"))
            self.hide_show_play_pause_button(hide=True)

    def tc_no_error(self, message):
        if message == "no_error":
            self.hide_show_play_pause_button(hide=False)

    def tc_after_kill(self, unfinished_file_path):
        try:
            self.progress_bar_disable()
            os.remove(unfinished_file_path)

        except Exception as e:
            pass

    """
    
    <===========================================  Playlist Functionality:  =============================================> 
    
    """

    def open_download_path_playlist(self):
        folder_loc = QFileDialog.getExistingDirectory(self, "Select Downloads Directory",
                                                      self.Default_loc_playlist,
                                                      QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if folder_loc:
            if check_default_location(folder_loc):
                self.ui.download_path_edit_playlist.setText(folder_loc + "/YOUTUBE_DL")
                self.Default_loc_playlist = folder_loc
            else:
                self.popup_message(title="Download Path Invalid", message="Download Path Must Inside Home Directory")
                return False

    def enable_hd_button_playlist(self):
        if self.ui.hd_radio_button_playlist_2.isChecked():
            if self.check_your_plan():
                message = "On Enabling HD+ feature, YouTube Playlist videos will be available in more Quality formats"
                self.popup_message(title="HD+ Quality Feature (Pro Feature)", message=message)
                self.is_hd_plus_playlist = True
                self.ytv_link_clicked_playlist()
            else:
                self.is_hd_plus_playlist = False
                self.ui.hd_radio_button_playlist_2.setChecked(False)
        else:
            self.is_hd_plus_playlist = False
            self.ytv_link_clicked_playlist()

    def ytv_link_clicked_playlist(self):
        self.play_list_counter = 1
        data = self.ui.yt_video_link.text()
        if data != "":
            if data.startswith("http://www.youtube.com/") or data.startswith(
                    "https://www.youtube.com/") or data.startswith("https://youtube.com/"):
                if check_internet_connection():
                    try:
                        is_running = self.process_ytv_thread.isRunning()
                    except Exception as e:
                        is_running = False
                    try:
                        is_size_running = self.file_size_thread.isRunning()
                    except Exception as e:
                        is_size_running = False
                    try:
                        is_playlist_fetch_running = self.get_videos_list.isRunning()
                    except Exception as e:
                        is_playlist_fetch_running = False
                    try:
                        is_playlist_download_running = self.process_ytv_play_list_thread.isRunning()
                    except Exception as e:
                        is_playlist_download_running = False
                    try:
                        is_playlist_process = self.process_ytv_playlist_thread.isRunning()
                    except Exception as e:
                        is_playlist_process = False
                    if not is_running and not is_playlist_fetch_running and not is_playlist_download_running and not is_playlist_process and not is_size_running:
                        self.progress_bar_enable()
                        try:
                            net_speed_thread = self.net_speed_thread.isRunning()
                        except Exception as e:
                            net_speed_thread = False
                            pass
                        if not net_speed_thread:
                            self.start_net_speed_thread()
                        self.ui.select_videos_playlist_2.clear()
                        self.ui.select_quality_playlist_2.clear()
                        self.ui.select_type_playlist_2.clear()
                        self.ui.select_videos_playlist_2.setEnabled(False)
                        self.ui.select_quality_playlist_2.setEnabled(False)
                        self.ui.select_type_playlist_2.setEnabled(False)
                        if self.ui.hd_radio_button_playlist_2.isChecked():
                            self.is_hd_plus_playlist = True
                        self.process_ytv_playlist_thread = ProcessYtVPlayList(self.ui.yt_video_link.text(),
                                                                              self.Default_loc_playlist)
                        self.process_ytv_playlist_thread.change_value_playlist.connect(self.setProgressVal_playlist)
                        self.process_ytv_playlist_thread.start()
                    else:
                        self.popup_message(title="Task Already In Queue",
                                           message="Please wait for the Running task to finish!")
                else:
                    self.popup_message(title="No internet connection", message="Please check your internet connection!")

    def download_action_playlist(self):
        context = dict()
        try:
            context["quality"] = (str(self.ui.select_quality_playlist_2.currentText()).split(" ")[0]).lower()
            context["formats"] = (str(self.ui.select_type_playlist_2.currentText()).split(" ")[2]).lower()
        except Exception as e:
            pass
        try:
            is_video_running = self.process_ytv_thread.isRunning()
        except Exception as e:
            is_video_running = False
        try:
            is_playlist_download_running = self.process_ytv_play_list_thread.isRunning()
        except Exception as e:
            is_playlist_download_running = False
        try:
            is_playlist_fetch_running = self.get_videos_list.isRunning()
        except Exception as e:
            is_playlist_fetch_running = False

        if is_video_running:
            self.popup_message(title="Task Already In Queue", message="Please wait for the Running task to finish!")
        elif is_playlist_fetch_running:
            self.popup_message(title="Info", message="Please wait. Playlist videos are loading.")
        elif is_playlist_download_running:
            self.popup_message(title="Info", message="Please wait. Playlist videos are Already Downloading.")
        else:
            if context["quality"] not in ['select', '',
                                          None] and not is_video_running and not is_playlist_fetch_running:
                context["video_type"] = self.ui.select_type_playlist_2.currentText()
                context["selected_video"] = safe_string((self.ui.select_videos_playlist_2.currentText()))
                context["selected_video_index"] = self.ui.select_videos_playlist_2.currentIndex()

                context["all_yt_playlist_obj"] = self.total_obj
                context["playlist"] = self.playlist
                context["location"] = self.Default_loc_playlist
                context["main_obj"] = self
                self.progress_bar_enable()
                self.ui.progress_bar.setRange(0, 100)
                self.all_videos = False
                self.all_playlist = True
                self.process_ytv_play_list_thread = DownloadVideoPlayList(context)
                self.process_ytv_play_list_thread.change_value.connect(self.tc_process_download_playlist)
                self.process_ytv_play_list_thread.finished.connect(self.tc_finished_downloading_thread_playlist)
                self.process_ytv_play_list_thread.after_kill.connect(self.tc_after_kill_playlist)
                self.process_ytv_play_list_thread.playlist_finished.connect(
                    self.tc_finished_downloading_thread_playlist_all)
                self.process_ytv_play_list_thread.error_playlist.connect(self.error_playlist)
                self.process_ytv_play_list_thread.ffmpeg_conversion.connect(self.ffmpeg_playlist_conversion)
                self.process_ytv_play_list_thread.start()
                self.hide_show_play_pause_button(hide=False)
            else:
                self.popup_message(title="Invalid Youtube Url", message="Please check your YT video url !")

    def tc_process_download_playlist(self, value_dict):
        if value_dict.get("complete_playlist"):
            counter = value_dict.get("counter")
            display_status = "Video {0} of {1}:     ({2}%) Completed: {3} of {4}        " \
                             "Speed: @{5}{6}".format(counter,
                                                     self.total_videos,
                                                     value_dict.get("progress"),
                                                     value_dict.get("downloaded"),
                                                     value_dict.get("total_size"),
                                                     self.speed,
                                                     self.unit)
            self.ui.progress_bar.setRange(0, self.total_videos)
            self.ui.progress_bar.setFormat(display_status)
            self.ui.progress_bar.setValue(counter)
        else:
            if not value_dict.get("is_killed"):
                display_status = "({0}%) Completed: {1} of {2}               " \
                                 "Speed: @{3}{4}".format(value_dict.get("progress"),
                                                         value_dict.get("downloaded"),
                                                         value_dict.get("total_size"),
                                                         self.speed,
                                                         self.unit)

                self.ui.progress_bar.setRange(0, 100)
                self.ui.progress_bar.setFormat(display_status)
                self.ui.progress_bar.setValue(value_dict.get("progress"))
            else:
                self.progress_bar_disable()

    def ffmpeg_playlist_conversion(self, value_dict):
        self.hide_show_play_pause_button(hide=True)
        if value_dict.get("complete_playlist"):
            file_type = value_dict.get("type")
            counter = value_dict.get("counter")
            if file_type == "AUDIO - MP3":
                display_status = "Converting Audio {0} of {1}".format(counter, self.total_videos)
            else:
                display_status = "Converting Video {0} of {1}".format(counter, self.total_videos)
            self.ui.progress_bar.setRange(0, self.total_videos)
            self.ui.progress_bar.setFormat(display_status)
            self.ui.progress_bar.setValue(counter)
        else:
            if not value_dict.get("is_killed"):
                self.ui.progress_bar.resetFormat()
                self.ui.progress_bar.setRange(0, 100)
                self.ui.progress_bar.setValue(value_dict.get("progress"))
            else:
                self.progress_bar_disable()

    def setProgressVal_playlist(self, yt_playlist):
        if yt_playlist.get("status"):
            yt_video_data = yt_playlist.get("video_context")
            if yt_video_data:
                self.total_videos = yt_playlist.get("playlist_length")
                self.get_videos_list = GetPlaylistVideos(self.is_hd_plus_playlist, yt_playlist["playlist_videos"],
                                                         self.Default_loc_playlist)
                self.get_videos_list.get_video_list.connect(self.set_video_list)
                self.get_videos_list.partial_finish.connect(self.partial_finish)
                self.get_videos_list.finished_video_list.connect(self.finish_video_list)
                self.get_videos_list.start()
            else:
                self.progress_bar_disable()
                self.popup_message(title="Invalid Youtube Playlist Url", message="Please check your Playlist link !")
                return

            if yt_video_data.get("status"):
                self.playlist = yt_playlist.get("playlist")
                self.playlist_title = yt_playlist.get("playlist_title")
                self.total_videos = yt_playlist.get("playlist_length")
                thumbnail_path, title, total_videos = process_html_data_playlist(yt_playlist, self.Default_loc_playlist)
                self.ui.textBrowser_playlist_thumbnail.setPixmap(QPixmap(thumbnail_path))
                self.ui.video_title_playlist.setText(f"Title: {title}")
                self.ui.video_length_playlist.setText(f"Total Length: Calculating..")
                self.ui.video_total_playlist.setText(f"Total Videos: {total_videos}")
                self.ui.video_size_playlist.setText(f"Total Size: Calculating..")
                all_format, all_quality_playlist, all_fps = yt_video_data.get("quality_data")
                self.ui.select_quality_playlist_2.addItems(all_quality_playlist)
                self.ui.select_type_playlist_2.addItems(["VIDEO - MP4", "AUDIO - MP3"])
                self.ui.tabWidget.setCurrentIndex(2)
            else:
                self.progress_bar_disable()
                self.popup_message(title="Invalid Youtube Playlist Url", message="Please check your Playlist link !")
        else:
            self.progress_bar_disable()
            self.popup_message(title="Invalid Youtube Playlist Url", message="Please check your Playlist link !")
            # self.popup_message(title="Video cannot be downloaded right now! (Schedule maintenance)",
            #                    message="Youtube always change their backend server, we are fixing our application in order to download videos for you.\n\n"
            #                            "Youtube-dl is in schedule maintenance. Don't worry we are pushing new updates for Youtube-dl soon.\nThanks\nSorry for inconvenience")

    def set_video_list(self, play_list_videos):
        if self.play_list_counter > self.total_videos:
            display_status = "Loading Video {0} of {1}".format(self.total_videos, self.total_videos)
        else:
            display_status = "Loading Video {0} of {1}".format(self.play_list_counter, self.total_videos)
        self.ui.progress_bar.setRange(0, self.total_videos)
        self.ui.progress_bar.setFormat(display_status)
        self.ui.progress_bar.setValue(self.play_list_counter)
        self.ui.select_videos_playlist_2.addItem(play_list_videos)
        self.play_list_counter += 1

    def partial_finish(self):
        self.progress_bar_enable()

    def finish_video_list(self, playlist_quality_dict):
        self.total_obj = playlist_quality_dict.get("total_obj")
        self.ui.select_videos_playlist_2.setEnabled(True)
        self.ui.select_quality_playlist_2.setEnabled(True)
        self.ui.select_type_playlist_2.setEnabled(True)
        self.ui.select_quality_playlist_2.clear()
        self.ui.select_type_playlist_2.clear()
        all_format = playlist_quality_dict.get("all_format")
        all_quality = playlist_quality_dict.get("all_quality")
        self.ui.select_quality_playlist_2.addItems(all_quality)
        self.ui.select_type_playlist_2.addItems(all_format)
        self.progress_bar_disable()

    def tc_finished_downloading_thread_playlist(self, json_data):
        if not json_data.get("is_killed"):
            title = json_data.get("title")
            self.hide_show_play_pause_button(hide=True)
            self.progress_bar_disable()
            folder_path = json_data.get("file_path")
            play_path = json_data.get("play_path")
            message = f"Download Success!\n\n{title}"
            self.file_download_success_dialog(message, folder_path, play_path)

    def tc_finished_downloading_thread_playlist_all(self, json_data):
        if not json_data.get("is_killed"):
            self.hide_show_play_pause_button(hide=True)
            self.progress_bar_disable()
            folder_path = json_data.get("file_path")
            play_path = json_data.get("play_path")
            all_videos_list = ["Download Success\n\n", f"Playlist Name: {self.playlist.title}\n\n"]

            for i in range(self.ui.select_videos_playlist_2.count()):
                v_title = self.ui.select_videos_playlist_2.itemText(i)
                if v_title != "Select All":
                    v_title = str(i) + ". " + v_title + "\n"
                    all_videos_list.append(v_title)

            res = "".join(all_videos_list)
            self.file_download_success_dialog(res, folder_path, play_path)

    def error_playlist(self, error_dict):
        self.hide_show_play_pause_button(hide=True)
        if error_dict.get("error") == "File Already Exists":
            file_path = error_dict.get("file_path")
            play_path = error_dict.get("play_path")
            file_title = error_dict.get("file")
            if file_path and play_path:
                self.file_download_success_dialog(f"File Already in your Downloads!\n\n{file_title}", file_path,
                                                  play_path)
            else:
                self.popup_message(title="File Already Exists", message=error_dict.get("error"))
        else:
            self.popup_message(title="Error Occurred", message=error_dict.get("error"))

    def tc_after_kill_playlist(self, unfinished_file_path):
        try:
            self.progress_bar_disable()
            os.remove(unfinished_file_path)
        except Exception as e:
            pass

    def show_video_thumbnail(self):
        try:
            process_ytv_playlist_thread = self.process_ytv_playlist_thread.isRunning()
        except Exception as e:
            process_ytv_playlist_thread = False
        try:
            get_videos_list = self.get_videos_list.isRunning()
        except Exception as e:
            get_videos_list = False

        if not process_ytv_playlist_thread and not get_videos_list:
            try:
                title_text = self.ui.select_videos_playlist_2.currentText()
                if title_text not in ["Select All", None, ""]:
                    index = self.ui.select_videos_playlist_2.currentIndex()
                    yt_play_list_obj = self.total_obj[index - 1]
                    thumbnail_url = yt_play_list_obj.thumbnail_url
                    thumbnail_image_path = get_thumbnail_path_from_local(title_text, thumbnail_url,
                                                                         self.Default_loc_playlist)
                    self.ui.textBrowser_playlist_thumbnail.setPixmap(QPixmap(thumbnail_image_path))
                    self.ui.video_title_playlist.setText(f"Title: {title_text}")
                    self.ui.video_total_playlist.setText(f"Total Videos: {str(self.total_videos)}")
            except Exception as e:
                pass
            if self.ui.select_videos_playlist_2.currentText() in ["", None]:
                pass
            else:
                self.file_size_thread = FileSizeThread(self)
                self.file_size_thread.get_size_of_file.connect(self.set_file_size)
                self.file_size_thread.start()
                self.progress_bar_enable()

    def set_file_size(self, size_dict):
        video_size = size_dict.get("video_size")
        video_length = size_dict.get("video_length")

        print(video_size, video_length)
        if video_size or video_length:
            self.ui.video_size_playlist.setText(f"Total Size: {video_size}")
            title_text = self.ui.select_videos_playlist_2.currentText()
            if title_text in ["Select All", None, ""]:
                self.ui.video_title_playlist.setText(f"Title: {self.playlist_title}")
            else:
                self.ui.video_title_playlist.setText(f"Title: {self.ui.select_videos_playlist_2.currentText()}")
            self.ui.video_total_playlist.setText(f"Total Videos: {str(self.total_videos)}")
            self.ui.video_length_playlist.setText(f"Total Length: {video_length}")

        self.progress_bar_disable()

    def check_for_audio_only_playlist(self):
        try:
            process_ytv_playlist_thread = self.process_ytv_playlist_thread.isRunning()
        except Exception as e:
            process_ytv_playlist_thread = False
        try:
            get_videos_list = self.get_videos_list.isRunning()
        except Exception as e:
            get_videos_list = False

        if not process_ytv_playlist_thread and not get_videos_list:
            if self.ui.select_type_playlist_2.currentText() == "AUDIO - MP3":
                self.ui.select_quality_playlist_2.setEnabled(False)
            elif self.ui.select_type_playlist_2.currentText() in ['VIDEO - MP4', 'VIDEO - WEBM']:
                self.ui.select_quality_playlist_2.setEnabled(True)

            if self.ui.select_videos_playlist_2.currentText() in ["", None]:
                pass
            else:
                try:
                    file_size_thread_running = self.file_size_thread.isRunning()
                except Exception as e:
                    file_size_thread_running = False
                if not file_size_thread_running:
                    self.file_size_thread = FileSizeThread(self)
                    self.file_size_thread.get_size_of_file.connect(self.set_file_size)
                    self.file_size_thread.start()
                    self.progress_bar_enable()

    """
        Downloads functionality:--------------------------------------------------
    """

    def clear_all_history(self):
        try:
            self.msg = QMessageBox()
            self.msg.setWindowFlag(QtCore.Qt.FramelessWindowHint)
            self.msg.setStyleSheet("background-color:rgba(0, 57, 96, 1);color:white;")
            self.msg.setIcon(QMessageBox.Information)
            self.msg.setText("Are you sure want to clear all videos and playlist history?")
            cb = QCheckBox("Delete all Source file too")
            cb.setChecked(self.delete_source_file)
            self.msg.setCheckBox(cb)
            yes_button = self.msg.addButton(QMessageBox.Yes)
            no_button = self.msg.addButton(QMessageBox.No)
            self.msg.exec_()
            if self.msg.clickedButton() == yes_button:
                if cb.isChecked():
                    self.delete_source_file = True
                    self.clear_download_history_all()
                else:
                    self.delete_source_file = False
                    self.clear_download_history_all()
                self.get_user_download_data()
            if self.msg.clickedButton() == no_button:
                if cb.isChecked():
                    self.delete_source_file = True
                else:
                    self.delete_source_file = False

        except Exception as e:
            self.popup_message(title="Error while deleting the file!", message="", error=True)
            pass

    def clear_download_history_all(self):
        try:
            video_history_path = self.Default_loc + "/YOUTUBE_DL/.downloads/download_data.json"
            os.remove(video_history_path)
        except Exception as e:
            pass
        try:
            playlist_history_path = self.Default_loc_playlist + "/YOUTUBE_DL/.downloads/download_data.json"
            os.remove(playlist_history_path)
        except Exception as e:
            pass
        if self.delete_source_file:
            try:
                video_file_path = self.Default_loc + "/YOUTUBE_DL"
                shutil.rmtree(video_file_path)
            except Exception as e:
                pass
            try:
                playlist_video_path = self.Default_loc_playlist + "/YOUTUBE_DL"
                shutil.rmtree(playlist_video_path)
            except Exception as e:
                pass

    def set_all_videos(self):
        self.show_default_type = self.Default_loc
        self.all_videos = True
        self.all_playlist = False
        selected_download_button_css(self)
        self.get_user_download_data()

    def set_all_playlist(self):
        self.show_default_type = self.Default_loc_playlist
        self.all_videos = False
        self.all_playlist = True
        selected_download_button_css(self)
        self.get_user_download_data()

    def get_user_download_data(self):
        selected_download_button_css(self)
        if self.all_playlist:
            self.show_default_type = self.Default_loc_playlist
        else:
            self.show_default_type = self.Default_loc
        try:
            self.ui.listWidget.clear()
            size = QtCore.QSize()
            size.setHeight(50)
            size.setWidth(50)
            user_json_data = get_local_download_data(self.show_default_type)
            user_json_data = sorted(user_json_data, key=lambda k: k['sort_param'], reverse=True)
            exist_entry = [self.ui.listWidget.item(x).text() for x in range(self.ui.listWidget.count())]

            for row in user_json_data:
                if self.all_playlist:
                    if row.get("download_type", "") == "videos":
                        continue
                else:
                    if row.get("download_type", "") == "playlist":
                        continue
                thumbnail_path = row.get("thumbnail_path")
                if not os.path.isfile(thumbnail_path):
                    thumbnail_path = ":/myresource/resource/download_preview.png"
                title = row.get("title_show")
                file_type = str(row.get("type")).upper()
                resolution = str(row.get("resolution")).upper()
                subtype = str(row.get("subtype")).upper()
                length = row.get("length")
                file_size = row.get("size")
                if file_type == "AUDIO":
                    details = f"{title} | {file_type} | Size: {file_size} | Length: {length}"
                else:
                    details = f"{title} | {file_type}-{resolution}-{subtype} | Size: {file_size} | Length: {length}"

                if details not in exist_entry:
                    icon = QtGui.QIcon()
                    icon.addPixmap(QtGui.QPixmap(thumbnail_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                    item = QtWidgets.QListWidgetItem(icon, details)
                    item.setSizeHint(size)
                    self.ui.listWidget.addItem(item)
            self.ui.listWidget.setIconSize(QtCore.QSize(90, 90))
        except Exception as e:
            self.popup_message(title="Error while getting download history!", message="", error=True)
            pass

    def show_downloads_folder(self):
        try:
            user_json_data = get_local_download_data(self.show_default_type)
            user_json_data = sorted(user_json_data, key=lambda k: k['sort_param'], reverse=True)
            c_index = self.ui.listWidget.currentIndex().row()
            if c_index != -1:
                selected_video = user_json_data[c_index]
                download_path = selected_video.get("download_path")
                if not os.path.isdir(download_path):
                    self.popup_message(title="Directory not found!", message="", error=True)
                else:
                    QDesktopServices.openUrl(QUrl(download_path))
            else:
                self.popup_message(title="Please select file first!", message="", error=True)
        except Exception as e:
            self.popup_message(title="Error while opening the directory!", message="", error=True)
            pass

    def play_videos_from_downloads(self):
        try:
            user_json_data = get_local_download_data(self.show_default_type)
            user_json_data = sorted(user_json_data, key=lambda k: k['sort_param'], reverse=True)
            if self.all_playlist:
                user_json_data = [row for row in user_json_data if row.get("download_type", "") == "playlist"]
            else:
                user_json_data = [row for row in user_json_data if row.get("download_type", "") == "videos"]
            c_index = self.ui.listWidget.currentIndex().row()
            if c_index != -1:
                selected_video = user_json_data[c_index]
                file_path = selected_video.get("file_path")
                if not os.path.isfile(file_path):
                    self.popup_message(title="File not found or deleted!", message="", error=True)
                else:
                    QDesktopServices.openUrl(QUrl(file_path))
            else:
                self.popup_message(title="Please select file first!!", message="", error=True)
        except Exception as e:
            self.popup_message(title="Error while playing the media!", message="", error=True)
            pass

    def details_video_from_downloads(self):
        try:
            c_index = self.ui.listWidget.currentIndex().row()
            if c_index != -1:
                video_info = get_local_download_data(self.show_default_type)
                video_info = sorted(video_info, key=lambda k: k['sort_param'], reverse=True)
                if self.all_playlist:
                    video_info = [row for row in video_info if row.get("download_type", "") == "playlist"]
                else:
                    video_info = [row for row in video_info if row.get("download_type", "") == "videos"]
                video_info = video_info[c_index]
                title = video_info.get("title_show", "-")
                length = video_info.get("length", "-")
                author = video_info.get("author", "-")
                v_type = video_info.get("type", "-")
                if v_type == "video":
                    fps = video_info.get("fps", "-")
                    resolution = video_info.get("resolution", "-")
                    subtype = video_info.get("subtype", "-")
                else:
                    fps = "N/A"
                    resolution = "N/A"
                    subtype = "MP3"
                size = video_info.get("size", "-")
                url = video_info.get("url", "-")
                download_date = video_info.get("download_date", "-")
                download_time = video_info.get("download_time", "-")
                all_videos_list = [
                    f"From Channel -      {str(author).upper()}\n"
                    f"File Type -     {str(v_type).upper()}\n"
                    f"Length -        {length}\n"
                    f"Resolution -        {str(resolution).upper()}\n"
                    f"Format -        {str(subtype).upper()}\n"
                    f"FPS -       {fps}\n"
                    f"Size -      {size}\n"
                    f"Watch URL -     {url}\n"
                    f"Downloaded On -     {download_date} {download_time}"]
                res = "".join(all_videos_list)
                self.popup_message(f"Title | {title}", res)
            else:
                self.popup_message(title="Please select file first!", message="", error=True)
        except Exception as e:
            self.popup_message(title="Error while getting details!", message="", error=True)
            pass

    def delete_video_from_downloads(self):
        try:
            self.msg = QMessageBox()
            self.msg.setWindowFlag(QtCore.Qt.FramelessWindowHint)
            self.msg.setStyleSheet("background-color:rgba(0, 57, 96, 1);color:white;")
            self.msg.setIcon(QMessageBox.Information)
            c_index = self.ui.listWidget.currentIndex().row()
            if c_index != -1:
                current_file_to_delete = self.ui.listWidget.currentItem().text()
                self.msg.setText(f"Are you sure want to delete ?\n\n{current_file_to_delete}")
                cb = QCheckBox("Delete Source file too")
                cb.setChecked(self.delete_source_file)
                self.msg.setCheckBox(cb)
                yes_button = self.msg.addButton(QMessageBox.Yes)
                no_button = self.msg.addButton(QMessageBox.No)
                self.msg.exec_()
                if self.msg.clickedButton() == yes_button:
                    if cb.isChecked():
                        self.delete_source_file = True
                        self.delete_entry_from_list(delete_source_file=True)
                    else:
                        self.delete_source_file = False
                        self.delete_entry_from_list()
                if self.msg.clickedButton() == no_button:
                    if cb.isChecked():
                        self.delete_source_file = True
                    else:
                        self.delete_source_file = False
            else:
                self.popup_message(title="Please select file first!", message="", error=True)
        except Exception as e:
            self.popup_message(title="Error while deleting the file!", message="", error=True)
            pass

    def delete_entry_from_list(self, delete_source_file=False):
        video_info = get_local_download_data(self.show_default_type)
        c_index = self.ui.listWidget.currentIndex().row()
        if c_index != -1:
            video_info = sorted(video_info, key=lambda k: k['sort_param'], reverse=True)
            video_info_copy = deepcopy(video_info)
            if self.all_playlist:
                video_info = [row for row in video_info if row.get("download_type", "") == "playlist"]
            else:
                video_info = [row for row in video_info if row.get("download_type", "") == "videos"]
            poped_item = video_info.pop(c_index)
            poped_item_copy_index = video_info_copy.index(poped_item)
            video_info_copy.pop(poped_item_copy_index)
            save_after_delete(video_info_copy, self.show_default_type)
            self.ui.listWidget.clear()
            self.get_user_download_data()
            if delete_source_file:
                try:
                    file_path = poped_item.get("file_path")
                    os.remove(file_path)
                except Exception as e:
                    pass
        else:
            self.popup_message(title="Please select file first!", message="", error=True)

    def search_videos(self):
        try:
            search_string = self.ui.search_videos.text()
            video_info = get_local_download_data(self.show_default_type)
            video_info = sorted(video_info, key=lambda k: k['sort_param'], reverse=True)
            exist_entry = [x.get("title_show") for x in video_info]
            index = -1
            flag = 0
            index_list = set()
            for entry in exist_entry:
                index += 1
                if search_string.lower() in entry.lower():
                    index_list.add(index)
                    flag = 1
            if flag == 0:
                pass
            else:
                self.ui.listWidget.clear()
                size = QtCore.QSize()
                size.setHeight(50)
                size.setWidth(50)
                for number in range(0, len(video_info)):
                    if number in index_list:
                        row = video_info[number]
                        if self.all_playlist:
                            if row.get("download_type", "") == "videos":
                                continue
                        else:
                            if row.get("download_type", "") == "playlist":
                                continue
                        thumbnail_path = row.get("thumbnail_path")
                        if not os.path.isfile(thumbnail_path):
                            thumbnail_path = ":/myresource/resource/download_preview.png"
                        title = row.get("title_show")
                        file_type = str(row.get("type")).upper()
                        resolution = str(row.get("resolution")).upper()
                        subtype = str(row.get("subtype")).upper()
                        length = row.get("length")
                        file_size = row.get("size")
                        if file_type == "AUDIO":
                            details = f"{title} | {file_type} | Size: {file_size} | Length: {length}"
                        else:
                            details = f"{title} | {file_type}-{resolution}-{subtype} | Size: {file_size} | Length: {length}"
                        if details not in exist_entry:
                            icon = QtGui.QIcon()
                            icon.addPixmap(QtGui.QPixmap(thumbnail_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
                            item = QtWidgets.QListWidgetItem(icon, details)
                            item.setSizeHint(size)
                            self.ui.listWidget.addItem(item)
                self.ui.listWidget.setIconSize(QtCore.QSize(90, 90))
        except Exception as e:
            self.popup_message(title="Error while searching the files!", message="", error=True)
            pass

    def clear_search_bar_on_edit(self):
        if self.ui.search_videos.text() == "Search Download History":
            self.ui.search_videos.clear()

    """
            About page functionality:--------------------------------------------------
    """

    def redirect_to_warlordsoft(self):
        warlord_soft_link = "https://warlordsoftwares.in/"
        webbrowser.open(warlord_soft_link)

    def redirect_to_paypal_donation(self):
        paypal_donation_link = "https://www.paypal.com/paypalme/rishabh3354/5"
        webbrowser.open(paypal_donation_link)

    def ge_more_apps(self):
        paypal_donation_link = "https://snapcraft.io/search?q=rishabh"
        webbrowser.open(paypal_donation_link)

    def redirect_to_rate_snapstore(self):
        QDesktopServices.openUrl(QUrl("snap://youtube-dl-pro"))

    def redirect_to_feedback_button(self):
        feedback_link = "https://warlordsoftwares.in/contact_us/"
        webbrowser.open(feedback_link)

    def purchase_licence_2(self):
        if check_internet_connection():
            account_dict = get_user_data_from_local()
            if account_dict:
                account_id = str(account_dict.get("email")).split("@")[0]
                if account_id:
                    warlord_soft_link = f"https://warlordsoftwares.in/warlord_soft/subscription/?product={PRODUCT_NAME}&account_id={account_id} "
                else:
                    warlord_soft_link = f"https://warlordsoftwares.in/signup/"
                webbrowser.open(warlord_soft_link)
                data = dict()
                data["email"] = f"{account_id}@warlordsoft.in"
                data["password"] = f"{account_id}@warlordsoft.in"
                data["re_password"] = f"{account_id}@warlordsoft.in"
                self.save_token = SaveLocalInToken(data)
                self.save_token.start()
        else:
            self.popup_message(title="No internet connection", message="Please check your internet connection!")

    def refresh_account_2(self):
        self.ui.error_message.clear()
        self.ui.account_progress_bar.setRange(0, 0)
        self.ui.account_progress_bar.setVisible(True)
        self.refresh_thread = RefreshButtonThread(PRODUCT_NAME)
        self.refresh_thread.change_value_refresh.connect(self.after_refresh)
        self.refresh_thread.start()

    def after_refresh(self, response_dict):
        if response_dict.get("status"):
            user_plan_data = get_user_data_from_local()
            if user_plan_data:
                self.logged_in_user_plan_page(user_plan_data)
        else:
            self.ui.error_message.setText(response_dict.get("message"))
        self.ui.account_progress_bar.setRange(0, 1)
        self.ui.account_progress_bar.setVisible(False)

    def my_plan(self):
        token = check_for_local_token()
        if token not in [None, ""]:
            user_plan_data = get_user_data_from_local()
            if user_plan_data:
                self.logged_in_user_plan_page(user_plan_data)
            else:
                user_plan_data = dict()
                user_plan_data['plan'] = "N/A"
                user_plan_data['expiry_date'] = "N/A"
                user_plan_data['email'] = "N/A"
                self.logged_in_user_plan_page(user_plan_data)
        else:
            user_plan_data = get_user_data_from_local()
            if user_plan_data:
                self.logged_in_user_plan_page(user_plan_data)

    def logged_in_user_plan_page(self, user_plan_data):
        account_email = user_plan_data.get('email')
        plan = user_plan_data.get("plan", "N/A")
        expiry_date = user_plan_data.get("expiry_date")
        if account_email:
            account_id = str(account_email).split("@")[0]
            self.ui.lineEdit_account_id_2.setText(account_id)
        else:
            self.ui.lineEdit_account_id_2.setText("N/A")
        if plan == "Free Trial":
            self.ui.lineEdit_plan_2.setText("Evaluation")
        elif plan == "Life Time Free Plan":
            self.ui.purchase_licence_2.setEnabled(False)
            self.ui.refresh_account_2.setEnabled(False)
            self.ui.lineEdit_plan_2.setText(plan)
            self.ui.groupBox_13.setVisible(False)
            if self.one_time_congratulate:
                self.ui.account_progress_bar.setRange(0, 1)
                self.ui.account_progress_bar.setVisible(False)
                self.popup_message(title="Congratulations! Plan Upgraded to PRO",
                                   message="Your plan has been upgraded to PRO. Enjoy lifetime licence. Thankyou for your purchase.")
                self.one_time_congratulate = False
        else:
            self.ui.lineEdit_plan_2.setText(plan)
        if expiry_date:
            if plan == "Life Time Free Plan":
                self.ui.lineEdit_expires_on_2.setText(f"{PRODUCT_NAME} PRO VERSION")
                self.is_plan_active = True
            else:
                plan_days_left = days_left(expiry_date)
                if plan_days_left == "0 Day(s) Left":
                    self.ui.error_message.setText("Evaluation period ended, Upgrade to Pro")
                    self.ui.lineEdit_expires_on_2.setText(plan_days_left)
                    self.is_plan_active = False
                    self.ui.hd_radio_button_2.setChecked(False)
                    self.ui.hd_radio_button_playlist_2.setChecked(False)
                else:
                    self.is_plan_active = True
                    self.ui.lineEdit_expires_on_2.setText(plan_days_left)
        else:
            self.ui.lineEdit_expires_on_2.setText("N/A")

    def check_your_plan(self):
        if not self.is_plan_active:
            self.msg = QMessageBox()
            self.msg.setWindowFlag(QtCore.Qt.FramelessWindowHint)
            self.msg.setStyleSheet("background-color:rgba(0, 57, 96, 1);color:white;")
            self.msg.setIcon(QMessageBox.Information)
            self.msg.setText("Evaluation period ended, Upgrade to Pro")
            self.msg.setInformativeText(
                "In Youtube-dl free version, HD+ option is not available. But you can still download SD quality videos.\n"
                "Please support the developer and purchase a license to UNLOCK this feature.")
            purchase = self.msg.addButton(QMessageBox.Yes)
            close = self.msg.addButton(QMessageBox.Yes)
            purchase.setText('Purchase Licence')
            close.setText('Close')
            purchase.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_DialogOkButton)))
            close.setIcon(QIcon(QApplication.style().standardIcon(QStyle.SP_BrowserStop)))
            self.msg.exec_()
            try:
                if self.msg.clickedButton() == purchase:
                    self.account_page()
                elif self.msg.clickedButton() == close:
                    pass
            except Exception as e:
                pass
            return False
        return True


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    sys.exit(app.exec_())
