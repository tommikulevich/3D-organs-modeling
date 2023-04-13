from functools import reduce
import os,sys
import unittest
from __main__ import vtk, qt, ctk, slicer
from glob import glob
import json
from collections import OrderedDict
import re
import threading
import time

try:
  import queue
except ImportError:
  import Queue as queue

from time import sleep

# To avoid the overhead of importing SimpleITK during application
# startup, the import of SimpleITK is delayed until it is needed.
sitk = None
sitkUtils = None

#
# SimpleFilters
#

class SimpleFilters:

  # Use class-level scoped variable for module consants
  if not __file__.endswith("SimpleFilters.py"):
    import inspect
    __file__ = inspect.getframeinfo(inspect.currentframe())[0]

  ICON_DIR = os.path.dirname(os.path.realpath(__file__)) + '/Resources/Icons/'
  JSON_DIR = os.path.dirname(os.path.realpath(__file__)) + '/Resources/json/'


  def __init__(self, parent):
    parent.title = "Simple Filters"
    parent.categories = ["Filtering"]
    parent.dependencies = []
    parent.contributors = ["Bradley Lowekamp (MSC/NLM), Steve Pieper (Isomics), Jean-Christophe Fillion-Robin (Kitware)"]
    parent.helpText = \
"""
This modules provides a basic interface to 250 image filters from the
Insight Toolkit. It provides access to algorithms such as binary
morphology, grayscale morphology, region growing, smoothing, denosing,
distance fields, FFTs, convolutions, automatic thresholding, intensity
math and many advanced algorithms.
<br /><br />

Most algorithms which take multiple input images expect the inputs to
have the same physical locations (spacing, origin, orientation and
largest possible region), and be the same pixel type.
<br /><br />

For general information about the module see the <a href=\"{}/Documentation/Nightly/Modules/SimpleFilters\">online documentation</a>.
<br /><br />

For detailed information about a specific filter please consult the <a href=\"http://www.itk.org/Doxygen/html/\">Insight Toolkit Doxygen</a>.
 """.format(parent.slicerWikiUrl, slicer.app.majorVersion, slicer.app.minorVersion)

    parent.acknowledgementText = """
The developers would like to thank the support of the Slicer Community, the Insight Toolkit and the ITK Community."
""" # replace with organization, grant and thanks.
    self.parent = parent

    parent.icon = qt.QIcon("%s/ITK.png" % self.ICON_DIR)



#
# qSimpleFiltersWidget
#

