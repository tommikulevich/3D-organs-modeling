from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PyQt5 import QtCore


class OrganDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.selected_piece = None
        self.init_ui()

    def init_ui(self):
        vbox = QVBoxLayout()

        label = QLabel("Choose your organ:")
        vbox.addWidget(label)
        self.setWindowFlags(self.windowFlags() & ~QtCore.Qt.WindowCloseButtonHint)

        queen_btn = QPushButton("All of them")
        queen_btn.clicked.connect(lambda: self.set_selected_piece("all"))
        vbox.addWidget(queen_btn)

        self.setLayout(vbox)
        self.setWindowTitle("Organ Dialog")
        self.setModal(True)

    def set_selected_piece(self, piece):
        self.selected_piece = piece
        self.accept()

    def get_selected(self):
        return self.selected_piece
