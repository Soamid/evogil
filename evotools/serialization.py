from datetime import datetime


def get_current_time():
    return datetime.today().strftime("%Y-%m-%d.%H%M%S.%f")
