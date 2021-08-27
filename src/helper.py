import datetime
import json
import os
import random
from PyQt5.QtNetwork import QNetworkConfigurationManager
from utils import get_time_format
from youtube_script import get_download_path, ALL_VIDEO_RESOLUTIONS, ALL_VIDEO_RESOLUTIONS_PLAYLIST
import subprocess
import re
from typing import Iterator


FREQUENCY_MAPPER = {1: 0.2, 2: 0.4, 3: 0.6, 4: 1.0, 5: 2.0, 6: 3.0}

DUR_REGEX = re.compile(
    r"Duration: (?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\.(?P<ms>\d{2})"
)
TIME_REGEX = re.compile(
    r"out_time=(?P<hour>\d{2}):(?P<min>\d{2}):(?P<sec>\d{2})\.(?P<ms>\d{2})"
)


def save_download_info(yt, yt_obj, download_path, file_path, location_path, download_type):
    try:
        video_info_list = list()
        video_info = dict()
        video_info["download_type"] = download_type
        video_info["title_show"] = yt_obj.title
        video_info["title_safe"] = safe_string(yt_obj.title)
        video_info["length"] = get_time_format(yt.length)
        video_info["author"] = yt.author
        video_info["url"] = yt.watch_url
        video_info["size"] = humanbytes(yt_obj.filesize)
        video_info["resolution"] = yt_obj.resolution
        video_info["type"] = yt_obj.type
        if download_type in ["audio", "playlist_audio"]:
            video_info["fps"] = "-"
        else:
            video_info["fps"] = yt_obj.fps
        video_info["subtype"] = yt_obj.subtype
        video_info["download_date"] = datetime.datetime.strftime(datetime.datetime.now(), '%d %b %Y')
        video_info["download_time"] = datetime.datetime.strftime(datetime.datetime.now(), "%H:%M")
        video_info["download_path"] = download_path
        video_info["sort_param"] = str(datetime.datetime.now())
        video_info["file_path"] = file_path
        video_info["thumbnail_path"] = f"{location_path}/YOUTUBE_DL/.thumbnails/{safe_string(yt_obj.title)}.jpg"

        video_info_list.append(video_info.copy())
        download_data_dir = f'{location_path}/YOUTUBE_DL/.downloads'
        prev_saved_data = get_local_download_data(location_path)

        if prev_saved_data:
            prev_saved_data.extend(video_info_list)
            data = json.dumps(prev_saved_data)
        else:
            data = json.dumps(video_info_list)

        os.makedirs(download_data_dir, exist_ok=True)
        file_name = f'{download_data_dir}/download_data.json'
        with open(file_name, "w+") as file:
            file.write(data)

    except Exception as ee:
        pass


def save_after_delete(data, location_path):
    try:
        data = json.dumps(data)
        download_data_dir = f'{location_path}/YOUTUBE_DL/.downloads'
        os.makedirs(download_data_dir, exist_ok=True)
        file_name = f'{download_data_dir}/download_data.json'
        with open(file_name, "w+") as file:
            file.write(data)
    except Exception as e:
        pass


def get_local_download_data(location_path):
    download_data_dir = f'{location_path}/YOUTUBE_DL/.downloads'
    prev_saved_data = []
    try:
        os.makedirs(download_data_dir, exist_ok=True)
        file_name = f'{download_data_dir}/download_data.json'
        user_data_file = open(file_name, "r+")
        data = user_data_file.read()
        prev_saved_data = json.loads(data)
    except Exception as error:
        pass

    return prev_saved_data


