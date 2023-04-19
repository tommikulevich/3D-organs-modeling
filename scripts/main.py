import sys
from PyQt5.QtWidgets import QApplication, QWidget, QPushButton, QFileDialog


class App(QWidget):

    def __init__(self):
        super().__init__()
        self.title = 'File Explorer'
        self.left = 10
        self.top = 10
        self.width = 320
        self.height = 200
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        button = QPushButton('Open File', self)
        button.setToolTip('Click to open the file explorer')
        button.move(100, 70)
        button.clicked.connect(self.showFileDialog)

        self.show()

    def showFileDialog(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        file_dialog.setNameFilter("Text files (*.txt)")
        if file_dialog.exec_():
            file_names = file_dialog.selectedFiles()
            print("Selected file directory:", file_names[0])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = App()
    sys.exit(app.exec_())