class SimpleFiltersWidget:
  def __init__(self, parent = None):

    # To avoid the overhead of importing SimpleITK during application
    # startup, the import of SimpleITK is delayed until it is needed.
    global sitk
    import SimpleITK as sitk
    global sitkUtils
    import sitkUtils

    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

    jsonFiles = glob(SimpleFilters.JSON_DIR+"*.json")
    jsonFiles.sort(key=lambda x: os.path.basename(x))

    self.jsonFilters = []

    for fname in jsonFiles:
      try:
        with open(fname) as fp:
          j = json.load(fp,object_pairs_hook=OrderedDict)
          if j["name"] in dir(sitk):
            self.jsonFilters.append(j)
          else:
            if j["itk_module"] in sitk.Version().ITKModulesEnabled():
              import sys
              sys.stderr.write("Unknown SimpleITK class \"{}\".\n".format(j["name"]))
      except Exception as e:
        import sys
        sys.stderr.write(f"Error while reading \"{fname}\". Exception: {e}\n")


    self.filterParameters = None
    self.logic = None


  def setup(self):
    # Instantiate and connect widgets ...

    #
    # Filters Area
    #
    filtersCollapsibleButton = ctk.ctkCollapsibleButton()
    filtersCollapsibleButton.text = "Filters"
    self.layout.addWidget(filtersCollapsibleButton)
    # Layout within the dummy collapsible button
    filtersFormLayout = qt.QFormLayout(filtersCollapsibleButton)

    # filter search
    self.searchBox = ctk.ctkSearchBox()
    filtersFormLayout.addRow("Search:", self.searchBox)
    self.searchBox.connect("textChanged(QString)", self.onSearch)

    # filter selector
    self.filterSelector = qt.QComboBox()
    filtersFormLayout.addRow("Filter:", self.filterSelector)

    # add all the filters listed in the json files
    for idx,j in enumerate(self.jsonFilters):
      name = j["name"]
      self.filterSelector.addItem(name, idx)

    # connections
    self.filterSelector.connect('currentIndexChanged(int)', self.onFilterSelect)


    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    self.filterParameters = FilterParameters(parametersCollapsibleButton)

    # Add vertical spacer
    self.layout.addStretch(1)

    #
    # Status and Progress
    #
    statusLabel = qt.QLabel("Status: ")
    self.currentStatusLabel = qt.QLabel("Idle")
    hlayout = qt.QHBoxLayout()
    hlayout.addStretch(1)
    hlayout.addWidget(statusLabel)
    hlayout.addWidget(self.currentStatusLabel)
    self.layout.addLayout(hlayout)

    self.filterStartTime = None

    self.progress = qt.QProgressBar()
    self.progress.setRange(0,1000)
    self.progress.setValue(0)
    self.layout.addWidget(self.progress)
    self.progress.hide()

    #
    # Cancel/Apply Row
    #
    self.restoreDefaultsButton = qt.QPushButton("Restore Defaults")
    self.restoreDefaultsButton.toolTip = "Restore the default parameters."
    self.restoreDefaultsButton.enabled = True

    self.cancelButton = qt.QPushButton("Cancel")
    self.cancelButton.toolTip = "Abort the algorithm."
    self.cancelButton.enabled = False

    self.applyButton = qt.QPushButton("Apply")
    self.applyButton.toolTip = "Run the algorithm."
    self.applyButton.enabled = True

    hlayout = qt.QHBoxLayout()

    hlayout.addWidget(self.restoreDefaultsButton)
    hlayout.addStretch(1)
    hlayout.addWidget(self.cancelButton)
    hlayout.addWidget(self.applyButton)
    self.layout.addLayout(hlayout)

    # connections
    self.restoreDefaultsButton.connect('clicked(bool)', self.onRestoreDefaultsButton)
    self.applyButton.connect('clicked(bool)', self.onApplyButton)
    self.cancelButton.connect('clicked(bool)', self.onCancelButton)

    # Initlial Selection
    self.filterSelector.currentIndexChanged(self.filterSelector.currentIndex)


  def cleanup(self):
    pass


  def printPythonCommand(self):
    #self.filterParameters.prerun()  # Do this first!
    printStr = []
    currentFilter = self.filterParameters.filter
    varName = currentFilter.__class__.__name__
    printStr.append(f'myFilter = {varName}()')
    for key in dir(currentFilter):
      if key == 'GetName' or key.startswith('GetGlobal'):
        pass
      elif key[:3] == 'Get':
        setAttr = key.replace("Get", "Set", 1)
        if hasattr(currentFilter, setAttr):
          value = eval(f"currentFilter.{key}()")
          printStr.append(f'myFilter.{setAttr}({value})')

    print("\n".join(printStr))

  def onLogicRunStop(self):
      self.applyButton.setEnabled(True)
      self.restoreDefaultsButton.setEnabled(True)
      self.cancelButton.setEnabled(False)
      self.logic = None
      self.progress.hide()


  def onLogicRunStart(self):
      self.applyButton.setEnabled(False)
      self.restoreDefaultsButton.setEnabled(False)


  def onSearch(self, searchText):
    # add all the filters listed in the json files
    self.filterSelector.clear()
    # split text on whitespace of and string search
    searchTextList = searchText.split()
    for idx,j in enumerate(self.jsonFilters):
      lname = j["name"].lower()
      # require all elements in list, to add to select. case insensitive
      if  reduce(lambda x, y: x and (lname.find(y.lower())!=-1), [True]+searchTextList):
        self.filterSelector.addItem(j["name"],idx)


  def onFilterSelect(self, selectorIndex):
    self.filterParameters.destroy()
    if selectorIndex < 0:
      return
    jsonIndex= self.filterSelector.itemData(selectorIndex)
    json = self.jsonFilters[jsonIndex]
    self.filterParameters.create(json)

    if "briefdescription" in self.jsonFilters[jsonIndex]:
      tip=self.jsonFilters[jsonIndex]["briefdescription"]
      tip=tip.rstrip()
      self.filterSelector.setToolTip(tip)
    else:
      self.filterSelector.setToolTip("")


  def onRestoreDefaultsButton(self):
    self.onFilterSelect(self.filterSelector.currentIndex)


  def onApplyButton(self):
    try:

      self.currentStatusLabel.text = "Starting"

      self.filterParameters.prerun()

      self.logic = SimpleFiltersLogic()

      self.printPythonCommand()

      #print "running..."
      self.logic.run(self.filterParameters.filter,
                     self.filterParameters.output,
                     self.filterParameters.outputLabelMap,
                     *self.filterParameters.inputs)

    except:
      self.currentStatusLabel.text = "Exception"

      import sys
      msg = sys.exc_info()[0]

      # if there was an exception during start-up make sure to finish
      self.onLogicRunStop()


      qt.QMessageBox.critical(slicer.util.mainWindow(),
                              f"Exception before execution of {self.filterParameters.filter.GetName()}",
                              msg)



  def onCancelButton(self):
    self.currentStatusLabel.text = "Aborting"
    if self.logic:
      self.logic.abort = True


  def onLogicEventStart(self):
    self.filterStartTime = time.time()
    self.currentStatusLabel.text = "Running"
    self.cancelButton.setDisabled(False)
    self.progress.setValue(0)
    self.progress.show()


  def onLogicEventEnd(self):
    elapsedTimeSec = time.time() - self.filterStartTime
    self.currentStatusLabel.text = f"Completed ({elapsedTimeSec:3.1f}s)"
    self.progress.setValue(1000)


  def onLogicEventAbort(self):
    #print "Aborting..."
    self.currentStatusLabel.text = "Aborted"


  def onLogicEventProgress(self, progress):
    self.currentStatusLabel.text = "Running ({:3.1f}%)".format(progress*100.0)
    self.progress.setValue(progress*1000)


  def onLogicEventIteration(self, nIter):
    print("Iteration " , nIter)



