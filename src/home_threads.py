import requests
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QImage, QPixmap
from country_names_all import SERVER

UserAgent = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
Fields = "fields=videoId,title,videoThumbnails,lengthSeconds,author,viewCount,publishedText"


def get_live_server():
    try:
        default_server = list(SERVER.values())[0]
        for server in list(SERVER.values()):
            response = requests.get(server, UserAgent)
            if response.status_code in [200, 201]:
                default_server = server
                break
        return default_server
    except Exception as e:
        print(e)
        return list(SERVER.values())[0]


class HomeThreads(QtCore.QThread):
    home_results = pyqtSignal(list)
    server_change_error = pyqtSignal(str)

    def __init__(self, default_server, country_code, category, parent=None):
        super(HomeThreads, self).__init__(parent)
        self.country_code = country_code
        self.category = category
        self.end_point = default_server

    def get_end_points(self):
        self.end_point = get_live_server()

    def get_result(self):
        query = self.end_point + "/api/v1/" + self.category + "?" + Fields + "&" + "region=" + self.country_code

        return requests.get(query, UserAgent)

    def run(self):
        try:
            result = self.get_result()
            if result.status_code in [200, 201]:
                self.home_results.emit(result.json())
            else:
                self.get_end_points()
                result = self.get_result()
                self.home_results.emit(result.json())
        except Exception as e:
            print(e)
            self.server_change_error.emit("")


class PixMapLoadingThread(QtCore.QThread):
    finish = pyqtSignal(dict)
    progress = pyqtSignal(dict)
    finish_first_pixmap = pyqtSignal()

    def __init__(self, load_images, pixmap_cache, parent=None):
        super(PixMapLoadingThread, self).__init__(parent)
        self.load_images = load_images
        self.pixmap_cache = pixmap_cache

    def run(self):
        try:
            counter = 0
            for sno, urls in enumerate(self.load_images, 1):
                if self.pixmap_cache.get(urls):
                    self.progress.emit({"pixmap": self.pixmap_cache.get(urls), "progress": sno})
                else:
                    image = QImage()
                    image.loadFromData(requests.get(urls, UserAgent).content)
                    self.progress.emit({"pixmap": QPixmap(image), "progress": sno})

                if counter == 0:
                    self.finish_first_pixmap.emit()
                    counter += 1

        except Exception as e:
            print(str(e))
            self.finish.emit({"status": False, 'message': str(e)})
        self.finish.emit({"status": True, 'message': ""})


class CompleterThread(QtCore.QThread):
    get_completer_value = pyqtSignal(list)

    def __init__(self, default_server, text, region, parent=None):
        super(CompleterThread, self).__init__(parent)
        self.query = text
        self.region = region
        self.end_point = default_server

    # def get_end_points(self):
    #     self.end_point = get_live_server()

    # def run(self):
    #     try:
    #         result = self.get_result()
    #         if result.status_code in [200, 201]:
    #             self.get_completer_value.emit(result.json().get("suggestions"))
    #         else:
    #             self.get_end_points()
    #             result = self.get_result()
    #             self.get_completer_value.emit(result.json().get("suggestions"))
    #     except Exception as e:
    #         print(e)
    #         pass
    #
    # def get_result(self):
    #     query = self.end_point + "/api/v1/search/suggestions" + "?q=" + self.query
    #     return requests.get(query, UserAgent)

    def run(self):
        try:
            result = self.get_result_google_api()
            if result.status_code in [200, 201]:
                self.get_completer_value.emit([f"🔍  {x[0]}" for x in result.json()[1]])
            else:
                self.get_end_points()
                result = self.get_result_google_api()
                self.get_completer_value.emit([f"🔍  {x[0]}" for x in result.json()[1]])
        except Exception as e:
            print(e)
            pass

    def get_result(self):
        query = self.end_point + "/api/v1/search/suggestions" + "?q=" + self.query
        return requests.get(query, UserAgent)

    def get_result_google_api(self):
        query = "https://suggestqueries.google.com/complete/search?ds=yt&client=youtube&hjson=t&cp=1&format=5&alt=json&q=" + self.query
        return requests.get(query, UserAgent)


class SearchThreads(QtCore.QThread):
    search_results = pyqtSignal(list)

    def __init__(self, default_server, query, country_code, page, sort_by, parent=None):
        super(SearchThreads, self).__init__(parent)
        self.query = query
        self.country_code = country_code
        self.page = page
        self.search_type = "video"
        self.sort_by = sort_by
        self.end_point = default_server

    def get_end_points(self):
        self.end_point = get_live_server()

    def get_result(self):
        query = self.end_point + "/api/v1/search" + "?q=" + self.query + "&page=" + self.page + "&type=" + self.search_type + "&sort_by=" \
                + self.sort_by + "&" + "region=" + self.country_code + "&" + Fields

        return requests.get(query, UserAgent)

    def run(self):
        try:
            result = self.get_result()
            if result.status_code in [200, 201]:
                self.search_results.emit(result.json())
            else:
                self.get_end_points()
                result = self.get_result()
                self.search_results.emit(result.json())
        except Exception as e:
            print(e)
            pass

