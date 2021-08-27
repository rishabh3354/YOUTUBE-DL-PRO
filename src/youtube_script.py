import getpass
import os
from PyQt5.QtCore import QProcessEnvironment, QStandardPaths
from pytube import YouTube
from utils import get_time_format
import requests
import pytube.request
pytube.request.default_range_size = 1048576

ALL_VIDEO_RESOLUTIONS = {'144p': 'LD', '240p': 'LD', '360p': 'SD', '480p': 'SD',
                         '720p': 'HD', '1080p': 'FHD', '1440p': '2K', '2160p': '4K', '4320p': '8K'}

ALL_VIDEO_RESOLUTIONS_PLAYLIST = {'144p': 'LD', '240p': 'LD', '360p': 'SD', '480p': 'SD',
                                  '720p': 'HD', '1080p': 'FHD'}


def get_download_path(location,
                      thumbnail=False,
                      process_dash_stream=False,
                      download_video_path=False,
                      download_audio_path=False,
                      download_playlist_video_path=False,
                      download_playlist_audio_path=False,
                      ):
    try:
        if location:
            if thumbnail:
                location += '/YOUTUBE_DL/.thumbnails'
                os.makedirs(location, exist_ok=True)
            elif process_dash_stream:
                location += '/YOUTUBE_DL/.dash_stream'
                os.makedirs(location, exist_ok=True)
            elif download_video_path:
                location += '/YOUTUBE_DL/videos'
                os.makedirs(location, exist_ok=True)
            elif download_playlist_video_path:
                location += '/YOUTUBE_DL/playlist/videos'
                os.makedirs(location, exist_ok=True)
            elif download_playlist_audio_path:
                location += '/YOUTUBE_DL/playlist/audio'
                os.makedirs(location, exist_ok=True)
            elif download_audio_path:
                location += '/YOUTUBE_DL/audio'
                os.makedirs(location, exist_ok=True)
            else:
                location += '/Downloads'
            return location
        else:
            HOME = QProcessEnvironment().systemEnvironment().value('SNAP_REAL_HOME')
            if HOME != '':
                if thumbnail:
                    HOME += '/Downloads/YOUTUBE_DL/.thumbnails'
                    os.makedirs(HOME, exist_ok=True)
                elif process_dash_stream:
                    HOME += '/Downloads/YOUTUBE_DL/.dash_stream'
                    os.makedirs(HOME, exist_ok=True)
                elif download_video_path:
                    HOME += '/Downloads/YOUTUBE_DL/videos'
                    os.makedirs(HOME, exist_ok=True)
                elif download_audio_path:
                    HOME += '/Downloads/YOUTUBE_DL/audio'
                    os.makedirs(HOME, exist_ok=True)
                else:
                    HOME += '/Downloads'
            else:
                HOME = QStandardPaths.writableLocation(QStandardPaths.HomeLocation)
    except Exception as e:
        HOME = QProcessEnvironment().systemEnvironment().value('SNAP_REAL_HOME') + "/Downloads/YOUTUBE_DL/"

    return HOME


def get_initial_download_dir():
    try:
        download_path = QProcessEnvironment().systemEnvironment().value('SNAP_REAL_HOME')
        if download_path not in ["", None]:
            download_path = download_path + "/Downloads"
        else:
            username = getpass.getuser()
            if username not in ["", None]:
                download_path = f"/home/{username}/Downloads"
            else:
                download_path = os.environ['HOME']
                if download_path not in ["", None]:
                    download_path = download_path + "/Downloads"
                else:
                    download_path = os.path.expanduser("~") + "/Downloads"
        os.makedirs(download_path, exist_ok=True)
    except Exception as e:
        print("error in getting download path", str(e))
        return "/Downloads"
    return download_path


def get_initial_document_dir():
    try:
        download_path = QProcessEnvironment().systemEnvironment().value('SNAP_REAL_HOME')
        if download_path not in ["", None]:
            download_path = download_path + "/Documents"
        else:
            username = getpass.getuser()
            if username not in ["", None]:
                download_path = f"/home/{username}/Documents"
            else:
                download_path = os.environ['HOME']
                if download_path not in ["", None]:
                    download_path = download_path + "/Documents"
                else:
                    download_path = os.path.expanduser("~") + "/Documents"
        os.makedirs(download_path, exist_ok=True)
    except Exception as e:
        print("error in getting download path", str(e))
        return "/Documents"
    return download_path


def process_ytv(url, is_hd_plus, location):
    from helper import select_format_data
    from helper import safe_string

    context = dict()
    try:
        yt = YouTube(url)
        context["yt"] = yt
        context["title"] = str(yt.title)
        context["thumbnail_url"] = yt.thumbnail_url
        context["length"] = get_time_format(yt.length)
        context["stream_url"] = [item.url for item in yt.streams.filter(progressive=True).order_by('resolution')]
        context["audio_stream_url"] = [item.url for item in yt.streams.filter(only_audio=True).order_by('abr')]
        file_extension = '.jpg'
        context["quality_data"] = select_format_data(yt, is_hd_plus)
        context["channel"] = yt.author
        context["views"] = yt.views
        description = yt.description
        if description == "":
            context["description"] = "No description available!"
        else:
            context["description"] = yt.description
        image_url = yt.thumbnail_url
        r = requests.get(image_url)
        title = safe_string(yt.title)
        try:
            with open(f"{get_download_path(location, thumbnail=True)}/{title}{file_extension}", 'wb') as f:
                f.write(r.content)
        except Exception as e:
            pass
        context["status"] = True
    except Exception as e:
        context["status"] = False
        pass

    return context


def process_playlist(url, location):
    from pytube import Playlist
    context = dict()
    try:
        playlist = Playlist(url)
        context["playlist"] = playlist
        context["playlist_length"] = len(playlist.video_urls)
        context["playlist_videos"] = playlist.video_urls
        context["playlist_title"] = playlist.title
        if len(playlist.video_urls) > 0:
            first_video_in_playlist = playlist.video_urls[0]
            context["video_context"] = process_ytv(first_video_in_playlist, False, location)
            if context["video_context"].get("status", True) is False:
                context["status"] = False
            else:
                context["status"] = True

    except Exception as e:
        context["status"] = False
        pass
    return context
