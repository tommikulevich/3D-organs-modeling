dicomDataDir= "C:/Users/Misio/Documents/GitHub/3D-organs-modeling/demo/input"
outputFolder= "C:/Users/Misio/Documents/GitHub/3D-organs-modeling/demo/output"

loadedNodeIDs = []
from DICOMLib import DICOMUtils
import tempfile
import time

slicer.app.testingEnabled() == True
slicer.util.selectModule("DICOM")
dicomBrowser = slicer.modules.DICOMWidget.browserWidget.dicomBrowser
dicomBrowser.importDirectory(dicomDataDir, dicomBrowser.ImportDirectoryAddLink)
dicomBrowser.waitForImportFinished()

db = slicer.dicomDatabase
patientList = db.patients()
studyList = db.studiesForPatient(patientList[0])
seriesList = db.seriesForStudy(studyList[0])
fileList = db.filesForSeries(seriesList[0])

patientUIDs = db.patients()
for patientUID in patientUIDs:
    loadedNodeIDs.extend(DICOMUtils.loadPatientByUID(patientUID))

slicer.util.selectModule("MONAILabel")

slicer.modules.MONAILabelWidget.onClickFetchInfo()

volumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
image_id = volumeNode.GetName()
##qt.QApplication.setOverrideCursor(qt.Qt.WaitCursor)

tmp_dir = slicer.util.tempDirectory("slicer-monai-label")
in_file = tempfile.NamedTemporaryFile(suffix=slicer.modules.MONAILabelWidget.file_ext, dir=tmp_dir).name
start = time.time()
slicer.util.saveNode(volumeNode, in_file)
session = False
if session:
    slicer.modules.MONAILabelWidget.current_sample["session_id"] = \
    slicer.modules.MONAILabelWidget.logic.create_session(in_file)["session_id"]
else:
    slicer.modules.MONAILabelWidget.logic.upload_image(in_file, image_id)
    slicer.modules.MONAILabelWidget.current_sample["session"] = False

slicer.modules.MONAILabelWidget._volumeNode = volumeNode
init_sample = True

if init_sample:
    slicer.modules.MONAILabelWidget.initSample({"id": image_id}, autosegment=False)

slicer.modules.MONAILabelWidget.updateGUIFromParameterNode()

slicer.modules.MONAILabelWidget.onClickSegmentation()

slicer.modules.MONAILabelWidget._segmentNode.CreateClosedSurfaceRepresentation()
slicer.app.layoutManager().threeDWidget(0).threeDView().resetFocalPoint()

segmentationNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLSegmentationNode")
# C:/Users/Misio/Documents/GitHub/3D-organs-modeling/demo/output = "D:/stl_testy_slicer"
slicer.modules.segmentations.logic().ExportSegmentsClosedSurfaceRepresentationToFiles(outputFolder, segmentationNode,
                                                                                      None, "STL", True, 1.0, False)
slicer.modules.segmentations.logic().ExportSegmentsClosedSurfaceRepresentationToFiles(outputFolder, segmentationNode,
                                                                                      None, "OBJ", True, 1.0, False)