#
# SimpleFiltersLogic
#

class SimpleFiltersLogic:
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    self.main_queue = queue.Queue()
    self.main_queue_running = False
    self.thread = threading.Thread()
    self.abort = False


  def __del__(self):
    if self.main_queue_running:
      self.main_queue_stop()
    if self.thread.is_alive():
      self.thread.join()


  def yieldPythonGIL(self, seconds=0):
    sleep(seconds)


  def cmdCheckAbort(self, sitkFilter):
    if self.abort:
      sitkFilter.Abort()


  def cmdStartEvent(self, sitkFilter):
    #print "cmStartEvent"
    widget = slicer.modules.SimpleFiltersWidget
    self.main_queue.put(lambda: widget.onLogicEventStart())
    self.yieldPythonGIL()


  def cmdProgressEvent(self, sitkFilter):
    #print "cmProgressEvent", sitkFilter.GetProgress()
    widget = slicer.modules.SimpleFiltersWidget
    self.main_queue.put(lambda p=sitkFilter.GetProgress(): widget.onLogicEventProgress(p))
    self.cmdCheckAbort(sitkFilter)
    self.yieldPythonGIL()

  def cmdIterationEvent(self, sitkFilter, nIter):
    print("cmIterationEvent")
    widget = slicer.modules.SimpleFiltersWidget
    self.main_queue.put(lambda: widget.onLogicEventIteration(nIter))
    self.cmdCheckAbort(sitkFilter)
    self.yieldPythonGIL()

  def cmdAbortEvent(self, sitkFilter):
    #print "cmAbortEvent"
    widget = slicer.modules.SimpleFiltersWidget
    self.main_queue.put(lambda: widget.onLogicEventAbort())
    self.yieldPythonGIL()

  def cmdEndEvent(self):
    #print "cmEndEvent"
    widget = slicer.modules.SimpleFiltersWidget
    self.main_queue.put(lambda: widget.onLogicEventEnd())
    self.yieldPythonGIL()

  def thread_doit(self,sitkFilter,*inputImages):
    try:

      nIter = 0
      try:
        sitkFilter.AddCommand(sitk.sitkStartEvent, lambda: self.cmdStartEvent(sitkFilter))
        sitkFilter.AddCommand(sitk.sitkProgressEvent, lambda: self.cmdProgressEvent(sitkFilter))
        sitkFilter.AddCommand(sitk.sitkIterationEvent, lambda: self.cmdIterationEvent(sitkFilter,nIter))
        sitkFilter.AddCommand(sitk.sitkAbortEvent, lambda: self.cmdAbortEvent(sitkFilter))
        sitkFilter.AddCommand(sitk.sitkEndEvent, lambda: self.cmdEndEvent())

      except:
        import sys
        print("Unexpected error:", sys.exc_info()[0])

      img = sitkFilter.Execute(*inputImages)

      if not self.abort:
        self.main_queue.put(lambda img=img:self.updateOutput(img))

    except Exception as e:
      if hasattr(e, 'message'):
        msg = e.message
      else:
        msg = str(e)
      self.abort = True

      self.yieldPythonGIL()
      self.main_queue.put(lambda :qt.QMessageBox.critical(slicer.util.mainWindow(),
                                                          f"Exception during execution of {sitkFilter.GetName()}",
                                                          msg))
    finally:
      # this filter is persistent, remove commands
      sitkFilter.RemoveAllCommands()
      self.main_queue.put(self.main_queue_stop)

  def main_queue_start(self):
    """Begins monitoring of main_queue for callables"""
    self.main_queue_running = True
    slicer.modules.SimpleFiltersWidget.onLogicRunStart()
    qt.QTimer.singleShot(0, self.main_queue_process)

  def main_queue_stop(self):
    """End monitoring of main_queue for callables"""
    self.main_queue_running = False
    if self.thread.is_alive():
      self.thread.join()
    slicer.modules.SimpleFiltersWidget.onLogicRunStop()

  def main_queue_process(self):
    """processes the main_queue of callables"""
    try:
      while not self.main_queue.empty():
        f = self.main_queue.get_nowait()
        if callable(f):
          f()

      if self.main_queue_running:
        # Yield the GIL to allow other thread to do some python work.
        # This is needed since pyQt doesn't yield the python GIL
        self.yieldPythonGIL(.01)
        qt.QTimer.singleShot(0, self.main_queue_process)

    except Exception as e:
      import sys
      sys.stderr.write(f"FilterLogic error in main_queue: \"{e}\"")

      # if there was an error try to resume
      if not self.main_queue.empty() or self.main_queue_running:
        qt.QTimer.singleShot(0, self.main_queue_process)

  def updateOutput(self,img):

    nodeWriteAddress=sitkUtils.GetSlicerITKReadWriteAddress(self.outputNodeName)
    sitk.WriteImage(img,nodeWriteAddress)

    node = slicer.util.getNode(self.outputNodeName)

    applicationLogic = slicer.app.applicationLogic()
    selectionNode = applicationLogic.GetSelectionNode()

    if self.outputLabelMap:
      selectionNode.SetReferenceActiveLabelVolumeID(node.GetID())
    else:
      selectionNode.SetReferenceActiveVolumeID(node.GetID())

    applicationLogic.PropagateVolumeSelection(0)
    applicationLogic.FitSliceToAll()

  def run(self, filter, outputMRMLNode, outputLabelMap, *inputs):
    """
    Run the actual algorithm
    """

    if self.thread.is_alive():
      import sys
      sys.stderr.write("FilterLogic is already executing!")
      return

    inputImages = []

    for i in inputs:
      if i is None:
        break

      imgNodeName = i.GetName()

      img = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(imgNodeName) )
      inputImages.append(img)

    self.output = None
    # check
    self.outputNodeName = outputMRMLNode.GetName()
    self.outputLabelMap = outputLabelMap

    self.abort = False

    self.thread = threading.Thread( target=lambda f=filter,i=inputImages:self.thread_doit(f,*inputImages))

    self.main_queue_start()
    self.thread.start()

