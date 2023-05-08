import os
import json
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from PySide2.QtCore import QFile, Signal
from PySide2.QtGui import QIcon
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import QApplication, QAction, QStyle, QFileDialog, QLineEdit, QLabel, QProgressBar
from PySide2.QtWidgets import QPushButton, QMainWindow, QMessageBox

import open3d as o3d
from open3d.visualization import gui

from mainAlgorithm import MainAlgorithm
from organDialog import OrganDialog


class MainWindow(QMainWindow):
    isReady = Signal()

    def __init__(self):
        super().__init__()
        uiFile = QFile('ui/main_window_qt.ui')
        uiFile.open(QFile.ReadOnly)
        ui = QUiLoader().load(uiFile, None)  # Loading ui from .ui file
        uiFile.close()

        self.setCentralWidget(ui)
        self.setWindowTitle("MSN Project")
        self.setWindowIcon(QIcon(QApplication.instance().style().standardPixmap(QStyle.SP_FileDialogListView)))

        # Finding and configuring window elements
        self.info_action = self.findChild(QAction, 'infoAction')
        self.info_action.triggered.connect(self.project_info)
        self.exit_action = self.findChild(QAction, 'exitAction')
        self.exit_action.triggered.connect(self.close)

        self.change_input_button = self.findChild(QPushButton, 'changeInputButton')
        self.change_input_button.clicked.connect(self.change_input_dir)
        self.change_output_button = self.findChild(QPushButton, 'changeOutputButton')
        self.change_output_button.clicked.connect(self.change_output_dir)

        self.input_line_edit = self.findChild(QLineEdit, 'inputLineEdit')
        self.input_line_edit.setText(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo/input').replace('\\', '/'))
        self.input_line_edit.setCursorPosition(0)
        self.output_line_edit = self.findChild(QLineEdit, 'outputLineEdit')
        self.output_line_edit.setText(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'demo/output').replace('\\', '/'))
        self.output_line_edit.setCursorPosition(0)

        self.start_button = self.findChild(QPushButton, 'startButton')
        self.start_button.clicked.connect(self.start_algorithm)
        self.show_button = self.findChild(QPushButton, 'showButton')
        self.show_button.clicked.connect(self.choose_window)

        self.status_label = self.findChild(QLabel, 'statusLabel')
        self.status_bar = self.findChild(QProgressBar, 'statusBar')
        self.status_bar.setVisible(False)

        self.algorithm = MainAlgorithm()  # Create algorithm object
        self.isReady.connect(self.readyProcedure)

        # Other initial operations
        self.save_config()

    @staticmethod
    def project_info():
        msg = QMessageBox()
        msg.setWindowIcon(QIcon(QApplication.instance().style().standardPixmap(QStyle.SP_FileDialogInfoView)))
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Here you will find a short tutorial how to use this program...")
        msg.setWindowTitle("Project Info | Help")
        msg.exec_()

    def change_input_dir(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Choose input folder")

        # TO-DO: add folder validation

        if folder_path:
            self.save_config()
            self.input_line_edit.setText(folder_path)
            self.input_line_edit.setCursorPosition(0)
            self.status_label.setText("Info: Input folder successfully changed!")

    def change_output_dir(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Choose output folder")

        # TO-DO: add folder validation

        if folder_path:
            self.save_config()
            self.output_line_edit.setText(folder_path)
            self.output_line_edit.setCursorPosition(0)
            self.status_label.setText("Info: Output folder successfully changed!")

    def get_input_dir(self):
        return self.input_line_edit.text()

    def get_output_dir(self):
        return self.output_line_edit.text()

    def save_config(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/config.json").replace('\\', '/')

        # Update config
        config = {
            "paths": {
                "input": self.get_input_dir(),
                "output": self.get_output_dir()
            }
        }

        # Write config to file
        with open(config_path, "w") as file:
            json.dump(config, file, indent=4)

    def get_config(self):
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/config.json").replace('\\', '/')

        # Check if the config file exists
        if not os.path.isfile(config_path):
            self.status_label.setText("Info: Config file not found or not selected!")
            return

        # Open config file
        with open(config_path, "r") as file:
            config = json.load(file)

        # Get paths
        paths = config.get("paths", {})
        input_path = paths.get("input", {})
        output_path = paths.get("output", {})

        return input_path, output_path

    def start_algorithm(self):
        executor = ProcessPoolExecutor(max_workers=multiprocessing.cpu_count())
        future = executor.submit(self.algorithm.startAlgorithm, self.get_input_dir(), self.get_output_dir())
        future.add_done_callback(self.endAlgorithm)

        # Experimental (need to change)
        self.status_label.setText("Info: Algorithm started...")
        if self.status_bar.isVisible():
            self.status_bar.setVisible(False)
        else:
            self.status_bar.setVisible(True)

    def endAlgorithm(self, future):
        self.isReady.emit()

    def readyProcedure(self):
        # Need to off status_bar and print something in status_label
        print("Algorithm ended...")

    @staticmethod
    def show_result(folder_path):
        geometries = []

        for filename in os.listdir(folder_path):
            if filename.lower().endswith(".obj"):   # For showing all .obj in the folder
                file_path = os.path.join(folder_path, filename)

                mesh = o3d.io.read_triangle_mesh(file_path)
                mesh.compute_vertex_normals()
                geometries.append(mesh)

        # TO-DO: fix errors when multiple windows are shown and user tries to close one of it
        # TO-DO (optional): create separate window using 'o3d.visualization.gui.Application' and
        #                   'o3d.visualization.gui.Window' classes (for visualization configuration)
        o3d.visualization.draw_geometries(geometries)

    def choose_window(self):
        organDialog = OrganDialog()

        if organDialog.exec_():
            selected = organDialog.get_selected()

            # TO-DO: add another options
            if selected == "all":
                results = self.get_output_dir()
                self.show_result(results)
            else:
                pass
