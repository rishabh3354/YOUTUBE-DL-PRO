import os
import time
import psutil
import requests
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from pytube import YouTube
from helper import run_ffmpeg_command, safe_string, save_download_info, get_file_size_for_playlist, get_file_size, \
    get_all_playlist_quality, check_internet_connection_for_net_speed, humanbytes
from youtube_script import process_ytv, get_download_path, process_playlist
import youtube_script
import pytube.request
pytube.request.default_range_size = 500000


class ProcessYtV(QtCore.QThread):
    change_value = pyqtSignal(dict)

    def __init__(self, url, is_hd_plus, location, parent=None):
        super(ProcessYtV, self).__init__(parent)
        self.url = url
        self.is_hd_plus = is_hd_plus
        self.location = location

    def run(self):
        ytv_data = process_ytv(self.url, self.is_hd_plus, self.location)
        self.change_value.emit(ytv_data)


class GetPlaylistVideos(QtCore.QThread):
    get_video_list = pyqtSignal(str)
    partial_finish = pyqtSignal()
    finished_video_list = pyqtSignal(dict)
    partial_progress = pyqtSignal(dict)

    def __init__(self, is_hd_plus_playlist, all_videos, location, parent=None):
        super(GetPlaylistVideos, self).__init__(parent)
        self.is_hd_plus_playlist = is_hd_plus_playlist
        self.all_videos = all_videos
        self.location = location

    def run(self):
        self.get_video_list.emit("Select All")
        total_obj = []

        for url in self.all_videos:
            try:
                yt = YouTube(url)
                total_obj.append(yt)
                self.get_video_list.emit(yt.title)
                try:
                    image_url = yt.thumbnail_url
                    r = requests.get(image_url)
                    file_extension = '.jpg'
                    with open(f"{get_download_path(self.location, thumbnail=True)}/{safe_string(yt.title)}{file_extension}", 'wb') as f:
                        f.write(r.content)
                except Exception as eit:
                    pass
            except Exception as e:
                print(e)

        self.partial_finish.emit()
        playlist_quality_dict = get_all_playlist_quality(total_obj, self.is_hd_plus_playlist, self)
        playlist_quality_dict["total_obj"] = total_obj
        self.finished_video_list.emit(playlist_quality_dict)


class ProcessYtVPlayList(QtCore.QThread):
    change_value_playlist = pyqtSignal(dict)

    def __init__(self, url, location, parent=None):
        super(ProcessYtVPlayList, self).__init__(parent)
        self.url = url
        self.location = location

    def run(self):
        ytv_data = process_playlist(self.url, self.location)
        self.change_value_playlist.emit(ytv_data)