def get_file_size(self):
    try:
        quality = (str(self.ui.select_quality_obj_2.currentText()).split(" ")[0]).lower()
        formats = (str(self.ui.select_format_obj_2.currentText()).split(" ")[2]).lower()
        fps = int(str(self.ui.select_fps_obj_2.currentText()).split(" ")[0])
        video_size = 0
        audio_file = 0

        if formats == "mp3":
            yt = self.yt.streams.filter(only_audio=True, subtype='mp4').order_by("abr")
            if yt:
                video_size = yt.last().filesize
        else:
            yt = self.yt.streams.filter(file_extension=formats, fps=fps, resolution=quality)
            if yt:
                video_size = yt.first().filesize
            else:
                yt = self.yt.streams.filter(file_extension=formats, resolution=quality)

                if yt:
                    video_size = yt.first().filesize
                else:
                    yt = self.yt.streams.filter(resolution=quality)

                    if yt:
                        video_size = yt.first().filesize
            yt = self.yt.streams.filter(only_audio=True, subtype='mp4').order_by("abr")
            if yt:
                audio_file = yt.last().filesize

            yt = self.yt.streams.filter(only_audio=True, subtype='mp4').order_by("abr")
            if yt:
                audio_file = yt.last().filesize

        if video_size == 0:
            video_size = ""
        else:
            if formats == "mp3":
                video_size = f"Total: {str(humanbytes(video_size))}  ( Audio: {str(humanbytes(video_size))})"
            else:
                video_size = f"Total: {str(humanbytes(video_size + audio_file))}  ( Video: {str(humanbytes(video_size))} | Audio: {str(humanbytes(audio_file))} )"
    except Exception as e:
        return None

    return video_size


def get_file_size_for_playlist(self):
    response_dict = {}
    try:
        all_yt_playlist_obj = self.total_obj
        video_type = self.ui.select_type_playlist_2.currentText()
        formats = (str(self.ui.select_type_playlist_2.currentText()).split(" ")[2]).lower()
        selected_video = safe_string((self.ui.select_videos_playlist_2.currentText()))
        selected_video_index = self.ui.select_videos_playlist_2.currentIndex()
        quality = (str(self.ui.select_quality_playlist_2.currentText()).split(" ")[0]).lower()

        video_size = 0
        video_length = 0
        audio_file = 0

        if video_type == "AUDIO - MP3":
            if selected_video != "select-all":
                yt_obj = all_yt_playlist_obj[selected_video_index - 1]
                video_length = yt_obj.length
                yt = yt_obj.streams.filter(only_audio=True, subtype='mp4').order_by("abr")
                if yt:
                    video_size = yt.last().filesize
            else:
                sum_of_all_files = 0
                sum_of_all_length = 0
                for item in all_yt_playlist_obj:
                    sum_of_all_length += item.length
                    video_length = sum_of_all_length
                    yt = item.streams.filter(only_audio=True, subtype='mp4').order_by("abr")
                    if yt:
                        size = yt.last().filesize
                        sum_of_all_files += size
                        video_size = sum_of_all_files

        else:
            if selected_video != "select-all":
                yt_obj = all_yt_playlist_obj[selected_video_index - 1]
                video_length = yt_obj.length
                yt = yt_obj.streams.filter(resolution=quality, file_extension=formats)

                if len(yt) == 0:
                    for item_formats in ['mp4', 'webm']:
                        yt = yt_obj.streams.filter(resolution=quality, file_extension=item_formats)
                        if yt:
                            break
                    if len(yt) == 0:
                        for item_quality in list(ALL_VIDEO_RESOLUTIONS_PLAYLIST.keys()):
                            yt = yt_obj.streams.filter(resolution=item_quality)
                            if yt:
                                break
                        if len(yt) == 0:
                            yt = yt.streams.filter().first()
                if yt:
                    video_size = yt.first().filesize

                yt = yt_obj.streams.filter(only_audio=True, subtype='mp4').order_by("abr")
                if yt:
                    audio_file = yt.last().filesize
            else:
                sum_of_all_files = 0
                sum_of_all_audio = 0
                sum_of_all_length = 0
                for item in all_yt_playlist_obj:
                    sum_of_all_length += item.length
                    video_length = sum_of_all_length
                    yt = item.streams.filter(resolution=quality, file_extension=formats)

                    if len(yt) == 0:
                        for item_formats in ['mp4', 'webm']:
                            yt = item.streams.filter(resolution=quality, file_extension=item_formats)
                            if yt:
                                break
                        if len(yt) == 0:
                            for item_quality in list(ALL_VIDEO_RESOLUTIONS_PLAYLIST.keys()):
                                yt = item.streams.filter(resolution=item_quality)
                                if yt:
                                    break
                            if len(yt) == 0:
                                yt = yt.streams.filter().first()

                    if yt:
                        size = yt.first().filesize
                        sum_of_all_files += size
                        video_size = sum_of_all_files

                for item in all_yt_playlist_obj:
                    yt = item.streams.filter(only_audio=True, subtype='mp4').order_by("abr")
                    if yt:
                        sum_of_all_audio += yt.last().filesize
                        audio_file = sum_of_all_audio

        if video_size == 0 or video_length == 0:
            video_size = ""
            video_length = ""
        else:
            if video_type == "AUDIO - MP3":
                video_size = f"Total: {str(humanbytes(video_size))}  ( Audio: {str(humanbytes(video_size))})"
            else:
                video_size = f"Total: {str(humanbytes(video_size + audio_file))}  ( Video: {str(humanbytes(video_size))} | Audio: {str(humanbytes(audio_file))} )"
            video_length = str(get_time_format(video_length))

    except Exception as e:
        response_dict["video_size"] = "N/A"
        response_dict["video_length"] = "N/A"
        return response_dict

    response_dict["video_size"] = video_size
    response_dict["video_length"] = video_length

    return response_dict


