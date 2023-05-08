import os
import sys


def add(library_paths=None):
    if library_paths is None:
        library_paths = [os.path.abspath(path) for path in os.getenv("LibraryPaths", "").split(os.pathsep)]

    if sys.version_info < (3, 8) or sys.platform != 'win32':
        return

    for path in library_paths:
        if not os.path.exists(path):
            continue
        os.add_dll_directory(path)


if __name__ == "__main__":
    add()
