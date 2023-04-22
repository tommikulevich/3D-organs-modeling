import open3d as o3d
import sys
from PyQt5.QtGui import QWindow
from PyQt5.QtWidgets import QApplication, QTextEdit, QVBoxLayout, QHBoxLayout, QAction
from PyQt5.QtWidgets import QWidget, QLineEdit, QListWidget
from PyQt5.QtWidgets import QPushButton, QLabel, QMainWindow, QCheckBox, QMessageBox
from organdialog import Dialog
from open3d.visualization import gui
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setGeometry(300, 300, 400, 400)

        # dodanie górnej belki menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu('Window')
        exit_action = QAction('Close', self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        help_menu = menubar.addMenu("Help")
        monai_action = QAction("MONAI SERVER", self)
        monai_action.triggered.connect(self.monai_help)
        help_menu.addAction(monai_action)


        # dodanie przycisków
        self.button = QPushButton("Start MONAI", self)
        self.button.setGeometry(100, 100, 200, 50)
        self.button.clicked.connect(self.monai)
        self.button1 = QPushButton("Show 3D", self)
        self.button1.setGeometry(100, 250, 200, 50)
        self.button1.clicked.connect(self.pop_up_window)


    def monai_help(self):
        msg = QMessageBox()
        msg.setText("Later")
        msg.exec_()
    def monai(self):
        pass
    def show_new_window(self):
        mesh = o3d.io.read_triangle_mesh("Example OBJ/segmentation_spleen_16.obj")
        mesh.compute_vertex_normals()
        vertices = mesh.vertices
        vertex_colors = mesh.vertex_colors
        o3d.visualization.draw_geometries([mesh])


    def pop_up_window(self):
        app = QApplication.instance()
        if not app:
            app = QApplication([])
        dialog = Dialog()
        if dialog.exec_():
            selected = dialog.get_selected()
            if selected == "all":
                self.show_new_window()


if __name__ == "__main__":
    app = QApplication.instance()
    if (app is None):
        app = QApplication(sys.argv)
    w = MainWindow()
    w.show()
    app.exec_()