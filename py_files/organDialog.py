from PySide2.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QCheckBox
from PySide2 import QtCore


class OrganDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.selected_pieces = []
        self.init_ui()

    def init_ui(self):
        vbox = QVBoxLayout()

        label = QLabel("Choose your organ:")
        vbox.addWidget(label)

        all_radio = QCheckBox("All")
        vbox.addWidget(all_radio)

        right_kidney_radio = QCheckBox("Right kidney")
        vbox.addWidget(right_kidney_radio)

        left_kidney_radio = QCheckBox("Left kidney")
        vbox.addWidget(left_kidney_radio)

        aorta_radio = QCheckBox("Aorta")
        vbox.addWidget(aorta_radio)

        cava_radio = QCheckBox("Vena cava")
        vbox.addWidget(cava_radio)

        liver_radio = QCheckBox("Liver")
        vbox.addWidget(liver_radio)

        spleen_radio = QCheckBox("Spleen")
        vbox.addWidget(spleen_radio)

        stomach_radio = QCheckBox("Stomach")
        vbox.addWidget(stomach_radio)

        all_radio.stateChanged.connect(lambda state: self.update_checkboxes_state())
        # all_radio.setChecked(True)  # Set the "All" checkbox as checked by default

        all_btn = QPushButton("Show result")
        all_btn.clicked.connect(self.get_selected_pieces)
        vbox.addWidget(all_btn)

        self.setLayout(vbox)
        self.setWindowTitle("Organ Dialog")
        self.setModal(True)

    def get_selected_pieces(self):
        self.selected_pieces = []
        for child in self.children():
            if isinstance(child, QCheckBox) and child.isChecked():
                if child.text() != "All":
                    self.selected_pieces.append(child.text().lower() + ".stl")
                else:
                    self.selected_pieces.append(child.text().lower())
        self.accept()

    def update_checkboxes_state(self):
        for child in self.children():
            if isinstance(child, QCheckBox):
                if child.text() == "All":
                    if child.isChecked():
                        setting = False
                    else:
                        setting = True
                else:
                    child.setChecked(False)
                    child.setEnabled(setting)

    def get_selected(self):
        return self.selected_pieces