class DownloadVideo(QtCore.QThread):
    change_value = pyqtSignal(dict)
    finished = pyqtSignal(dict)
    converting_videos = pyqtSignal(dict)
    error = pyqtSignal(dict)
    no_error = pyqtSignal(str)
    after_kill = pyqtSignal(str)

    def __init__(self, context, parent=None):
        super(DownloadVideo, self).__init__(parent)
        self.context = context
        self.type = self.context.get('type')
        self.is_hd_plus = self.context.get('is_hd_plus')
        self.yt = self.context.get("yt")
        self.title = self.yt.title
        self.main_obj = self.context.get("main_obj")
        self.location = self.context.get('location')
        self.audio_download_path = get_download_path(self.location, download_audio_path=True)
        self.video_download_path = get_download_path(self.location, download_video_path=True)
        self.dash_download_path = get_download_path(self.location, process_dash_stream=True)
        self.process_dash = False
        self.full_file_path = None
        self.audio_filename = None

        # thread control flags
        self.is_paused = False
        self.is_killed = False

        def progress_callback(stream, chunk, bytes_remaining):
            try:
                progress_dict = {"is_hd_plus": self.is_hd_plus, "type": self.type,
                                 "progress": 0, "stop": False, "is_killed": self.is_killed,
                                 "file_path": self.video_download_path,
                                 "play_path": self.full_file_path,
                                 "title": self.title,
                                 "total_size": humanbytes(self.yt_obj.filesize),
                                 "downloaded": humanbytes(0)
                                 }

                while self.is_paused:
                    time.sleep(0)
                    if self.is_killed:
                        self.terminate()
                        self.after_kill.emit(self.full_file_path)
                        break

                if self.is_killed:
                    self.change_value.emit(progress_dict)
                    self.after_kill.emit(self.full_file_path)
                    self.terminate()

                size = self.yt_obj.filesize
                progress_dict["downloaded"] = humanbytes(size - bytes_remaining)
                progress_dict["progress"] = int(((size - bytes_remaining) / size) * 100)
                if progress_dict["progress"] == 100 and self.yt_obj.is_progressive:
                    progress_dict["stop"] = True
                    self.finished.emit(progress_dict)
                else:
                    self.change_value.emit(progress_dict)

            except Exception as e:
                self.error.emit({"error": str(e), "file_path": self.video_download_path,
                                 "play_path": self.full_file_path
                                 })
                pass

        def complete_callback(stream, file_handle):
            try:
                progress_dict = {"is_hd_plus": self.is_hd_plus, "type": self.type,
                                 "progress": 0, "stop": False, "is_killed": self.is_killed,
                                 "file_path": self.video_download_path,
                                 "play_path": self.full_file_path,
                                 "title": self.title,
                                 }

                if self.yt_obj.is_progressive is False and self.type == "video" and self.process_dash:
                    video_extension = self.context.get("formats")
                    dash_audio_file = f"{self.dash_download_path}/{self.dash_audio_filename}.mp4"
                    if self.context["quality"] in ["1440p", "2160p", "4320p"] or self.context["formats"] == "webm":
                        dash_video_file = f"{self.dash_download_path}/{self.dash_video_filename}.webm"
                        out_file_name = f"{self.video_download_path}/{self.dash_video_filename}.mkv"
                    else:
                        out_file_name = f"{self.video_download_path}/{self.dash_video_filename}.{video_extension}"
                        dash_video_file = f"{self.dash_download_path}/{self.dash_video_filename}.{video_extension}"

                    for progress_dict["progress"] in run_ffmpeg_command(
                            ['ffmpeg', '-i', dash_video_file, '-i', dash_audio_file, '-c:v', 'copy', '-c:a', 'copy',
                             out_file_name]):
                        while self.is_paused:
                            time.sleep(0)
                            if self.is_killed:
                                self.terminate()
                                self.after_kill.emit(self.full_file_path)
                                break
                        if self.is_killed:
                            self.terminate()
                            self.after_kill.emit(self.full_file_path)
                            break
                        if progress_dict["progress"] == 100 and self.process_dash:
                            self.finished.emit(progress_dict)
                        else:
                            self.converting_videos.emit(progress_dict)

                    os.remove(dash_audio_file)
                    os.remove(dash_video_file)

                elif self.type == "audio":
                    self.converting_videos.emit(progress_dict)
                    in_file_path = f"{self.audio_download_path}/{self.audio_filename}.mp4"
                    out_file_path = f"{self.audio_download_path}/{self.audio_filename}.mp3"

                    progress_dict = {"is_hd_plus": self.is_hd_plus, "type": self.type, "progress": 0,
                                     "stop": self.process_dash, "is_killed": self.is_killed,
                                     "file_path": self.audio_download_path,
                                     "play_path": f"{self.audio_download_path}/{self.audio_filename}.mp3",
                                     "title": self.title,
                                     }

                    for progress_dict["progress"] in run_ffmpeg_command(
                            ['ffmpeg', '-i', in_file_path, '-vn', out_file_path]):

                        while self.is_paused:
                            time.sleep(0)
                            if self.is_killed:
                                self.terminate()
                                self.after_kill.emit(out_file_path)
                                break

                        if self.is_killed:
                            self.terminate()
                            self.after_kill.emit(out_file_path)
                            break
                        if progress_dict["progress"] == 100:
                            self.finished.emit(progress_dict)
                        else:
                            self.converting_videos.emit(progress_dict)
                    os.remove(in_file_path)

            except Exception as e:
                self.error.emit({"error": str(e), "file_path": self.video_download_path,
                                 "play_path": self.full_file_path
                                 })
                pass

        self.yt.register_on_progress_callback(progress_callback)
        self.yt.register_on_complete_callback(complete_callback)

    def run(self):
        try:
            if self.type == "video" and not self.is_hd_plus:
                yt = self.yt.streams.filter(progressive=True, file_extension=self.context["formats"],
                                            fps=self.context["fps"],
                                            resolution=self.context["quality"])
                if yt:
                    self.yt_obj = yt.first()
                    title = str(self.yt_obj.title)
                    filename = safe_string("{0}_{1}_{2}_{3}fps".format(title,
                                                                       self.yt_obj.type,
                                                                       self.context["quality"],
                                                                       self.context["fps"],
                                                                       ))

                    self.full_file_path = self.video_download_path + "/" + filename + "." + self.yt_obj.subtype
                    if not os.path.isfile(self.full_file_path):
                        self.no_error.emit("no_error")
                        self.main_obj.ui.progress_bar.setRange(0, 0)
                        self.yt_obj.download(self.video_download_path, filename=f"{filename}.{self.yt_obj.subtype}")
                        save_download_info(self.yt, self.yt_obj, self.video_download_path, self.full_file_path,
                                           self.location)
                    else:
                        self.error.emit({"error": "File Already Exists", "file_path": self.video_download_path,
                                         "play_path": self.full_file_path, "title": title
                                         })
            elif self.type == "audio":
                yt = self.yt.streams.filter(only_audio=True, subtype='mp4')
                if yt:
                    self.yt_obj = yt.first()
                    title = str(self.yt_obj.title)
                    self.audio_filename = safe_string("{0}_{1}".format(title, self.yt_obj.type))
                    full_file_path = self.audio_download_path + "/" + self.audio_filename + "." + "mp3"
                    if not os.path.isfile(full_file_path):
                        self.no_error.emit("no_error")
                        self.main_obj.ui.progress_bar.setRange(0, 0)
                        self.yt_obj.download(self.audio_download_path, filename=f"{self.audio_filename}.{self.yt_obj.subtype}")
                        save_download_info(self.yt, self.yt_obj, self.audio_download_path, full_file_path,
                                           self.location)
                    else:
                        self.error.emit({"error": "File Already Exists", "file_path": self.audio_download_path,
                                         "play_path": full_file_path, "title": title
                                         })

            elif self.type == "video" and self.is_hd_plus:
                skip_audio = False
                if self.context["quality"] in ["1440p", "2160p", "4320p"]:
                    self.context["formats"] = "webm"
                video_yt = self.yt.streams.filter(file_extension=self.context["formats"],
                                                  fps=self.context["fps"],
                                                  resolution=self.context["quality"])
                if video_yt:
                    self.yt_obj = video_yt.first()
                    title = str(self.yt_obj.title)
                    self.dash_video_filename = safe_string("{0}_{1}_{2}_{3}fps".format(title,
                                                                                       self.yt_obj.type,
                                                                                       self.context["quality"],
                                                                                       self.context["fps"],
                                                                                       ))
                    if self.context["quality"] in ["1440p", "2160p", "4320p"] or self.context["formats"] == "webm":
                        self.full_file_path = self.video_download_path + "/" + self.dash_video_filename + "." + "mkv"
                    else:
                        self.full_file_path = self.video_download_path + "/" + self.dash_video_filename + "." + self.yt_obj.subtype

                    if not os.path.isfile(self.full_file_path):
                        self.no_error.emit("no_error")
                        self.main_obj.ui.progress_bar.setRange(0, 0)
                        if self.yt_obj.is_progressive:
                            skip_audio = True
                            self.yt_obj.download(self.video_download_path, filename=f"{self.dash_video_filename}.{self.yt_obj.subtype}")
                        else:
                            self.yt_obj.download(self.dash_download_path, filename=f"{self.dash_video_filename}.{self.yt_obj.subtype}")
                        save_download_info(self.yt, self.yt_obj, self.video_download_path, self.full_file_path,
                                           self.location)
                    else:
                        skip_audio = True
                        self.error.emit({"error": "File Already Exists", "file_path": self.video_download_path,
                                         "play_path": self.full_file_path, "title": title
                                         })
                else:
                    if self.context["quality"] in ["1440p", "2160p", "4320p"]:
                        self.context["formats"] = "webm"
                    video_yt = self.yt.streams.filter(file_extension=self.context["formats"],
                                                      resolution=self.context["quality"])
                    if video_yt:
                        self.yt_obj = video_yt.first()
                        title = str(self.yt_obj.title)
                        self.dash_video_filename = safe_string("{0}_{1}_{2}".format(title,
                                                                                    self.yt_obj.type,
                                                                                    self.context["quality"],
                                                                                    ))
                        if self.context["quality"] in ["1440p", "2160p", "4320p"] or self.context["formats"] == "webm":
                            self.full_file_path = self.video_download_path + "/" + self.dash_video_filename + "." + "mkv"
                        else:
                            self.full_file_path = self.video_download_path + "/" + self.dash_video_filename + "." + self.yt_obj.subtype
                        if not os.path.isfile(self.full_file_path):
                            self.no_error.emit("no_error")
                            self.main_obj.ui.progress_bar.setRange(0, 0)
                            if self.yt_obj.is_progressive:
                                skip_audio = True
                                self.yt_obj.download(self.video_download_path, filename=f"{self.dash_video_filename}.{self.yt_obj.subtype}")
                            else:
                                self.yt_obj.download(self.dash_download_path, filename=f"{self.dash_video_filename}.{self.yt_obj.subtype}")
                            save_download_info(self.yt, self.yt_obj, self.video_download_path, self.full_file_path,
                                               self.location)
                        else:
                            skip_audio = True
                            self.error.emit({"error": "File Already Exists", "file_path": self.video_download_path,
                                             "play_path": self.full_file_path, "title": title
                                             })
                    else:
                        video_yt = self.yt.streams.filter(resolution=self.context["quality"])
                        self.yt_obj = video_yt.first()
                        title = str(self.yt_obj.title)
                        self.dash_video_filename = safe_string("{0}_{1}_{2}".format(title,
                                                                                    self.yt_obj.type,
                                                                                    self.context["quality"],
                                                                                    ))
                        if self.context["quality"] in ["1440p", "2160p", "4320p"] or self.context["formats"] == "webm":
                            self.full_file_path = self.video_download_path + "/" + self.dash_video_filename + "." + "mkv"
                        else:
                            self.full_file_path = self.video_download_path + "/" + self.dash_video_filename + "." + self.yt_obj.subtype
                        if not os.path.isfile(self.full_file_path):
                            self.no_error.emit("no_error")
                            self.main_obj.ui.progress_bar.setRange(0, 0)
                            if self.yt_obj.is_progressive:
                                skip_audio = True
                                self.yt_obj.download(self.video_download_path, filename=f"{self.dash_video_filename}.{self.yt_obj.subtype}")
                            else:
                                self.yt_obj.download(self.dash_download_path, filename=f"{self.dash_video_filename}.{self.yt_obj.subtype}")
                            save_download_info(self.yt, self.yt_obj, self.video_download_path, self.full_file_path,
                                               self.location)
                        else:
                            skip_audio = True
                            self.error.emit({"error": "File Already Exists", "file_path": self.video_download_path,
                                             "play_path": self.full_file_path, "title": title
                                             })
                if skip_audio is False:
                    if not self.is_killed:
                        audio_yt = self.yt.streams.filter(only_audio=True, subtype='mp4')
                        if audio_yt:
                            self.process_dash = True
                            self.yt_obj = audio_yt.first()
                            title = str(self.yt_obj.title)
                            self.dash_audio_filename = safe_string("{0}_{1}".format(title, self.yt_obj.type))
                            self.yt_obj.download(self.dash_download_path, filename=f"{self.dash_audio_filename}.{self.yt_obj.subtype}")

        except Exception as e:
            self.error.emit({"error": str(e), "file_path": self.video_download_path,
                             "play_path": self.full_file_path, "title": ""
                             })
            pass

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def kill(self):
        self.is_killed = True


