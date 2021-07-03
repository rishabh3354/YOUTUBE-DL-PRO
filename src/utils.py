import time
from PyQt5 import QtGui
from country_names_all import ALPHA2_CODES, COUNTRY_NAME, SERVER_LIST, SERVER_NAME


def get_time_format(length):
    time_str = str(time.strftime('%H:%M:%S', time.gmtime(length)))
    if time_str[0:2] == '00':
        return "{0}m:{1}s".format(time_str[3:5], time_str[6:])
    else:
        return "{0}h:{1}m:{0}s".format(time_str[0:2], time_str[3:5], time_str[6:])


def human_format(num):
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    # add more suffixes if you need them
    return '%.2f%s' % (num, ['', 'K', 'M', 'G', 'T', 'P'][magnitude])


def get_country_name_with_code_dict():
    return dict(zip(COUNTRY_NAME, ALPHA2_CODES))


def get_country_all():
    return COUNTRY_NAME


def set_all_countries_icons(self):
    for index, name in enumerate(ALPHA2_CODES):
        file_name = f":/myresource/resource/{name.lower()}.png"
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(file_name), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.youtube_setting_ui.ui.country.setItemIcon(index, icon)


def get_all_server_name_dict():
    return dict(zip(SERVER_NAME, SERVER_LIST))
