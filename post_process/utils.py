from html.parser import HTMLParser
from datetime import datetime
import numpy as np
import builtins

def progress_bar(prefix = '@', decimals = 1, length = 100, fill = '█', end = "\r"):
    def decorator(func):
        # I'm evil
        # def patched_print(*args, **kwargs):
        #     builtins.print()
        #     builtins.print(*args, **kwargs)
        #     builtins.print()
        #
        # print = patched_print

        def decorated(*args, **kwargs):

            progress_generator = func(*args, **kwargs) 
            try:
                while True:
                    progress = next(progress_generator)
                    percent = (f"{100*progress:.{decimals}f}")
                    filled = int(length * progress)
                    bar = fill * filled + '-' * (length - filled)

                    builtins.print(f"{prefix} |{bar}| {percent}%", end=end)

            except StopIteration as result:
                print = builtins.print
                return result.value
            except Exception as e:
                print = builtins.print
                raise e

        return decorated
    return decorator


class MLStripper(HTMLParser):
    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs= True
        self.fed = []
        
    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()

def change_key(old_key, new_key, dictionary):
    if old_key not in dictionary:
        raise Exception("key does not exist")

    dictionary[new_key] = dictionary.pop(old_key)
    return dictionary

def filter_keys(wanted_keys, dictionary):
    return {k: dictionary[k] for k in wanted_keys if k in dictionary}

def get_timestamp():
    return datetime.now().strftime("%d-%m-%Y_%I-%M-%S_%p")

def pad_to_dense(M, value=0):
    """Appends the minimal required amount of zeroes at the end of each 
     array in the jagged array `M`, such that `M` looses its jagedness."""

    maxlen = max(len(r) for r in M)

    padded = np.empty((len(M), maxlen))
    padded.fill(value)

    for row, values in enumerate(M):
        padded[row, :len(values)] = values

    return padded