class DownloadVideoPlayList(QtCore.QThread):
    change_value = pyqtSignal(dict)
    finished = pyqtSignal(dict)
    playlist_finished = pyqtSignal(dict)
    error_playlist = pyqtSignal(dict)
    after_kill = pyqtSignal(str)
    ffmpeg_conversion = pyqtSignal(dict)

    def __init__(self, context, parent=None):
        super(DownloadVideoPlayList, self).__init__(parent)
        self.context = context
        self.type = self.context.get('video_type')
        self.quality = self.context.get('quality')
        self.formats = self.context.get('formats')
        self.playlist = self.context.get('playlist')
        self.main_obj = self.context.get('main_obj')
        self.all_yt_playlist_obj = self.context.get("all_yt_playlist_obj")
        self.selected_video_index = self.context.get('selected_video_index')
        self.selected_video = self.context.get('selected_video')
        self.location = self.context.get('location')
        if self.selected_video == "select-all":
            self.complete_playlist = True
        else:
            self.complete_playlist = False
        self.counter = 1

        self.audio_download_path = get_download_path(self.location, download_playlist_audio_path=True)
        self.video_download_path = get_download_path(self.location, download_playlist_video_path=True)
        self.dash_download_path = get_download_path(self.location, process_dash_stream=True)

        self.all_quality = list(youtube_script.ALL_VIDEO_RESOLUTIONS_PLAYLIST.keys())
        self.all_format = ['mp4', 'webm']

        # thread control flags
        self.is_paused = False
        self.is_killed = False

        def progress_callback(stream, chunk, bytes_remaining):
            try:
                progress_dict = {"type": self.type,
                                 "progress": 0,
                                 "is_killed": self.is_killed,
                                 "file_path": self.video_download_path,
                                 "play_path": self.full_file_path,
                                 "complete_playlist": self.complete_playlist,
                                 "counter": self.counter,
                                 "total_size": humanbytes(self.pl_obj.filesize),
                                 "downloaded": humanbytes(0)
                                 }

                while self.is_paused:
                    time.sleep(0)
                    if self.is_killed:
                        self.terminate()
                        self.after_kill.emit(self.full_file_path)
                        break

                if self.is_killed:
                    self.terminate()
                    self.after_kill.emit(self.full_file_path)
                else:
                    size = self.pl_obj.filesize
                    progress_dict["downloaded"] = humanbytes(size - bytes_remaining)
                    progress_dict["progress"] = int(((size - bytes_remaining) / size) * 100)
                    self.change_value.emit(progress_dict)

            except Exception as e:
                self.error_playlist.emit({"error": str(e), "file_path": self.video_download_path,
                                          "play_path": self.full_file_path
                                          })
                pass

        for item in self.all_yt_playlist_obj:
            item.register_on_progress_callback(progress_callback)

    def run(self):
        try:
            if self.type in ['VIDEO - MP4', 'VIDEO - WEBM']:
                if not self.complete_playlist:
                    video_obj = self.all_yt_playlist_obj[self.selected_video_index - 1]
                    pl_obj = video_obj.streams.filter(resolution=self.quality, file_extension=self.formats)
                    if len(pl_obj) == 0:
                        for formats in self.all_format:
                            pl_obj = video_obj.streams.filter(resolution=self.quality, file_extension=formats)
                            if pl_obj:
                                break
                        if len(pl_obj) == 0:
                            for quality in self.all_quality:
                                pl_obj = video_obj.streams.filter(resolution=quality)
                                if pl_obj:
                                    break
                            if len(pl_obj) == 0:
                                pl_obj = video_obj.streams.filter().first()

                    if pl_obj:
                        self.pl_obj = pl_obj.first()
                        self.title = self.pl_obj.title
                        filename = safe_string("{0}_{1}_{2}".format(self.title, self.pl_obj.type, self.quality))
                        filename_dash_audio = safe_string("{0}_{1}_{2}_dash_audio".format(self.title, self.pl_obj.type, self.quality))
                        if self.formats == "webm":
                            self.full_file_path = self.video_download_path + "/" + filename + "." + "mkv"
                        else:
                            self.full_file_path = self.video_download_path + "/" + filename + "." + self.pl_obj.subtype
                        self.full_file_path_dash = self.dash_download_path + "/" + filename + "." + self.pl_obj.subtype
                        self.full_audio_path_dash = self.dash_download_path + "/" + filename_dash_audio + "." + "mp4"
                        if not os.path.isfile(self.full_file_path):
                            # video dash
                            self.main_obj.ui.progress_bar.setRange(0, 0)
                            self.pl_obj.download(self.dash_download_path, filename=f"{filename}.{self.pl_obj.subtype}")
                            save_download_info(video_obj, self.pl_obj, self.video_download_path, self.full_file_path,
                                               self.location, True)
                            # Audio dash
                            pl_audio_obj = video_obj.streams.filter(only_audio=True).first()
                            self.pl_obj = pl_audio_obj
                            self.pl_obj.download(self.dash_download_path, filename=f"{filename_dash_audio}.{self.pl_obj.subtype}")
                            self.convert_video_using_ffmpeg()

                            progress_dict = {"type": self.type,
                                             "is_killed": self.is_killed,
                                             "file_path": self.video_download_path,
                                             "play_path": self.full_file_path,
                                             "complete_playlist": self.complete_playlist,
                                             "counter": self.counter,
                                             "title": self.title
                                             }
                            self.finished.emit(progress_dict)
                        else:
                            self.error_playlist.emit(
                                {"error": "File Already Exists", "file_path": self.video_download_path,
                                 "play_path": self.full_file_path, "file": self.title
                                 })
                else:
                    self.counter = 1
                    for video_obj in self.all_yt_playlist_obj:
                        pl_obj = video_obj.streams.filter(resolution=self.quality, file_extension=self.formats)
                        if len(pl_obj) == 0:
                            for formats in self.all_format:
                                pl_obj = video_obj.streams.filter(resolution=self.quality, file_extension=formats)
                                if pl_obj:
                                    break
                            if len(pl_obj) == 0:
                                for quality in self.all_quality:
                                    pl_obj = video_obj.streams.filter(resolution=quality)
                                    if pl_obj:
                                        break
                                if len(pl_obj) == 0:
                                    pl_obj = video_obj.streams.filter().first()

                        if pl_obj:
                            self.pl_obj = pl_obj.first()
                            self.title = self.pl_obj.title
                            filename = safe_string("{0}_{1}_{2}".format(self.title, self.pl_obj.type, self.quality))
                            filename_dash_audio = safe_string("{0}_{1}_{2}_dash_audio".format(self.title, self.pl_obj.type, self.quality))
                            if self.formats == "webm":
                                self.full_file_path = self.video_download_path + "/" + filename + "." + "mkv"
                            else:
                                self.full_file_path = self.video_download_path + "/" + filename + "." + self.pl_obj.subtype
                            self.full_file_path_dash = self.dash_download_path + "/" + filename + "." + self.pl_obj.subtype
                            self.full_audio_path_dash = self.dash_download_path + "/" + filename_dash_audio + "." + "mp4"
                            if not os.path.isfile(self.full_file_path):
                                # video dash
                                self.pl_obj.download(self.dash_download_path, filename=f"{filename}.{self.pl_obj.subtype}")
                                save_download_info(video_obj, self.pl_obj, self.video_download_path,
                                                   self.full_file_path,
                                                   self.location, True)
                                # Audio dash
                                pl_audio_obj = video_obj.streams.filter(only_audio=True).first()
                                self.pl_obj = pl_audio_obj
                                self.pl_obj.download(self.dash_download_path, filename=f"{filename_dash_audio}.{self.pl_obj.subtype}")
                                self.convert_video_using_ffmpeg()
                                if self.counter == len(self.all_yt_playlist_obj):
                                    progress_dict = {"type": self.type,
                                                     "is_killed": self.is_killed,
                                                     "file_path": self.video_download_path,
                                                     "play_path": self.full_file_path,
                                                     "complete_playlist": self.complete_playlist,
                                                     "counter": self.counter,
                                                     "title": self.title
                                                     }
                                    self.playlist_finished.emit(progress_dict)
                            else:
                                if self.counter == len(self.all_yt_playlist_obj):
                                    progress_dict = {"type": self.type,
                                                     "is_killed": self.is_killed,
                                                     "file_path": self.video_download_path,
                                                     "play_path": self.full_file_path,
                                                     "complete_playlist": self.complete_playlist,
                                                     "counter": self.counter,
                                                     "title": self.title
                                                     }
                                    self.playlist_finished.emit(progress_dict)
                                self.error_playlist.emit(
                                    {"error": "File Already Exists", "file_path": self.video_download_path,
                                     "play_path": self.full_file_path, "file": self.title
                                     })
                            self.counter += 1
            else:
                # Audio
                if not self.complete_playlist:
                    video_obj = self.all_yt_playlist_obj[self.selected_video_index - 1]
                    pl_obj = video_obj.streams.filter(only_audio=True)

                    if pl_obj:
                        self.pl_obj = pl_obj.first()
                        self.title = self.pl_obj.title
                        self.audio_filename = safe_string("{0}_{1}".format(self.title, self.pl_obj.type))
                        self.in_file_path = f"{self.audio_download_path}/{self.audio_filename}.mp4"
                        self.full_file_path = f"{self.audio_download_path}/{self.audio_filename}.mp3"
                        if not os.path.isfile(self.full_file_path):
                            self.main_obj.ui.progress_bar.setRange(0, 0)
                            self.pl_obj.download(self.audio_download_path, filename=f"{self.audio_filename}.{self.pl_obj.subtype}")
                            self.convert_audio_using_ffmpeg()
                            save_download_info(video_obj, self.pl_obj, self.audio_download_path, self.full_file_path,
                                               self.location, True)
                        else:
                            self.error_playlist.emit(
                                {"error": "File Already Exists", "file_path": self.audio_download_path,
                                 "play_path": self.full_file_path, "file": self.title
                                 })
                else:
                    self.counter = 1
                    for video_obj in self.all_yt_playlist_obj:
                        pl_obj = video_obj.streams.filter(only_audio=True)
                        if pl_obj:
                            self.pl_obj = pl_obj.first()
                            self.title = self.pl_obj.title
                            self.audio_filename = safe_string("{0}_{1}".format(self.title, self.pl_obj.type))
                            self.in_file_path = f"{self.audio_download_path}/{self.audio_filename}.mp4"
                            self.full_file_path = f"{self.audio_download_path}/{self.audio_filename}.mp3"
                            if not os.path.isfile(self.full_file_path):
                                self.pl_obj.download(self.audio_download_path, filename=f"{self.audio_filename}.{self.pl_obj.subtype}")
                                self.convert_audio_using_ffmpeg(single_audio=False)
                                save_download_info(video_obj, self.pl_obj, self.audio_download_path,
                                                   self.full_file_path,
                                                   self.location, True)
                                if self.counter == len(self.all_yt_playlist_obj):
                                    progress_dict = {"type": self.type,
                                                     "is_killed": self.is_killed,
                                                     "file_path": self.video_download_path,
                                                     "play_path": self.full_file_path,
                                                     "complete_playlist": self.complete_playlist,
                                                     "counter": self.counter,
                                                     "title": self.title
                                                     }
                                    self.playlist_finished.emit(progress_dict)
                            else:
                                if self.counter == len(self.all_yt_playlist_obj):
                                    progress_dict = {"type": self.type,
                                                     "is_killed": self.is_killed,
                                                     "file_path": self.video_download_path,
                                                     "play_path": self.full_file_path,
                                                     "complete_playlist": self.complete_playlist,
                                                     "counter": self.counter,
                                                     "title": self.title
                                                     }
                                    self.playlist_finished.emit(progress_dict)
                                self.error_playlist.emit(
                                    {"error": "File Already Exists", "file_path": self.video_download_path,
                                     "play_path": self.full_file_path, "file": self.title
                                     })
                            self.counter += 1

        except Exception as e:
            self.error_playlist.emit({"error": str(e), "file_path": "", "play_path": ""})
            pass

    def convert_video_using_ffmpeg(self):
        for progress in run_ffmpeg_command(
                ['ffmpeg', '-i', self.full_file_path_dash, '-i', self.full_audio_path_dash, '-c:v', 'copy', '-c:a',
                 'copy',
                 self.full_file_path]):
            pass
        try:
            os.remove(self.full_file_path_dash)
            os.remove(self.full_audio_path_dash)
        except Exception as e:
            pass

    def convert_audio_using_ffmpeg(self, single_audio=True):
        progress_dict = {"type": self.type,
                         "is_killed": self.is_killed,
                         "file_path": self.video_download_path,
                         "play_path": self.full_file_path,
                         "complete_playlist": self.complete_playlist,
                         "counter": self.counter,
                         "title": self.title,
                         "total_size": humanbytes(self.pl_obj.filesize),
                         "downloaded": humanbytes(self.pl_obj.filesize)
                         }
        for progress_dict["progress"] in run_ffmpeg_command(
                ['ffmpeg', '-i', self.in_file_path, '-vn', self.full_file_path]):
            self.change_value.emit(progress_dict)
        if single_audio:
            self.finished.emit(progress_dict)
        try:
            os.remove(self.in_file_path)
        except Exception as e:
            pass

    def pause(self):
        self.is_paused = True

    def resume(self):
        self.is_paused = False

    def kill(self):
        self.is_killed = True


class FileSizeThread(QtCore.QThread):
    get_size_of_file = pyqtSignal(dict)

    def __init__(self, playlist_obj, parent=None):
        super(FileSizeThread, self).__init__(parent)
        self.playlist_obj = playlist_obj

    def run(self):
        size_dict = get_file_size_for_playlist(self.playlist_obj)
        self.get_size_of_file.emit(size_dict)


class FileSizeThreadSingleVideo(QtCore.QThread):
    get_size_of_single_video_file = pyqtSignal(str)

    def __init__(self, yt_obj, parent=None):
        super(FileSizeThreadSingleVideo, self).__init__(parent)
        self.yt_obj = yt_obj

    def run(self):
        size = get_file_size(self.yt_obj)
        self.get_size_of_single_video_file.emit(size)


class PlayThread(QtCore.QThread):
    get_stream_url = pyqtSignal(list)

    def __init__(self, video_url, parent=None):
        super(PlayThread, self).__init__(parent)
        self.video_url = video_url

    def run(self):
        from pytube import YouTube
        stream_url = [item.url for item in YouTube(self.video_url).streams.filter(progressive=True).order_by('resolution')]
        self.get_stream_url.emit(stream_url)
