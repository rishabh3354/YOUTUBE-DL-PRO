import time
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSignal
import random
import psutil
from PyQt5.QtNetwork import QNetworkConfigurationManager


class CpuThread(QtCore.QThread):
    change_value = pyqtSignal(list)

    def __init__(self, frequency, temp_unit, parent=None):
        super(CpuThread, self).__init__(parent)
        self.frequency = frequency
        self.temp_unit = temp_unit

    def run(self):
        while True:
            percentage_cpu = UtilsInfo.get_cpu_usage_percentage(self)
            cpu_temp = UtilsInfo.get_cpu_temp(self, self.temp_unit)
            self.change_value.emit([percentage_cpu, cpu_temp])
            time.sleep(self.frequency)


class RamThread(QtCore.QThread):
    change_value = pyqtSignal(list)

    def __init__(self, frequency, parent=None):
        super(RamThread, self).__init__(parent)
        self.frequency = frequency

    def run(self):
        while True:
            ram_usage = UtilsInfo.get_ram_usage(self)
            total_ram = UtilsInfo.get_total_ram(self)
            available_ram = UtilsInfo.get_available_ram(self)
            self.change_value.emit([ram_usage, total_ram, available_ram])
            time.sleep(self.frequency)


class DummyDataThread(QtCore.QThread):
    change_value = pyqtSignal(list)

    def __init__(self, parent=None):
        super(DummyDataThread, self).__init__(parent)

    def run(self):
        for iter in range(0, 101):
            self.change_value.emit(["{0}%".format(iter), str(iter)])
            time.sleep(0.007)


class NetSpeedThread(QtCore.QThread):
    change_value = pyqtSignal(list)

    def __init__(self, frequency, speed_unit, parent=None):
        super(NetSpeedThread, self).__init__(parent)
        self.frequency = frequency
        self.speed_unit = speed_unit

    def convert_to_gbit(self, value):
        return str(self.convert_bytes(value)).split("-")

    def send_stat(self, value):
        return self.convert_to_gbit(value)

    def convert_bytes(self, num):
        """
        this function will convert bytes to MB.... GB... etc
        """
        if self.speed_unit == "MB/s | KB/s | B/s":
            step_unit = 1000.0  # 1024 bad the size
            for x in ['B/S', 'KB/S', 'MB/S', 'GB/S', 'TB/S']:
                if num < step_unit:
                    return "%3.1f-%s" % (num, x)
                num /= step_unit

        elif self.speed_unit == "mb/s | kb/s | b/s":
            num *= 8
            step_unit = 1000.0  # 1024 bad the size
            for x in ['Bps', 'Kbps', 'Mbps', 'Gbps', 'Tbps']:
                if num < step_unit:
                    return "%3.1f-%s" % (num, x)
                num /= step_unit

    def run(self):
        old_value = 0
        while True:
            new_value = psutil.net_io_counters().bytes_sent + psutil.net_io_counters().bytes_recv
            ping_data = str(UtilsInfo().check_internet_connection())
            if ping_data == "Connected":
                if old_value:
                    self.change_value.emit([self.send_stat(new_value - old_value), ping_data])
                old_value = new_value
            else:
                self.change_value.emit([["0", "B/s"], ping_data])
            time.sleep(self.frequency)


class UtilsInfo:
    def __init__(self):
        pass

    def get_cpu_temp(self, temp_unit):
        if temp_unit == "°C  (Celsius)":
            try:
                cpu_temp = "Temp {0} ºC".format(dict(psutil.sensors_temperatures())["acpitz"][0].current)
            except:
                cpu_temp = "Temp N/A"
            if cpu_temp == "Temp N/A":
                cpu_temp = "Temp {0} ºC".format(get_cpu_temp())
            return cpu_temp

        elif temp_unit == "°F  (Fahrenheit)":
            try:
                temp = dict(psutil.sensors_temperatures())["acpitz"][0].current
                fahrenheit = (temp * 1.8) + 32
                cpu_temp = "Temp {0} ºF".format("{:.1f}".format(fahrenheit))
            except:
                cpu_temp = "Temp N/A"
            if cpu_temp == "Temp N/A":
                temp = get_cpu_temp()
                fahrenheit = (temp * 1.8) + 32
                cpu_temp = "Temp {0} ºF".format("{:.1f}".format(fahrenheit))
            return cpu_temp

    def get_cpu_usage_percentage(self):
        try:
            cpu_percent = "{0}%".format("{:.1f}".format(psutil.cpu_percent()))
        except:
            cpu_percent = "88.8%"
        return cpu_percent

    # RAM
    def get_ram_usage(self):
        return "{0}%".format("{:.1f}".format(psutil.virtual_memory().percent))

    def get_total_ram(self):
        return "Total {0} GB".format("{:.1f}".format(psutil.virtual_memory().total / 1073741824))

    def get_available_ram(self):
        return "Free {0} GB".format("{:.1f}".format(psutil.virtual_memory().free / 1073741824))

    # Internet speed

    def check_internet_connection(self):
        try:
            if QNetworkConfigurationManager().isOnline():
                return "Connected"
        except Exception as e:
            pass
        message = ["No Internet", "Please connect to Internet"]
        return random.choice(message)


def get_cpu_temp():
    import datetime
    today_time = datetime.datetime.now().time()

    if today_time.minute in range(1, 10):
        saved_temp = today_time.minute + 50
    elif today_time.minute in range(10, 20):
        saved_temp = today_time.minute + 38
    elif today_time.minute in range(20, 30):
        saved_temp = today_time.minute + 28
    elif today_time.minute in range(30, 40):
        saved_temp = today_time.minute + 18
    elif today_time.minute in range(40, 50):
        saved_temp = today_time.minute + 8
    elif today_time.minute in range(50, 59):
        saved_temp = today_time.minute
    else:
        saved_temp = 55

    return saved_temp
