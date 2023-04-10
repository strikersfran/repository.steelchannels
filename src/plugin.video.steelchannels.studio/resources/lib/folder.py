import os

def init_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)


def remove_dir(path):
    if os.path.exists(path):
        os.rmdir(path)
        return True


def remove_file(path):
    if os.path.exists(path):
        os.remove(path)
        return True