#
# Class to manage parameters
#

class FilterParameters:
  """ This class is for managing the widgets for the parameters for a filter
  """

  # class-scope regular expression to help covert from CamelCase
  reCamelCase = re.compile('((?<=[a-z0-9])[A-Z]|(?!^)[A-Z](?=[a-z]))')

  def __init__(self, parent=None):
    self.parent = parent
    self.widgets = []
    self.widgetConnections = []
    self.json = json
    self.filter = None
    self.inputs = []
    self.output = None
    self.prerun_callbacks = []
    self.outputLabelMap = False

    self.outputSelector = None
    self.outputLabelMapBox = None

  def __del__(self):
    self.widgetConnections = []
    self.widgets = []

  def BeautifyCamelCase(self, str):
    return self.reCamelCase.sub(r' \1',str)

  def create(self, json):
    if not self.parent:
      raise "no parent"

    parametersFormLayout = self.parent.layout()

    # You can't use exec in a function that has a subfunction, unless you specify a context.
    exec('self.filter = sitk.{}()'.format(json["name"]), globals(), locals())

    self.prerun_callbacks = []
    self.inputs = []
    self.outputLabelMap = False

    #
    # input volume selectors
    #
    if "inputs" in json:

      # have named inputs
      n=0
      for input in json["inputs"]:

        w = self.createInputWidget(n, noneEnabled=("optional" in input and input["optional"]))

        name = "Input Volume: "
        if  "name" in input:
          name = "Input {}: ".format(input["name"])
        name = name.replace("Image", "Volume")

        print(f"adding {n}: {name}")
        inputSelectorLabel = qt.QLabel(name)
        self.widgets.append(inputSelectorLabel)

        # add to layout after connection
        parametersFormLayout.addRow(inputSelectorLabel, w)

        self.inputs.append(w.currentNode())

        n+=1

        if "number_of_inputs" in json and json["number_of_inputs"] != 0:
          import sys
          sys.stderr.write("Expected \"number_of_inputs\" to be 0 not {}!".format(json["number_of_inputs"]))

    else:

      for n in range(json["number_of_inputs"]):

        w = self.createInputWidget(n)

        inputSelectorLabel = qt.QLabel("Input Volume: ")
        self.widgets.append(inputSelectorLabel)

        # add to layout after connection
        parametersFormLayout.addRow(inputSelectorLabel, w)

        self.inputs.append(w.currentNode())

      #end for each input

    if json["template_code_filename"] == "KernelImageFilter":
      w = self.createVectorWidget("KernelRadius","std::vector<uint32_t>")
      self.widgets.append(w)
      self.addWidgetWithToolTipAndLabel(w,{"briefdescriptionSet":"Radius of structuring element","name":"KernelRadius"})

      labels=["Annulus",
              "Box",
              "Ball",
              "Cross"]
      values=["sitk.sitkAnnulus",
              "sitk.sitkBox",
              "sitk.sitkBall",
              "sitk.sitkCross"]
      w = self.createEnumWidget("KernelType",labels,values)
      self.addWidgetWithToolTipAndLabel(w,{"briefdescriptionSet":"Structuring element","name":"Kernel Type"})

    elif json["template_code_filename"] == "RegionGrowingImageFilter"\
          or json["template_code_filename"] == "FastMarchingImageFilter":

      name="SeedList"
      if (json["template_code_filename"] == "FastMarchingImageFilter"):
        name="TrialPoints"

      fiducialSelector = slicer.qMRMLNodeComboBox()
      self.widgets.append(fiducialSelector)
      fiducialSelector.nodeTypes = ( "vtkMRMLMarkupsFiducialNode", "vtkMRMLAnnotationHierarchyNode")
      fiducialSelector.addAttribute("vtkMRMLAnnotationHierarchyNode", "MainChildType", "vtkMRMLAnnotationFiducialNode" )
      fiducialSelector.selectNodeUponCreation = True
      fiducialSelector.addEnabled = True
      fiducialSelector.removeEnabled = False
      fiducialSelector.renameEnabled = True
      fiducialSelector.noneEnabled = False
      fiducialSelector.showHidden = False
      fiducialSelector.showChildNodeTypes = True
      fiducialSelector.setMRMLScene( slicer.mrmlScene )
      fiducialSelector.setToolTip( "Pick the Markups node for the seed list." )

      fiducialSelector.connect("nodeActivated(vtkMRMLNode*)", lambda node,name=name:self.onFiducialListNode(name,node))
      self.widgetConnections.append((fiducialSelector, "nodeActivated(vtkMRMLNode*)"))
      self.prerun_callbacks.append(lambda w=fiducialSelector,name=name:self.onFiducialListNode(name,w.currentNode()))

      fiducialSelectorLabel = qt.QLabel(f"{name}: ")
      self.widgets.append(fiducialSelectorLabel)

      #todo set tool tip
      # add to layout after connection
      parametersFormLayout.addRow(fiducialSelectorLabel, fiducialSelector)


    #
    # Iterate over the members in the JSON to generate a GUI
    #
    for member in json["members"]:
      w = None
      if "type" in member:
        t = member["type"]

      if "dim_vec" in member and int(member["dim_vec"]):
        if member["itk_type"].endswith("IndexType") or member["itk_type"].endswith("PointType"):
          isPoint = member["itk_type"].endswith("PointType")

          fiducialSelector = slicer.qMRMLNodeComboBox()
          self.widgets.append(fiducialSelector)
          fiducialSelector.nodeTypes = (  "vtkMRMLMarkupsFiducialNode", "vtkMRMLAnnotationFiducialNode" )
          fiducialSelector.selectNodeUponCreation = True
          fiducialSelector.addEnabled = False
          fiducialSelector.removeEnabled = False
          fiducialSelector.renameEnabled = True
          fiducialSelector.noneEnabled = False
          fiducialSelector.showHidden = False
          fiducialSelector.showChildNodeTypes = True
          fiducialSelector.setMRMLScene( slicer.mrmlScene )
          fiducialSelector.setToolTip( "Pick the Fiducial for the Point or Index" )

          fiducialSelector.connect("nodeActivated(vtkMRMLNode*)", lambda node,w=fiducialSelector,name=member["name"],isPt=isPoint:self.onFiducialNode(name,w,isPt))
          self.widgetConnections.append((fiducialSelector, "nodeActivated(vtkMRMLNode*)"))
          self.prerun_callbacks.append(lambda w=fiducialSelector,name=member["name"],isPt=isPoint:self.onFiducialNode(name,w,isPt))

          w1 = fiducialSelector

          fiducialSelectorLabel = qt.QLabel("{}: ".format(member["name"]))
          self.widgets.append(fiducialSelectorLabel)

          icon = qt.QIcon(SimpleFilters.ICON_DIR+"Fiducials.png")

          toggle = qt.QPushButton(icon, "")
          toggle.setCheckable(True)
          toggle.toolTip = "Toggle Fiducial Selection"
          self.widgets.append(toggle)

          w2 = self.createVectorWidget(member["name"],t)

          hlayout = qt.QHBoxLayout()
          hlayout.addWidget(fiducialSelector)
          hlayout.setStretchFactor(fiducialSelector,1)
          hlayout.addWidget(w2)
          hlayout.setStretchFactor(w2,1)
          hlayout.addWidget(toggle)
          hlayout.setStretchFactor(toggle,0)
          w1.hide()

          self.widgets.append(hlayout)

          toggle.connect("clicked(bool)", lambda checked,ptW=w2,fidW=w1:self.onToggledPointSelector(checked,ptW,fidW))
          self.widgetConnections.append((toggle, "clicked(bool)"))

          parametersFormLayout.addRow(fiducialSelectorLabel, hlayout)

        else:
          w = self.createVectorWidget(member["name"],t)

      elif "point_vec" in member:

        fiducialSelector = slicer.qMRMLNodeComboBox()
        self.widgets.append(fiducialSelector)
        fiducialSelector.nodeTypes = ( "vtkMRMLMarkupsFiducialNode", "vtkMRMLAnnotationHierarchyNode")
        fiducialSelector.addAttribute("vtkMRMLAnnotationHierarchyNode", "MainChildType", "vtkMRMLAnnotationFiducialNode" )
        fiducialSelector.selectNodeUponCreation = True
        fiducialSelector.addEnabled = True
        fiducialSelector.removeEnabled = False
        fiducialSelector.renameEnabled = True
        fiducialSelector.noneEnabled = False
        fiducialSelector.showHidden = False
        fiducialSelector.showChildNodeTypes = True
        fiducialSelector.setMRMLScene( slicer.mrmlScene )
        fiducialSelector.setToolTip( "Pick the Markups node for the point list." )

        fiducialSelector.connect("nodeActivated(vtkMRMLNode*)", lambda node,name=member["name"]:self.onFiducialListNode(name,node))
        self.widgetConnections.append((fiducialSelector, "nodeActivated(vtkMRMLNode*)"))
        self.prerun_callbacks.append(lambda w=fiducialSelector,name=member["name"],:self.onFiducialListNode(name,w.currentNode()))

        w = fiducialSelector

      elif "enum" in member:
        w = self.createEnumWidget(member["name"],member["enum"])
      elif member["name"].endswith("Direction") and "std::vector" in t:
        # This member name is use for direction cosine matrix for image sources.
        # We are going to ignore it
        pass
      elif t == "InterpolatorEnum":
        labels=["Nearest Neighbor",
                "Linear",
                "BSpline",
                "Gaussian",
                "Label Gaussian",
                "Hamming Windowed Sinc",
                "Cosine Windowed Sinc",
                "Welch Windowed Sinc",
                "Lanczos Windowed Sinc",
                "Blackman Windowed Sinc"]
        values=["sitk.sitkNearestNeighbor",
                "sitk.sitkLinear",
                "sitk.sitkBSpline",
                "sitk.sitkGaussian",
                "sitk.sitkLabelGaussian",
                "sitk.sitkHammingWindowedSinc",
                "sitk.sitkCosineWindowedSinc",
                "sitk.sitkWelchWindowedSinc",
                "sitk.sitkLanczosWindowedSinc",
                "sitk.sitkBlackmanWindowedSinc"]

        w = self.createEnumWidget(member["name"],labels,values)
        pass
      elif t == "PixelIDValueEnum":
        labels=["int8_t",
                "uint8_t",
                "int16_t",
                "uint16_t",
                "uint32_t",
                "int32_t",
                "float",
                "double"]
        values=["sitk.sitkInt8",
                "sitk.sitkUInt8",
                "sitk.sitkInt16",
                "sitk.sitkUInt16",
                "sitk.sitkInt32",
                "sitk.sitkUInt32",
                "sitk.sitkFloat32",
                "sitk.sitkFloat64"]
        w = self.createEnumWidget(member["name"],labels,values)
      elif t in ["double", "float"]:
        w = self.createDoubleWidget(member["name"])
      elif t == "bool":
        w = self.createBoolWidget(member["name"])
      elif t in ["uint8_t", "int8_t",
               "uint16_t", "int16_t",
               "uint32_t", "int32_t",
               "unsigned int", "int"]:
        w = self.createIntWidget(member["name"],t)
      elif t in ["uint64_t", "int64_t"]:
        w = self.createLargeIntWidget(member["name"])
      else:
        import sys
        sys.stderr.write("Unknown member \"{}\" of type \"{}\"\n".format(member["name"],member["type"]))

      if w:
        self.addWidgetWithToolTipAndLabel(w,member)


    # end for each member


    #
    # output volume selector
    #
    outputSelectorLabel = qt.QLabel("Output Volume: ")
    self.widgets.append(outputSelectorLabel)


    self.outputSelector = slicer.qMRMLNodeComboBox()
    self.widgets.append(self.outputSelector)
    self.outputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode", "vtkMRMLLabelMapVolumeNode"]
    self.outputSelector.selectNodeUponCreation = True
    self.outputSelector.addEnabled = True
    self.outputSelector.removeEnabled = False
    self.outputSelector.renameEnabled = True
    self.outputSelector.noneEnabled = False
    self.outputSelector.showHidden = False
    self.outputSelector.showChildNodeTypes = False
    self.outputSelector.baseName = json["name"]+" Output"
    self.outputSelector.setMRMLScene( slicer.mrmlScene )
    self.outputSelector.setToolTip( "Pick the output to the algorithm." )

    self.outputSelector.connect("nodeActivated(vtkMRMLNode*)", lambda node:self.onOutputSelect(node))
    self.widgetConnections.append((self.outputSelector, "nodeActivated(vtkMRMLNode*)"))


    # add to layout after connection
    parametersFormLayout.addRow(outputSelectorLabel, self.outputSelector)

    self.output = self.outputSelector.currentNode()

    #
    # LabelMap toggle
    #
    outputLabelMapLabel = qt.QLabel("LabelMap: ")
    self.widgets.append(outputLabelMapLabel)

    self.outputLabelMapBox = qt.QCheckBox()
    self.widgets.append(self.outputLabelMapBox)
    self.outputLabelMapBox.setToolTip("Output Volume is set as a labelmap")
    self.outputLabelMapBox.setChecked(self.outputLabelMap)
    self.outputLabelMapBox.setDisabled(True)

    self.outputLabelMapBox.connect("stateChanged(int)", lambda val:self.onOutputLabelMapChanged(bool(val)))
    self.widgetConnections.append((self.outputLabelMapBox, "stateChanged(int)"))
     # add to layout after connection
    parametersFormLayout.addRow(outputLabelMapLabel, self.outputLabelMapBox)


  def createInputWidget(self,n, noneEnabled=False):
      inputSelector = slicer.qMRMLNodeComboBox()
      self.widgets.append(inputSelector)
      inputSelector.nodeTypes = ["vtkMRMLScalarVolumeNode", "vtkMRMLLabelMapVolumeNode"]
      inputSelector.selectNodeUponCreation = True
      inputSelector.addEnabled = False
      inputSelector.removeEnabled = False
      inputSelector.noneEnabled = noneEnabled
      inputSelector.showHidden = False
      inputSelector.showChildNodeTypes = False
      inputSelector.setMRMLScene( slicer.mrmlScene )
      inputSelector.setToolTip( "Pick the input to the algorithm." )

      # connect and verify parameters
      inputSelector.connect("nodeActivated(vtkMRMLNode*)", lambda node,i=n:self.onInputSelect(node,i))
      self.widgetConnections.append((inputSelector, "nodeActivated(vtkMRMLNode*)"))
      return inputSelector

  def createEnumWidget(self,name,enumList,valueList=None):

    w = qt.QComboBox()
    self.widgets.append(w)

    default = self._getParameterValue(name)

    if valueList is None:
      valueList = ["self.filter."+e for e in enumList]

    for e,v in zip(enumList,valueList):
      w.addItem(e,v)

      # check if current item is default, set if it is
      ldict = locals().copy()
      exec('itemValue='+v, globals(), ldict)
      if ldict['itemValue'] == default:
        w.setCurrentIndex(w.count-1)

    w.connect("currentIndexChanged(int)", lambda selectorIndex,n=name,selector=w:self.onEnumChanged(n,selectorIndex,selector))
    self.widgetConnections.append((w, "currentIndexChanged(int)"))
    return w

  def createVectorWidget(self,name,type):
    m = re.search(r"<([a-zA-Z ]+)>", type)
    if m:
      type = m.group(1)

    w = ctk.ctkCoordinatesWidget()
    self.widgets.append(w)

    if type in ["double", "float"]:
      w.setDecimals(5)
      w.minimum=-3.40282e+038
      w.maximum=3.40282e+038
      w.connect("coordinatesChanged(double*)", lambda val,widget=w,name=name:self.onFloatVectorChanged(name,widget,val))
    elif type == "bool":
      w.setDecimals(0)
      w.minimum=0
      w.maximum=1
      w.connect("coordinatesChanged(double*)", lambda val,widget=w,name=name:self.onBoolVectorChanged(name,widget,val))
    else:
      w.setDecimals(0)
      w.connect("coordinatesChanged(double*)", lambda val,widget=w,name=name:self.onIntVectorChanged(name,widget,val))
    self.widgetConnections.append((w, "coordinatesChanged(double*)"))

    default = self._getParameterValue(name)
    w.coordinates = ",".join(str(x) for x in default)
    return w

  def createIntWidget(self,name,type="int"):

    w = qt.QSpinBox()
    self.widgets.append(w)

    if type=="uint8_t":
      w.setRange(0,255)
    elif type=="int8_t":
      w.setRange(-128,127)
    elif type=="uint16_t":
      w.setRange(0,65535)
    elif type=="int16_t":
      w.setRange(-32678,32767)
    elif type=="uint32_t" or type=="unsigned int":
      w.setRange(0,2147483647)
    elif type=="int32_t" or type=="int":
      w.setRange(-2147483648,2147483647)

    w.setValue(int(self._getParameterValue(name)))
    w.connect("valueChanged(int)", lambda val,name=name:self.onScalarChanged(name,val))
    self.widgetConnections.append((w, "valueChanged(int)"))
    return w

  def createLargeIntWidget(self,name):
    w = qt.QLineEdit()
    self.widgets.append(w)
    validator = qt.QRegExpValidator(qt.QRegExp(r'[0-9-]{0,20}'), w)
    w.setValidator(validator)
    w.setText(self._getParameterValue(name))
    w.connect("textChanged(QString)", lambda val,name=name:self.onScalarChanged(name,int(val)))
    self.widgetConnections.append((w, "textChanged(QString)"))
    return w

  def createBoolWidget(self,name):
    w = qt.QCheckBox()
    self.widgets.append(w)

    w.setChecked(self._getParameterValue(name))

    w.connect("stateChanged(int)", lambda val,name=name:self.onScalarChanged(name,bool(val)))
    self.widgetConnections.append((w, "stateChanged(int)"))

    return w

  def _getParameterValue(self, parameterName):
    ldict = locals().copy()
    exec(f'default = self.filter.Get{parameterName}()', globals(), ldict)
    return ldict['default']

  def createDoubleWidget(self,name):

    w = qt.QDoubleSpinBox()
    self.widgets.append(w)

    w.setRange(-3.40282e+038, 3.40282e+038)
    w.decimals = 5

    w.setValue(self._getParameterValue(name))
    w.connect("valueChanged(double)", lambda val,name=name:self.onScalarChanged(name,val))
    self.widgetConnections.append((w, "valueChanged(double)"))

    return w

  def addWidgetWithToolTipAndLabel(self,widget,memberJSON):
    tip=""
    if "briefdescriptionSet" in memberJSON and len(memberJSON["briefdescriptionSet"]):
      tip=memberJSON["briefdescriptionSet"]
    elif "detaileddescriptionSet" in memberJSON:
      tip=memberJSON["detaileddescriptionSet"]

    # remove trailing white space
    tip=tip.rstrip()

    l = qt.QLabel(self.BeautifyCamelCase(memberJSON["name"])+": ")
    self.widgets.append(l)

    widget.setToolTip(tip)
    l.setToolTip(tip)

    parametersFormLayout = self.parent.layout()
    parametersFormLayout.addRow(l,widget)

  def onToggledPointSelector(self, fidVisible, ptWidget, fiducialWidget):
    ptWidget.setVisible(False)
    fiducialWidget.setVisible(False)

    ptWidget.setVisible(not fidVisible)
    fiducialWidget.setVisible(fidVisible)

    if ptWidget.visible:
      # Update the coordinate values to envoke the changed signal.
      # This will update the filter from the widget
      ptWidget.coordinates = ",".join(str(x) for x in ptWidget.coordinates.split(',') )

  def onInputSelect(self, mrmlNode, n):
    self.inputs[n] = mrmlNode

  def onOutputSelect(self, mrmlNode):
    self.output = mrmlNode
    self.onOutputLabelMapChanged(mrmlNode.IsA("vtkMRMLLabelMapVolumeNode"))

  def onOutputLabelMapChanged(self, v):
    self.outputLabelMap = v
    self.outputLabelMapBox.setChecked(v)

  def onFiducialNode(self, name, mrmlWidget, isPoint):
    if not mrmlWidget.visible:
      return
    annotationFiducialNode = mrmlWidget.currentNode()

    # point in physical space
    coord = [0,0,0]

    if annotationFiducialNode.GetClassName() == "vtkMRMLMarkupsFiducialNode":
      # slicer4 Markups node
      if annotationFiducialNode.GetNumberOfFiducials() < 1:
        return
      annotationFiducialNode.GetNthFiducialPosition(0, coord)
    else:
      annotationFiducialNode.GetFiducialCoordinates(coord)

    # HACK transform from RAS to LPS
    coord = [-coord[0],-coord[1],coord[2]]

    # FIXME: we should not need to copy the image
    if not isPoint and len(self.inputs) and self.inputs[0]:
      imgNodeName = self.inputs[0].GetName()
      img = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(imgNodeName) )
      coord = img.TransformPhysicalPointToIndex(coord)
    exec(f'self.filter.Set{name}(coord)')

  def onFiducialListNode(self, name, mrmlNode):
    annotationHierarchyNode = mrmlNode

    # list of points in physical space
    coords = []

    if annotationHierarchyNode.GetClassName() == "vtkMRMLMarkupsFiducialNode":
      # slicer4 Markups node

      for i in range(annotationHierarchyNode.GetNumberOfFiducials()):
        coord = [0,0,0]
        annotationHierarchyNode.GetNthFiducialPosition(i, coord)
        coords.append(coord)
    else:
      # slicer4 style hierarchy nodes

      # get the first in the list
      for listIndex in range(annotationHierarchyNode.GetNumberOfChildrenNodes()):
        if annotationHierarchyNode.GetNthChildNode(listIndex) is None:
          continue

        annotation = annotationHierarchyNode.GetNthChildNode(listIndex).GetAssociatedNode()
        if annotation is None:
          continue

        coord = [0,0,0]
        annotation.GetFiducialCoordinates(coord)
        coords.append(coord)

    if self.inputs[0]:
      imgNodeName = self.inputs[0].GetName()
      img = sitk.ReadImage(sitkUtils.GetSlicerITKReadWriteAddress(imgNodeName) )

      # HACK transform from RAS to LPS
      coords = [ [-pt[0],-pt[1],pt[2]] for pt in coords]

      idx_coords = [img.TransformPhysicalPointToIndex(pt) for pt in coords]

      exec(f'self.filter.Set{name}(idx_coords)')

  def onScalarChanged(self, name, val):
    exec(f'self.filter.Set{name}(val)')

  def onEnumChanged(self, name, selectorIndex, selector):
    data=selector.itemData(selectorIndex)
    exec(f'self.filter.Set{name}({data})')

  def onBoolVectorChanged(self, name, widget, val):
    coords = [bool(float(x)) for x in widget.coordinates.split(',')]
    exec(f'self.filter.Set{name}(coords)')

  def onIntVectorChanged(self, name, widget, val):
    coords = [int(float(x)) for x in widget.coordinates.split(',')]
    exec(f'self.filter.Set{name}(coords)')

  def onFloatVectorChanged(self, name, widget, val):
    coords = [float(x) for x in widget.coordinates.split(',')]
    exec(f'self.filter.Set{name}(coords)')


  def prerun(self):
    for f in self.prerun_callbacks:
      f()

  def destroy(self):

    for widget, sig in self.widgetConnections:
      widget.disconnect(sig)
    self.widgetConnections = []

    for w in self.widgets:
      #self.parent.layout().removeWidget(w)
      w.deleteLater()
      w.setParent(None)
    self.widgets = []