def safe_string(input_str):
    from slugify import slugify
    return slugify(input_str)


def process_html_data(yt_data, location):
    title = yt_data.get("title")
    thumbnail_url = yt_data.get("thumbnail_url")
    length = yt_data.get("length")
    thumbnail_image_path = get_thumbnail_path_from_local(title, thumbnail_url, location)
    return thumbnail_image_path, title, length


def process_html_data_playlist(yt_playlist_data, location):
    yt_video_data = yt_playlist_data.get("video_context")
    playlist_title = yt_playlist_data.get("playlist_title")
    thumbnail_url = yt_video_data.get("thumbnail_url")
    total_videos = yt_playlist_data.get("playlist_length")
    thumbnail_image_path = get_thumbnail_path_from_local(yt_video_data.get("title"), thumbnail_url, location)

    return thumbnail_image_path, playlist_title, str(total_videos)


def get_thumbnail_path_from_local(title, thumbnail_url, location):
    image_file_path = None
    title = safe_string(title)
    try:
        file_extension = os.path.splitext(thumbnail_url)[1]
        if "?" in file_extension:
            file_extension = str(file_extension.split("?")[0])
        image_file_path = f'{get_download_path(location, thumbnail=True)}/{title}{file_extension}'
    except Exception as ee:
        pass

    return image_file_path


def select_format_data(yt, is_hd_plus):
    all_quality = list()
    all_fps = list()

    if not is_hd_plus:
        res_fps_list = [x.__dict__ for x in yt.streams.filter(progressive=True).order_by('resolution')]
        all_format = ['VIDEO - MP4']
    else:
        res_fps_list = [x.__dict__ for x in yt.streams.order_by('resolution')]
        all_format = ['VIDEO - MP4', 'VIDEO - WEBM', 'AUDIO - MP3']

    for data in res_fps_list:
        if data.get("resolution"):
            raw_res = data.get("resolution")
            res = f"{raw_res} ({ALL_VIDEO_RESOLUTIONS.get(raw_res)})"
            if res not in all_quality:
                all_quality.append(res)
        if data.get("fps"):
            raw_fps = data.get("fps")
            fps = f"{raw_fps} FPS"
            if fps not in all_fps:
                all_fps.append(fps)

    return list(all_format), list(all_quality), list(all_fps)


def check_internet_connection():
    try:
        if QNetworkConfigurationManager().isOnline():
            return True
    except Exception as e:
        pass
    return False


def check_internet_connection_for_net_speed():
    try:
        if QNetworkConfigurationManager().isOnline():
            return "Connected"
    except Exception as e:
        pass
    message = ["No Internet", "Please connect to Internet"]
    return random.choice(message)


def humanbytes(byte_str):

    B = float(byte_str)
    KB = float(1024)
    MB = float(KB ** 2)
    GB = float(KB ** 3)
    TB = float(KB ** 4)

    if B < KB:
        return '{0} {1}'.format(B, 'B')
    elif KB <= B < MB:
        return '{0:.2f} KB'.format(B / KB)
    elif MB <= B < GB:
        return '{0:.2f} MB'.format(B / MB)
    elif GB <= B < TB:
        return '{0:.2f} GB'.format(B / GB)
    elif TB <= B:
        return '{0:.2f} TB'.format(B / TB)


