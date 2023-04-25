import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog
from PyQt5.QtCore import QDir


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'File Explorer'
        self.left = 100
        self.top = 100
        self.width = 320
        self.height = 200
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        button = QPushButton('Open Directory', self)
        button.setToolTip('Click to open the file explorer')
        button.move(100, 70)
        button.clicked.connect(self.showFileDialog)

        self.show()

    def showFileDialog(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.Directory)
        if file_dialog.exec_():
            dir_path = file_dialog.selectedFiles()[0]
            file_format = "json"  # Replace with your desired file format
            contains_subdirs = self.containsSubdirs(dir_path)
            contains_wrong_format = self.containsWrongFormat(dir_path, file_format)
            if not contains_subdirs and not contains_wrong_format:
                print(f"The directory '{dir_path}' contains only files with format '.{file_format}'.")
            else:
                print(f"The directory '{dir_path}' does not meet the requirements.")

    def containsSubdirs(self, dir_path):
        dir = QDir(dir_path)
        for entry in dir.entryInfoList():
            if entry.isDir() and entry.fileName() not in [".", ".."]:
                return True
        return False

    def containsWrongFormat(self, dir_path, file_format):
        dir = QDir(dir_path)
        for entry in dir.entryInfoList():
            if entry.isDir() and entry.fileName() not in [".", ".."]:
                # Recursively check subdirectories
                sub_dir_path = entry.absoluteFilePath()
                if self.containsWrongFormat(sub_dir_path, file_format):
                    return True
            elif entry.isFile() and entry.suffix() != file_format:
                return True
        return False


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
