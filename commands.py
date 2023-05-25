dicomDataDir= "Q:/PG/Coding/Projekt Grupowy/MSN/demo/input"
outputFolder= "Q:/PG/Coding/Projekt Grupowy/MSN/demo/output"

loadedNodeIDs = []
from DICOMLib import DICOMUtils
import tempfile
import time
import json
import os

slicer.app.testingEnabled() == True
slicer.util.selectModule("DICOM")
dicomBrowser = slicer.modules.DICOMWidget.browserWidget.dicomBrowser

# ----- Loading data -----
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/config.json").replace('\\', '/')
with open(config_path, 'r') as f:
    config = json.load(f)

config['status'] = "load_data"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)
# -------------------------

dicomBrowser.importDirectory(dicomDataDir, dicomBrowser.ImportDirectoryAddLink)
dicomBrowser.waitForImportFinished()

db = slicer.dicomDatabase
patientList = db.patients()
studyList = db.studiesForPatient(patientList[0])
seriesList = db.seriesForStudy(studyList[0])
fileList = db.filesForSeries(seriesList[0])

# ----- Loading patients -----
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/config.json").replace('\\', '/')
with open(config_path, 'r') as f:
    config = json.load(f)

config['status'] = "load_patients"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)
# -----------------------------

patientUIDs = db.patients()
for patientUID in patientUIDs:
    loadedNodeIDs.extend(DICOMUtils.loadPatientByUID(patientUID))

# ----- MONAILabel: Initializing -----
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/config.json").replace('\\', '/')
with open(config_path, 'r') as f:
    config = json.load(f)

config['status'] = "monai_init"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)
# ------------------------------------

slicer.util.selectModule("MONAILabel")

# ----- MONAILabel: Loading data -----
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/config.json").replace('\\', '/')
with open(config_path, 'r') as f:
    config = json.load(f)

config['status'] = "monai_load_data"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)
# ------------------------------------

slicer.modules.MONAILabelWidget.onClickFetchInfo()

volumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
image_id = volumeNode.GetName()

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

# ----- MONAILabel: Segmentation -----
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/config.json").replace('\\', '/')
with open(config_path, 'r') as f:
    config = json.load(f)

config['status'] = "monai_autosegmentation"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)
# ------------------------------------

slicer.modules.MONAILabelWidget.onClickSegmentation()

# ----- MONAILabel: Creating a 3D representation -----
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/config.json").replace('\\', '/')
with open(config_path, 'r') as f:
    config = json.load(f)

config['status'] = "monai_3d"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)
# ----------------------------------------------------

slicer.modules.MONAILabelWidget._segmentNode.CreateClosedSurfaceRepresentation()
slicer.app.layoutManager().threeDWidget(0).threeDView().resetFocalPoint()

# ----- Saving files -----
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/config.json").replace('\\', '/')
with open(config_path, 'r') as f:
    config = json.load(f)

config['status'] = "write_data"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)
# -------------------------

segmentationNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLSegmentationNode")
slicer.modules.segmentations.logic().ExportSegmentsClosedSurfaceRepresentationToFiles(outputFolder, segmentationNode,
                                                                                      None, "STL", True, 1.0, False)
slicer.modules.segmentations.logic().ExportSegmentsClosedSurfaceRepresentationToFiles(outputFolder, segmentationNode,
                                                                                      None, "OBJ", True, 1.0, False)

# ----- Ending -----
config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config/config.json").replace('\\', '/')
with open(config_path, 'r') as f:
    config = json.load(f)

config['status'] = "ready"

with open(config_path, 'w') as f:
    json.dump(config, f, indent=4)
# -------------------
