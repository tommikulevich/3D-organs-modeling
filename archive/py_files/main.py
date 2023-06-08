import sys

from PySide2.QtWidgets import QApplication
from mainWindow import MainWindow

# IMPORTANT!!!
# Don't touch!!!
import subprocess
import sys

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    app.exec_()