def to_ms(s=None, des=None, **kwargs) -> float:
    if s:
        hour = int(s[0:2])
        minute = int(s[3:5])
        sec = int(s[6:8])
        ms = int(s[10:11])
    else:
        hour = int(kwargs.get("hour", 0))
        minute = int(kwargs.get("min", 0))
        sec = int(kwargs.get("sec", 0))
        ms = int(kwargs.get("ms", 0))

    result = (hour * 60 * 60 * 1000) + (minute * 60 * 1000) + (sec * 1000) + ms
    if des and isinstance(des, int):
        return round(result, des)
    return result


def run_ffmpeg_command(cmd: "list[str]") -> Iterator[int]:
    """
    Run an ffmpeg command, trying to capture the process output and calculate
    the duration / progress.
    Yields the progress in percent.
    """
    total_dur = None

    cmd_with_progress = [cmd[0]] + ["-progress", "-", "-nostats"] + cmd[1:]

    stderr = []

    p = subprocess.Popen(
        cmd_with_progress,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=False,
    )

    while True:
        line = p.stdout.readline().decode("utf8", errors="replace").strip()
        if line == "" and p.poll() is not None:
            break
        stderr.append(line.strip())

        if not total_dur and DUR_REGEX.search(line):
            total_dur = DUR_REGEX.search(line).groupdict()
            total_dur = to_ms(**total_dur)
            continue
        if total_dur:
            result = TIME_REGEX.search(line)
            if result:
                elapsed_time = to_ms(**result.groupdict())
                yield int(elapsed_time / total_dur * 100)

    if p.returncode != 0:
        raise RuntimeError(
            "Error running command {}: {}".format(cmd, str("\n".join(stderr)))
        )

    yield 100

    # video_stream = ffmpeg.input('audio.mp4')
    # audio_stream = ffmpeg.input('video.mp4')
    # ffmpeg.output(audio_stream, video_stream, 'out.mp4').run_async()


def check_default_location(path):
    try:
        home = str(path).split("/")[1]
        if home == "home":
            return True
        else:
            return False
    except Exception as e:
        return False


def get_all_playlist_quality(playlist_all_obj, is_hd_plus_playlist, self):
    all_quality = list()
    all_format = list()
    res_fps_list = []
    response_dict = {}

    if not is_hd_plus_playlist:
        for yt in playlist_all_obj:
            res_fps_list.append([x.__dict__ for x in yt.streams.filter(progressive=True).order_by('resolution')])
            all_format = ['VIDEO - MP4']
    else:
        counter = 1
        for yt in playlist_all_obj:
            res_fps_list.append([x.__dict__ for x in yt.streams.order_by('resolution')])
            self.partial_progress.emit({"counter": counter})
            counter += 1
            all_format = ['VIDEO - MP4', 'VIDEO - WEBM', 'AUDIO - MP3']

    for data in res_fps_list:
        for item in data:
            if item.get("resolution"):
                raw_res = item.get("resolution")
                if raw_res in ["1440p", "2160p", "4320p"]:
                    continue
                res = f"{raw_res} ({ALL_VIDEO_RESOLUTIONS_PLAYLIST.get(raw_res)})"
                if res not in all_quality:
                    all_quality.append(res)

    response_dict["all_format"] = list(all_format)
    response_dict["all_quality"] = list(all_quality)

    return response_dict


def get_stream_quality(stream_url, stream_quality, audio_type=False):
    if audio_type:
        try:
            if len(stream_url) <= 4:
                stream = stream_url[stream_quality]
            elif len(stream_url) <= 3:
                stream = stream_url[2]
            elif len(stream_url) <= 2:
                stream = stream_url[1]
            else:
                stream = stream_url[0]
        except Exception as e:
            print(e)
            stream = stream_url[0]
    else:
        try:
            if len(stream_url) <= 3:
                stream = stream_url[stream_quality]
            elif len(stream_url) <= 2:
                stream = stream_url[1]
            else:
                stream = stream_url[0]
        except Exception as e:
            print(e)
            stream = stream_url[-1]

    return stream


def get_downloaded_data_filter(data, filter_type):
    if filter_type == "all_files":
        return data
    else:
        return [item_dict for item_dict in data if item_dict.get("download_type") == filter_type]
