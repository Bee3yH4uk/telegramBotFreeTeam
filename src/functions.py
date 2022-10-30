from datetime import datetime
from threading import Thread


def tprint(*args, **kwargs):
    print(f"[{datetime.strftime(datetime.now(), '%H:%M:%S')}]", *args, **kwargs)


def thread(my_func):
    def wrapper(*args, **kwargs):
        my_thread = Thread(target=my_func, args=args, kwargs=kwargs)
        my_thread.start()

    return wrapper

