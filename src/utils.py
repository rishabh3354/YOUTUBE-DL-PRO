import time


def get_time_format(length):
    time_str = str(time.strftime('%H:%M:%S', time.gmtime(length)))
    if time_str[0:2] == '00':
        return "{0}m:{1}s".format(time_str[3:5], time_str[6:])
    else:
        return "{0}h:{1}m:{0}s".format(time_str[0:2], time_str[3:5], time_str[6:])
