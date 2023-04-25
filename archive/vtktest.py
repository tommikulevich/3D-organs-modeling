# import vtk
#
# # Create a vtkOBJReader and set the file name
# reader = vtk.vtkOBJReader()
# reader.SetFileName("Example OBJ/segmentation_spleen_16.obj")
#
# # Update the reader to read the file and create a vtkPolyData object
# reader.Update()
#
# # Create a vtkPolyDataMapper and set its input to the vtkPolyData object
# mapper = vtk.vtkPolyDataMapper()
# mapper.SetInputData(reader.GetOutput())
#
# # Create a vtkActor and set its mapper to the vtkPolyDataMapper
# actor = vtk.vtkActor()
# actor.SetMapper(mapper)
#
# # Create a vtkRenderer, add the actor to it, and set its background color
# renderer = vtk.vtkRenderer()
# renderer.AddActor(actor)
# renderer.SetBackground(0.1, 0.2, 0.4)
#
# # Create a vtkRenderWindow and set its size
# renderWindow = vtk.vtkRenderWindow()
# renderWindow.SetSize(800, 800)

import vtk
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QSlider
from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QHBoxLayout


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # create a VTK rendering window
        self.vtk_widget = QVTKRenderWindowInteractor(self)
        self.ren = vtk.vtkRenderer()
        self.vtk_widget.GetRenderWindow().AddRenderer(self.ren)
        reader = vtk.vtkOBJReader()
        reader.SetFileName("Example OBJ/segmentation_spleen_16.obj")
        reader.Update()
        # create a PyQt5 layout and add the VTK widget to it
        button = QPushButton('Button', self)
        h_layout = QHBoxLayout()
        h_layout.addWidget(button)
        layout = QVBoxLayout()
        layout.addLayout(h_layout)

        layout.addWidget(self.vtk_widget)

        # create a central widget and set the layout
        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(reader.GetOutput())
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        renderer = vtk.vtkRenderer()
        renderer.AddActor(actor)
        renderer.SetBackground(0.1, 0.2, 0.4)
        # add a VTK actor to the rendering window
        self.ren.AddActor(actor)

        # start the VTK interactor
        self.vtk_widget.Initialize()
        self.vtk_widget.Start()


if __name__ == '__main__':
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec_()

# # Create a vtkRenderWindowInteractor and set its render window
# interactor = vtk.vtkRenderWindowInteractor()
# interactor.SetRenderWindow(renderWindow)
#
# # Add the renderer to the render window and render the scene
# renderWindow.AddRenderer(renderer)
# renderWindow.Render()
#
# # Start the interactor
# interactor.Start()