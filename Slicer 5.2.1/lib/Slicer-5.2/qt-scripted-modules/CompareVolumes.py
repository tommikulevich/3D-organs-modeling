import os, string
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *

#
# CompareVolumes
#

class CompareVolumes(ScriptedLoadableModule):
  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    parent.title = "Compare Volumes"
    parent.categories = ["Wizards"]
    parent.dependencies = []
    parent.contributors = ["Steve Pieper (Isomics)"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    """
    parent.helpText = string.Template("""
    This module helps organize layouts and volume compositing to help compare images

Please refer to <a href=\"$a/Documentation/$b.$c/Modules/CompareVolumes\"> the documentation</a>.

    """).substitute({ 'a':parent.slicerWikiUrl, 'b':slicer.app.majorVersion, 'c':slicer.app.minorVersion })
    parent.acknowledgementText = """
    This file was originally developed by Steve Pieper, Isomics, Inc.
    It was partially funded by NIH grant 3P41RR013218-12S1 and P41 EB015902 the
    Neuroimage Analysis Center (NAC) a Biomedical Technology Resource Center supported
    by the National Institute of Biomedical Imaging and Bioengineering (NIBIB).
    And this work is part of the "National Alliance for Medical Image
    Computing" (NAMIC), funded by the National Institutes of Health
    through the NIH Roadmap for Medical Research, Grant U54 EB005149.
    Information on the National Centers for Biomedical Computing
    can be obtained from http://nihroadmap.nih.gov/bioinformatics.
    This work is also supported by NIH grant 1R01DE024450-01A1
    "Quantification of 3D Bony Changes in Temporomandibular Joint Osteoarthritis"
    (TMJ-OA).
""" # replace with organization, grant and thanks.

#
# qCompareVolumesWidget
#

class CompareVolumesWidget(ScriptedLoadableModuleWidget):

  def __init__(self, parent=None):
    ScriptedLoadableModuleWidget.__init__(self, parent)
    self.layerReveal = None

  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    if self.developerMode:
      # reload and run specific tests
      scenarios = ("Three Volume", "View Watcher", "LayerReveal",)
      for scenario in scenarios:
        button = qt.QPushButton("Reload and Test %s" % scenario)
        self.reloadAndTestButton.toolTip = "Reload this module and then run the %s self test." % scenario
        self.reloadCollapsibleButton.layout().addWidget(button)
        button.connect('clicked()', lambda s=scenario: self.onReloadAndTest(scenario=s))

    #
    # Parameters Area
    #
    parametersCollapsibleButton = ctk.ctkCollapsibleButton()
    parametersCollapsibleButton.text = "Parameters"
    self.layout.addWidget(parametersCollapsibleButton)

    # Layout within the dummy collapsible button
    parametersFormLayout = qt.QFormLayout(parametersCollapsibleButton)

    #
    # Volume order select
    #
    self.volumeOrderSelect = VolumeOrderSelect()
    parametersFormLayout.addRow("Volumes", self.volumeOrderSelect.widget)

    #
    # orientation
    #
    self.orientationBox = qt.QGroupBox()
    self.orientationBox.setLayout(qt.QFormLayout())
    self.orientationButtons = {}
    self.orientations = ("Axial", "Sagittal", "Coronal", "AxiSagCor")
    for orientation in self.orientations:
      self.orientationButtons[orientation] = qt.QRadioButton()
      self.orientationButtons[orientation].text = orientation
      self.orientationButtons[orientation].connect("clicked()",
                                lambda o=orientation: self.setOrientation(o))
      self.orientationBox.layout().addWidget(
                                self.orientationButtons[orientation])
    parametersFormLayout.addRow("Orientation", self.orientationBox)
    self.setOrientation(self.orientations[0])

    #
    # background volume selector
    #
    self.backgroundSelector = slicer.qMRMLNodeComboBox()
    self.backgroundSelector.nodeTypes = ( ("vtkMRMLVolumeNode"), "" )
    self.backgroundSelector.selectNodeUponCreation = True
    self.backgroundSelector.addEnabled = False
    self.backgroundSelector.removeEnabled = False
    self.backgroundSelector.noneEnabled = True
    self.backgroundSelector.showHidden = False
    self.backgroundSelector.showChildNodeTypes = True
    self.backgroundSelector.setMRMLScene( slicer.mrmlScene )
    self.backgroundSelector.setToolTip( "Common background - all lightbox panes will have this background and a different volume in each foreground." )
    parametersFormLayout.addRow("Common Background: ", self.backgroundSelector)

    #
    # label volume selector
    #
    self.labelSelector = slicer.qMRMLNodeComboBox()
    self.labelSelector.nodeTypes = ( ("vtkMRMLLabelMapVolumeNode"), "" )
    self.labelSelector.selectNodeUponCreation = True
    self.labelSelector.addEnabled = False
    self.labelSelector.removeEnabled = False
    self.labelSelector.noneEnabled = True
    self.labelSelector.showHidden = False
    self.labelSelector.showChildNodeTypes = True
    self.labelSelector.setMRMLScene( slicer.mrmlScene )
    self.labelSelector.setToolTip( "Common label - all lightbox panes will have this label on top." )
    parametersFormLayout.addRow("Common Label: ", self.labelSelector)

    #
    # Hot link and cursor
    #
    self.hotLinkWithCursorCheck = qt.QCheckBox()
    self.hotLinkWithCursorCheck.checked = True
    parametersFormLayout.addRow("Hot Link with Cursor", self.hotLinkWithCursorCheck)

    #
    # re-use some UI from LandmarkRegistration
    # - TODO: this makes odd circular dependency
    #   that may need to be refactored someday,
    #   but for now it works because this widget
    #   is a common depdency.
    #
    import LandmarkRegistration
    self.visualization = LandmarkRegistration.RegistrationLib.VisualizationWidget(None)
    self.visualization.groupBoxLayout.itemAt(3).widget().hide()
    self.visualization.groupBoxLayout.itemAt(2).widget().hide()
    self.visualization.groupBoxLayout.itemAt(1).widget().hide()
    self.visualization.groupBoxLayout.itemAt(0).widget().hide()
    parametersFormLayout.addRow(self.visualization.widget)
    self.visualization.connect("layoutRequested(mode,volumesToShow)", self.onCompareVolumes)

    #
    # Compare Button
    #
    self.compareVolumesButton = qt.QPushButton("Compare Checked Volumes")
    self.compareVolumesButton.setToolTip( "Make a set of slice views that show each of the currently checked volumes, with optional companion volumes, in the selected orientation." )
    parametersFormLayout.addRow(self.compareVolumesButton)
    self.compareVolumesButton.connect("clicked()", self.onCompareVolumes)

    #
    # Add layer reveal area
    #
    layerRevealCollapsibleButton = ctk.ctkCollapsibleButton()
    layerRevealCollapsibleButton.text = "Layer Reveal Cursor"
    self.layout.addWidget(layerRevealCollapsibleButton)
    layerRevealFormLayout = qt.QFormLayout(layerRevealCollapsibleButton)

    self.layerRevealCheck = qt.QCheckBox()
    layerRevealFormLayout.addRow("Layer Reveal Cursor", self.layerRevealCheck)
    self.layerRevealCheck.connect("toggled(bool)", self.onLayerRevealToggled)

    self.layerRevealScaleCheck = qt.QCheckBox()
    layerRevealFormLayout.addRow("Layer Reveal Cursor Scaled 2x", self.layerRevealScaleCheck)
    self.layerRevealScaleCheck.connect("toggled(bool)", self.onLayerRevealToggled)

    # Add vertical spacer
    self.layout.addStretch(1)

  def cleanup(self):
    self.volumeOrderSelect.cleanup()
    if self.layerReveal:
      self.layerReveal.cleanup()

  def setOrientation(self,orientation):
    if orientation in self.orientations:
      self.selectedOrientation = orientation
      self.orientationButtons[orientation].checked = True

  def onLayerRevealToggled(self):
    if self.layerReveal is not None:
      self.layerReveal.cleanup()
      self.layerReveal = None
    if self.layerRevealCheck.checked:
      self.layerReveal = LayerReveal(scale=self.layerRevealScaleCheck.checked)

  def onCompareVolumes(self):
    logic = CompareVolumesLogic()
    volumeIDs = self.volumeOrderSelect.volumeIDs()
    volumeNodes = [slicer.mrmlScene.GetNodeByID(id) for id in volumeIDs]
    if self.selectedOrientation == 'AxiSagCor':
        viewers = logic.viewersPerVolume(
            volumeNodes=volumeNodes,
            background=self.backgroundSelector.currentNode(),
            label=self.labelSelector.currentNode(),
            opacity=self.visualization.fadeSlider.value,
            )
    else:
        viewers = logic.viewerPerVolume(
            volumeNodes=volumeNodes,
            orientation=self.selectedOrientation,
            background=self.backgroundSelector.currentNode(),
            label=self.labelSelector.currentNode(),
            opacity=self.visualization.fadeSlider.value,
            )
    if self.hotLinkWithCursorCheck.checked:
        for viewName in viewers.keys():
            sliceWidget = slicer.app.layoutManager().sliceWidget(viewName)
            compositeNode = sliceWidget.sliceLogic().GetSliceCompositeNode()
            compositeNode.SetLinkedControl(True)
            compositeNode.SetHotLinkedControl(True)
        crosshairNode = slicer.mrmlScene.GetSingletonNode("default", "vtkMRMLCrosshairNode")
        crosshairNode.SetCrosshairMode(crosshairNode.ShowSmallBasic)


class VolumeOrderSelect:
    """Helper class to manage a list widget with a checkable
    and re-orderable item for each volume in the scene"""
    def __init__(self):
      self.widget = qt.QWidget()
      self.layout = qt.QVBoxLayout()
      self.widget.setLayout(self.layout)
      self.listWidget = qt.QListWidget()
      self.listWidget.setDragDropMode(qt.QAbstractItemView.InternalMove)
      self.layout.addWidget(self.listWidget)
      self.controlWiget = qt.QWidget()
      self.controlLayout = qt.QHBoxLayout()
      self.controlWiget.setLayout(self.controlLayout)
      self.selectAllButton = qt.QPushButton("Select all")
      self.unselectAllButton = qt.QPushButton("Unselect all")
      self.controlLayout.addWidget(self.selectAllButton)
      self.controlLayout.addWidget(self.unselectAllButton)
      self.layout.addWidget(self.controlWiget)
      self.selectAllButton.connect("clicked()", lambda state=qt.Qt.Checked: self.setCheckStates(state))
      self.unselectAllButton.connect("clicked()", lambda state=qt.Qt.Unchecked: self.setCheckStates(state))
      events = [slicer.mrmlScene.NodeAddedEvent,
                slicer.mrmlScene.NodeRemovedEvent,
                slicer.mrmlScene.NewSceneEvent]
      self.observations = []
      for event in events:
        self.observations.append(slicer.mrmlScene.AddObserver(event, self.refresh))
      self.refresh()

    def setCheckStates(self, state):
      listModel = self.listWidget.model()
      for row in range(listModel.rowCount()):
        item = self.listWidget.item(row)
        item.setCheckState(state)

    def cleanup(self):
      for observation in self.observations:
        slicer.mrmlScene.RemoveObserver(observation)

    def refresh(self, caller=None, event=None):
      """synchronize list items with current volume
      nodes in scene while retaining order and check state"""
      listModel = self.listWidget.model()
      # first, save the order and checkstate
      previousVolumeIDs = []
      previousCheckStates = []
      for row in range(listModel.rowCount()):
        item = self.listWidget.item(row)
        previousCheckStates.append(item.checkState())
        previousVolumeIDs.append(item.toolTip())
      # reset, and first add any of the previous volumes still in scene
      self.listWidget.clear()
      sceneVolumeNodes = list(slicer.util.getNodes('*VolumeNode*').values())
      sceneVolumeIDs = [node.GetID() for node in sceneVolumeNodes]
      volumeIDs = []
      volumeCheckStates = []
      for volumeIndex in range(len(previousVolumeIDs)):
        if previousVolumeIDs[volumeIndex] in sceneVolumeIDs:
          volumeIDs.append(previousVolumeIDs[volumeIndex])
          volumeCheckStates.append(previousCheckStates[volumeIndex])
      # add any new volumes that were here before
      for volumeID in sceneVolumeIDs:
        if volumeID not in volumeIDs:
          volumeIDs.append(volumeID)
          volumeCheckStates.append(qt.Qt.Checked)
      # add items
      for (volumeID,volumeCheckState) in zip(volumeIDs, volumeCheckStates):
        volumeNode = slicer.mrmlScene.GetNodeByID(volumeID)
        self.listWidget.addItem(volumeNode.GetName())
        item = self.listWidget.item(listModel.rowCount()-1)
        item.setToolTip(volumeID)
        item.setCheckState(volumeCheckState)

    def volumeIDs(self):
      volumeIDs = []
      listModel = self.listWidget.model()
      for row in range(listModel.rowCount()):
        item = self.listWidget.item(row)
        if item.checkState() == qt.Qt.Checked:
          volumeIDs.append(item.toolTip())
      return volumeIDs


#
# CompareVolumesLogic
#

class CompareVolumesLogic(ScriptedLoadableModuleLogic):
  """This class should implement all the actual
  computation done by your module.  The interface
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    ScriptedLoadableModuleLogic.__init__(self)
    self.sliceViewItemPattern = """
      <item><view class="vtkMRMLSliceNode" singletontag="{viewName}">
        <property name="orientation" action="default">{orientation}</property>
        <property name="viewlabel" action="default">{viewName}</property>
        <property name="viewcolor" action="default">{color}</property>
      </view></item>
     """
    # use a nice set of colors
    self.colors = slicer.util.getNode('GenericColors')
    self.lookupTable = self.colors.GetLookupTable()

  def assignLayoutDescription(self,layoutDescription):
    """assign the xml to the user-defined layout slot"""
    layoutNode = slicer.util.getNode('*LayoutNode*')
    if layoutNode.IsLayoutDescription(layoutNode.SlicerLayoutUserView):
      layoutNode.SetLayoutDescription(layoutNode.SlicerLayoutUserView, layoutDescription)
    else:
      layoutNode.AddLayoutDescription(layoutNode.SlicerLayoutUserView, layoutDescription)
    layoutNode.SetViewArrangement(layoutNode.SlicerLayoutUserView)

  def viewerPerVolume(self,volumeNodes=None,background=None,label=None,viewNames=[],layout=None,orientation='Axial',opacity=0.5):
    """ Load each volume in the scene into its own
    slice viewer and link them all together.
    If background is specified, put it in the background
    of all viewers and make the other volumes be the
    forground.  If label is specified, make it active as
    the label layer of all viewers.
    Return a map of slice nodes indexed by the view name (given or generated).
    Opacity applies only when background is selected.
    """
    import math

    if not volumeNodes:
      volumeNodes = list(slicer.util.getNodes('*VolumeNode*').values())

    if len(volumeNodes) == 0:
      return

    volumeCount = len(volumeNodes)
    volumeCountSqrt = math.sqrt(volumeCount)
    if layout:
      rows = layout[0]
      columns = layout[1]
    elif volumeCountSqrt == math.floor(volumeCountSqrt):
      rows = int(volumeCountSqrt)
      columns = int(volumeCountSqrt)
    else:
      # make an array with wide screen aspect ratio
      # - e.g. 3 volumes in 3x1 grid
      # - 5 volumes 3x2 with only two volumes in second row
      c = 1.5 * volumeCountSqrt
      columns = math.floor(c)
      if (c != columns) and (volumeCount % columns != 0):
        columns += 1
      if columns > volumeCount:
        columns = volumeCount
      r = volumeCount / columns
      rows = math.floor(r)
      if r != rows:
        rows += 1

    #
    # construct the XML for the layout
    # - one viewer per volume
    # - default orientation as specified
    #
    actualViewNames = []
    index = 1
    layoutDescription = ''
    layoutDescription += '<layout type="vertical">\n'
    for row in range(int(rows)):
      layoutDescription += ' <item> <layout type="horizontal">\n'
      for column in range(int(columns)):
        try:
          viewName = viewNames[index-1]
        except IndexError:
          viewName = '%d_%d' % (row,column)
        rgb = [int(round(v*255)) for v in self.lookupTable.GetTableValue(index)[:-1]]
        color = '#%0.2X%0.2X%0.2X' % tuple(rgb)
        layoutDescription += self.sliceViewItemPattern.format(viewName=viewName,orientation=orientation,color=color)
        actualViewNames.append(viewName)
        index += 1
      layoutDescription += '</layout></item>\n'
    layoutDescription += '</layout>'
    self.assignLayoutDescription(layoutDescription)

    # let the widgets all decide how big they should be
    slicer.app.processEvents()

    # put one of the volumes into each view, or none if it should be blank
    sliceNodesByViewName = {}
    layoutManager = slicer.app.layoutManager()
    for index in range(len(actualViewNames)):
      viewName = actualViewNames[index]
      try:
        volumeNodeID = volumeNodes[index].GetID()
      except IndexError:
        volumeNodeID = ""

      sliceWidget = layoutManager.sliceWidget(viewName)
      compositeNode = sliceWidget.mrmlSliceCompositeNode()
      if background:
        compositeNode.SetBackgroundVolumeID(background.GetID())
        compositeNode.SetForegroundVolumeID(volumeNodeID)
        compositeNode.SetForegroundOpacity(opacity)
      else:
        compositeNode.SetBackgroundVolumeID(volumeNodeID)
        compositeNode.SetForegroundVolumeID("")

      if label:
        compositeNode.SetLabelVolumeID(label.GetID())
      else:
        compositeNode.SetLabelVolumeID("")

      sliceNode = sliceWidget.mrmlSliceNode()
      sliceNode.SetOrientation(orientation)
      sliceNodesByViewName[viewName] = sliceNode
    return sliceNodesByViewName

  def rotateToVolumePlanes(self, referenceVolume):
    sliceNodes = slicer.util.getNodes('vtkMRMLSliceNode*')
    for name, node in list(sliceNodes.items()):
      node.RotateToVolumePlane(referenceVolume)
    # snap to IJK to try and avoid rounding errors
    sliceLogics = slicer.app.layoutManager().mrmlSliceLogics()
    numLogics = sliceLogics.GetNumberOfItems()
    for n in range(numLogics):
      l = sliceLogics.GetItemAsObject(n)
      l.SnapSliceOffsetToIJK()

  def zoom(self,factor,sliceNodes=None):
    """Zoom slice nodes by factor.
    factor: "Fit" or +/- amount to zoom
    sliceNodes: list of slice nodes to change, None means all.
    """
    if not sliceNodes:
      sliceNodes = slicer.util.getNodes('vtkMRMLSliceNode*')
    layoutManager = slicer.app.layoutManager()
    for sliceNode in list(sliceNodes.values()):
      if factor == "Fit":
        sliceWidget = layoutManager.sliceWidget(sliceNode.GetLayoutName())
        if sliceWidget:
          sliceWidget.sliceLogic().FitSliceToAll()
      else:
        newFOVx = sliceNode.GetFieldOfView()[0] * factor
        newFOVy = sliceNode.GetFieldOfView()[1] * factor
        newFOVz = sliceNode.GetFieldOfView()[2]
        sliceNode.SetFieldOfView( newFOVx, newFOVy, newFOVz )
        sliceNode.UpdateMatrices()

  def viewersPerVolume(self,volumeNodes=None,background=None,label=None,include3D=False,opacity=0.5):
    """ Make an axi/sag/cor(/3D) row of viewers
    for each volume in the scene.
    If background is specified, put it in the background
    of all viewers and make the other volumes be the
    forground.  If label is specified, make it active as
    the label layer of all viewers.
    Return a map of slice nodes indexed by the view name (given or generated).
    """
    import math

    if not volumeNodes:
      volumeNodes = list(slicer.util.getNodes('*VolumeNode*').values())

    if len(volumeNodes) == 0:
      return

    #
    # construct the XML for the layout
    # - one row per volume
    # - viewers for each orientation
    #
    orientations = ('Axial', 'Sagittal', 'Coronal')
    actualViewNames = []
    index = 1
    layoutDescription = ''
    layoutDescription += '<layout type="vertical">\n'
    row = 0
    for volumeNode in volumeNodes:
      layoutDescription += ' <item> <layout type="horizontal">\n'
      column = 0
      for orientation in orientations:
        viewName = volumeNode.GetName() + '-' + orientation
        rgb = [int(round(v*255)) for v in self.lookupTable.GetTableValue(index)[:-1]]
        color = '#%0.2X%0.2X%0.2X' % tuple(rgb)
        layoutDescription += self.sliceViewItemPattern.format(viewName=viewName,orientation=orientation,color=color)
        actualViewNames.append(viewName)
        index += 1
        column += 1
      if include3D:
        # print('TODO: add 3D viewer')
        pass
      layoutDescription += '</layout></item>\n'
    row += 1
    layoutDescription += '</layout>'
    self.assignLayoutDescription(layoutDescription)

    # let the widgets all decide how big they should be
    slicer.app.processEvents()

    # put one of the volumes into each row and set orientations
    layoutManager = slicer.app.layoutManager()
    sliceNodesByViewName = {}
    for volumeNode in volumeNodes:
      for orientation in orientations:
        viewName = volumeNode.GetName() + '-' + orientation
        sliceWidget = layoutManager.sliceWidget(viewName)
        compositeNode = sliceWidget.mrmlSliceCompositeNode()
        if background:
          compositeNode.SetBackgroundVolumeID(background.GetID())
          compositeNode.SetForegroundVolumeID(volumeNode.GetID())
          compositeNode.SetForegroundOpacity(opacity)
        else:
          compositeNode.SetBackgroundVolumeID(volumeNode.GetID())
          compositeNode.SetForegroundVolumeID("")
        if label:
          compositeNode.SetLabelVolumeID(label.GetID())
        else:
          compositeNode.SetLabelVolumeID("")
        sliceNode = sliceWidget.mrmlSliceNode()
        sliceNode.SetOrientation(orientation)
        sliceNodesByViewName[viewName] = sliceNode
    return sliceNodesByViewName

class ViewWatcher:
  """A helper class to manage observers on slice views"""

  def __init__(self):
    # the currentLayoutName is tag on the slice node that corresponds
    # view which should currently be shown in the DataProbe window.
    # Keeping track of this allows us to respond to non-interactor updates
    # to the slice (like from an external tracker) but only in the view where
    # the mouse has most recently entered.
    self.currentLayoutName = None

    # Default observer priority is 0.0, and the widgets have a 0.5 priority
    # so we set this to 1 in order to get events that would
    # otherwise be swallowed.  Since we do not abort the event, this is harmless.
    self.priority = 2

    # keep list of pairs: [observee,tag] so they can be removed easily
    self.observerTags = []
    # keep a map of interactor styles to sliceWidgets so we can easily get sliceLogic
    self.sliceWidgetsPerStyle = {}
    self.refreshObservers()

    # saved cursor for restoring custom after overlays
    self.savedCursor = None

    layoutManager = slicer.app.layoutManager()
    layoutManager.connect('layoutChanged(int)', self.refreshObservers)

    # instance variables filled in by processEvent
    self.sliceWidget = None
    self.sliceView = None
    self.sliceLogic = None
    self.sliceNode = None
    self.interactor = None
    self.xy = (0,0)
    self.xyz = (0,0,0)
    self.ras = (0,0,0)
    self.layerLogics = {}
    self.layerVolumeNodes = {}
    self.savedWidget = None

  def cleanup(self):
    """Virtual method meant to be overridden by the subclass
    Cleans up any observers (or widgets and other instances).
    This is needed because __del__ does not reliably get called.
    """
    layoutManager = slicer.app.layoutManager()
    layoutManager.disconnect('layoutChanged(int)', self.refreshObservers)
    self.removeObservers()

  def removeObservers(self):
    # remove observers and reset
    for observee,tag in self.observerTags:
      observee.RemoveObserver(tag)
    self.observerTags = []
    self.sliceWidgetsPerStyle = {}

  def refreshObservers(self):
    """ When the layout changes, drop the observers from
    all the old widgets and create new observers for the
    newly created widgets"""
    self.removeObservers()
    # get new slice nodes
    layoutManager = slicer.app.layoutManager()
    sliceNodeCount = slicer.mrmlScene.GetNumberOfNodesByClass('vtkMRMLSliceNode')
    for nodeIndex in range(sliceNodeCount):
      # find the widget for each node in scene
      sliceNode = slicer.mrmlScene.GetNthNodeByClass(nodeIndex, 'vtkMRMLSliceNode')
      sliceWidget = layoutManager.sliceWidget(sliceNode.GetLayoutName())
      if sliceWidget:
        # add obserservers and keep track of tags
        style = sliceWidget.sliceView().interactorStyle().GetInteractor()
        self.sliceWidgetsPerStyle[style] = sliceWidget
        events = ("MouseMoveEvent", "EnterEvent", "LeaveEvent")
        for event in events:
          tag = style.AddObserver(event, self.processEvent, self.priority)
          self.observerTags.append([style,tag])
        tag = sliceNode.AddObserver("ModifiedEvent", self.processEvent, self.priority)
        self.observerTags.append([sliceNode,tag])
        sliceLogic = sliceWidget.sliceLogic()
        compositeNode = sliceLogic.GetSliceCompositeNode()
        tag = compositeNode.AddObserver("ModifiedEvent", self.processEvent, self.priority)
        self.observerTags.append([compositeNode,tag])


  def processEvent(self,observee,event):
    if event == 'LeaveEvent':
      self.currentLayoutName = None
    if event == 'EnterEvent':
      sliceWidget = self.sliceWidgetsPerStyle[observee]
      self.currentLayoutName = None
      sliceLogic = sliceWidget.sliceLogic()
      sliceNode = sliceWidget.mrmlSliceNode()
      self.currentLayoutName = sliceNode.GetLayoutName()
    nodeEvent = (observee.IsA('vtkMRMLSliceNode') or
                observee.IsA('vtkMRMLSliceCompositeNode'))
    if nodeEvent:
      # for a slice node, get the corresponding style and
      # set it as the observee so update is made for that sliceWidget
      # if it is the current layout name
      layoutManager = slicer.app.layoutManager()
      sliceWidget = layoutManager.sliceWidget(observee.GetLayoutName())
      if sliceWidget and observee.GetLayoutName() == self.currentLayoutName:
        observee = sliceWidget.sliceView().interactor()
    if observee in self.sliceWidgetsPerStyle:
      self.sliceWidget = self.sliceWidgetsPerStyle[observee]
      self.sliceView = self.sliceWidget.sliceView()
      self.sliceLogic = self.sliceWidget.sliceLogic()
      self.sliceNode = self.sliceWidget.mrmlSliceNode()
      self.interactor = observee
      self.xy = self.interactor.GetEventPosition()
      self.xyz = self.sliceWidget.sliceView().convertDeviceToXYZ(self.xy);
      self.ras = self.sliceWidget.sliceView().convertXYZToRAS(self.xyz)

      self.layerLogics = {}
      self.layerVolumeNodes = {}
      layerLogicCalls = (('L', self.sliceLogic.GetLabelLayer),
                         ('F', self.sliceLogic.GetForegroundLayer),
                         ('B', self.sliceLogic.GetBackgroundLayer))
      for layer,logicCall in layerLogicCalls:
        self.layerLogics[layer] = logicCall()
        self.layerVolumeNodes[layer] = self.layerLogics[layer].GetVolumeNode()

      self.onSliceWidgetEvent(event)

  def onSliceWidgetEvent(self,event):
    """ virtual method called when an event occurs
    on a slice widget.  The instance variables of the class
    will have been filled by the processEvent method above
    """
    pass

  def cursorOff(self,widget):
    """Turn off and save the current cursor so
    the user can see an overlay that tracks the mouse"""
    if self.savedWidget == widget:
      return
    else:
      self.cursorOn()
    self.savedWidget = widget
    self.savedCursor = widget.cursor
    qt_BlankCursor = 10
    widget.setCursor(qt.QCursor(qt_BlankCursor))

  def cursorOn(self):
    """Restore the saved cursor if it exists, otherwise
    just restore the default cursor"""
    if self.savedWidget:
      if self.savedCursor:
        self.savedWidget.setCursor(self.savedCursor)
      else:
        self.savedWidget.unsetCursor()
    self.savedWidget = None
    self.savedCursor = None


class LayerReveal(ViewWatcher):
  """Track the mouse and show a reveal view"""

  def __init__(self,parent=None,width=400,height=400,showWidget=False,scale=False):
    super().__init__()
    self.width = width
    self.height = height
    self.showWidget = showWidget
    self.scale = scale
    self.renderer = None

    # utility Qt instances for use in methods
    self.gray = qt.QColor()
    self.gray.setRedF(0.5)
    self.gray.setGreenF(0.5)
    self.gray.setBlueF(0.5)
    # a painter to use for various jobs
    self.painter = qt.QPainter()

    # make a qwidget display
    if self.showWidget:
      self.frame = qt.QFrame(parent)
      mw = slicer.util.mainWindow()
      self.frame.setGeometry(mw.x, mw.y, self.width, self.height)
      self.frameLayout = qt.QVBoxLayout(self.frame)
      self.label = qt.QLabel()
      self.frameLayout.addWidget(self.label)
      self.frame.show()

    # make an image actor in the slice view
    self.vtkImage = vtk.vtkImageData()

    self.mrmlUtils = slicer.qMRMLUtils()
    self.imageMapper = vtk.vtkImageMapper()
    self.imageMapper.SetColorLevel(128)
    self.imageMapper.SetColorWindow(255)
    self.imageMapper.SetInputData(self.vtkImage)
    self.actor2D = vtk.vtkActor2D()
    self.actor2D.SetMapper(self.imageMapper)

  def cleanup(self):
    # clean up widget
    self.frame = None
    # clean up image actor
    if self.renderer:
      self.renderer.RemoveActor(self.actor2D)
    self.cursorOn()
    if self.sliceView:
      self.sliceView.scheduleRender()
    try:
      super().cleanup()
    except TypeError:
      # Apparently during reloading of a scripted
      # module the superclass is not in the
      # correct space, so ignore the error
      # because it doesn't happen in normal use
      # when this is called during toggling
      # of the LayerReveal cursor state
      pass

  def onSliceWidgetEvent(self,event):
    """Update reveal displays"""
    revealPixmap = self.revealPixmap(self.xy)

    #widget
    if self.showWidget:
      self.label.setPixmap(revealPixmap)

    # actor
    self.renderWindow = self.sliceView.renderWindow()
    self.renderer = self.renderWindow.GetRenderers().GetItemAsObject(0)

    if event == "LeaveEvent" or not self.layerVolumeNodes['F']:
      self.renderer.RemoveActor(self.actor2D)
      self.cursorOn()
      self.sliceView.forceRender()
    elif event == "EnterEvent":
      self.renderer.AddActor2D(self.actor2D)
      if self.layerVolumeNodes['F'] and (self.layerVolumeNodes['F'] != self.layerVolumeNodes['B']):
        self.cursorOff(self.sliceWidget)
    else:
      self.mrmlUtils.qImageToVtkImageData(revealPixmap.toImage(),self.vtkImage)
      self.imageMapper.SetInputData(self.vtkImage)
      x,y = self.xy
      self.actor2D.SetPosition(x- self.width/2,y-self.height/2)
      self.sliceView.forceRender()

  def revealPixmap(self, xy):
    """fill a pixmap with an image that has a reveal pattern
    at xy with the fg drawn over the bg"""

    # Get QImages for the two layers
    bgVTKImage = self.layerLogics['B'].GetImageData()
    fgVTKImage = self.layerLogics['F'].GetImageData()
    bgQImage = qt.QImage()
    fgQImage = qt.QImage()
    slicer.qMRMLUtils().vtkImageDataToQImage(bgVTKImage, bgQImage)
    slicer.qMRMLUtils().vtkImageDataToQImage(fgVTKImage, fgQImage)

    # get the geometry of the focal point (xy) and images
    # noting that vtk has the origin at the bottom left and qt has
    # it at the top left.  yy is the flipped version of y
    imageWidth = bgQImage.width()
    imageHeight = bgQImage.height()
    x,y=xy
    yy = imageHeight-y

    #
    # make a generally transparent image,
    # then fill quadrants with the fg image
    #
    overlayImage = qt.QImage(imageWidth, imageHeight, qt.QImage().Format_ARGB32)
    overlayImage.fill(0)

    halfWidth = imageWidth//2
    halfHeight = imageHeight//2
    topLeft = qt.QRect(0,0, x, yy)
    bottomRight = qt.QRect(x, yy, imageWidth-x-1, imageHeight-yy-1)

    self.painter.begin(overlayImage)
    self.painter.drawImage(topLeft, fgQImage, topLeft)
    self.painter.drawImage(bottomRight, fgQImage, bottomRight)
    self.painter.end()

    # draw the bg and fg on top of gray background
    compositePixmap = qt.QPixmap(self.width,self.height)
    compositePixmap.fill(self.gray)
    self.painter.begin(compositePixmap)
    self.painter.drawImage(
        -1 * (x  -self.width//2),
        -1 * (yy -self.height//2),
        bgQImage)
    self.painter.drawImage(
        -1 * (x  -self.width//2),
        -1 * (yy -self.height//2),
        overlayImage)
    self.painter.end()

    if self.scale:
      compositePixmap = self.scalePixmap(compositePixmap)

    # draw a border around the pixmap
    self.painter.begin(compositePixmap)
    self.pen = qt.QPen()
    self.color = qt.QColor("#FF0")
    self.color.setAlphaF(0.3)
    self.pen.setColor(self.color)
    self.pen.setWidth(5)
    self.pen.setStyle(3) # dotted line (Qt::DotLine)
    self.painter.setPen(self.pen)
    rect = qt.QRect(1, 1, self.width-2, self.height-2)
    self.painter.drawRect(rect)
    self.painter.end()

    return compositePixmap

  def scalePixmap(self,pixmap):
    # extract the center of the pixmap and then zoom
    halfWidth = self.width//2
    halfHeight = self.height//2
    quarterWidth = self.width//4
    quarterHeight = self.height//4
    centerPixmap = qt.QPixmap(halfWidth,halfHeight)
    centerPixmap.fill(self.gray)
    self.painter.begin(centerPixmap)
    fullRect = qt.QRect(0,0,halfWidth,halfHeight)
    centerRect = qt.QRect(quarterWidth, quarterHeight, halfWidth, halfHeight)
    self.painter.drawPixmap(fullRect, pixmap, centerRect)
    self.painter.end()
    scaledPixmap = centerPixmap.scaled(self.width, self.height)

    return scaledPixmap


class CompareVolumesTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self,scenario=None):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    if scenario == "Three Volume":
      self.test_CompareVolumes1()
    elif scenario == "View Watcher":
      self.test_CompareVolumes2()
    elif scenario == "LayerReveal":
      self.test_CompareVolumes3()
    else:
      self.test_CompareVolumes1()
      self.test_CompareVolumes2()
      self.test_CompareVolumes3()

  def test_CompareVolumes1(self):
    """ Test modes with 3 volumes.
    """

    m = slicer.util.mainWindow()
    m.moduleSelector().selectModule('CompareVolumes')

    self.delayDisplay("Starting the test")

    # first with two volumes
    from SampleData import SampleDataLogic
    head = SampleDataLogic().downloadMRHead()
    brain = SampleDataLogic().downloadDTIBrain()
    logic = CompareVolumesLogic()
    logic.viewerPerVolume()
    self.delayDisplay('Should be one row with two columns')
    logic.viewerPerVolume(volumeNodes=(brain,head), viewNames=('brain', 'head'))
    self.delayDisplay('Should be two columns, with names')

    # now with three volumes
    otherBrain = SampleDataLogic().downloadMRBrainTumor1()
    logic.viewerPerVolume()
    logic.viewerPerVolume(volumeNodes=(brain,head,otherBrain), viewNames=('brain', 'head','otherBrain'))
    self.delayDisplay('Should be one row with three columns')

    logic.viewerPerVolume(volumeNodes=(brain,head,otherBrain), viewNames=('brain', 'head','otherBrain'), orientation='Sagittal')
    self.delayDisplay('same thing in sagittal')

    logic.viewerPerVolume(volumeNodes=(brain,head,otherBrain), viewNames=('brain', 'head','otherBrain'), orientation='Coronal')
    self.delayDisplay('same thing in coronal')

    anotherHead = SampleDataLogic().downloadMRHead()
    logic.viewerPerVolume(volumeNodes=(brain,head,otherBrain,anotherHead), viewNames=('brain', 'head','otherBrain','anotherHead'), orientation='Coronal')
    self.delayDisplay('now four volumes, with three columns and two rows')


    logic.viewersPerVolume(volumeNodes=(brain,head))
    self.delayDisplay('now axi/sag/cor for two volumes')

    logic.viewersPerVolume(volumeNodes=(brain,head,otherBrain))
    self.delayDisplay('now axi/sag/cor for three volumes')

    self.delayDisplay('Test passed!')

  def test_CompareVolumes2(self):
    """
    Test modes with view watcher class.
    """

    m = slicer.util.mainWindow()
    m.moduleSelector().selectModule('CompareVolumes')

    self.delayDisplay("Starting View Watcher test")

    watcher = ViewWatcher()

    # first with two volumes
    from SampleData import SampleDataLogic
    head = SampleDataLogic().downloadMRHead()
    brain = SampleDataLogic().downloadDTIBrain()
    logic = CompareVolumesLogic()
    logic.viewerPerVolume()
    self.delayDisplay('Should be one row with two columns')
    logic.viewerPerVolume(volumeNodes=(brain,head), viewNames=('brain', 'head'))
    self.delayDisplay('Should be two columns, with names')

    watcher.cleanup()

    self.delayDisplay('Test passed!')

  def test_CompareVolumes3(self):
    """
    Test LayerReveal

    From the python console:
slicer.util.mainWindow().moduleSelector().selectModule("CompareVolumes"); slicer.modules.CompareVolumesWidget.onReloadAndTest(scenario="LayerReveal"); reveal = LayerReveal()
    """

    self.delayDisplay("Starting LayerReveal test")

    # first with two volumes
    from SampleData import SampleDataLogic
    head = SampleDataLogic().downloadMRHead()
    dti = SampleDataLogic().downloadDTIBrain()
    tumor = SampleDataLogic().downloadMRBrainTumor1()
    logic = CompareVolumesLogic()
    logic.viewerPerVolume()
    self.delayDisplay('Should be one row with two columns')
    logic.viewerPerVolume(volumeNodes=(dti,tumor,head),
                            background=dti, viewNames=('dti', 'tumor', 'head'))
    self.delayDisplay('Should be three columns, with dti in foreground')

    # the name of the view was givein the the call to viewerPerVolume above.
    # here we ask the layoutManager to give us the corresponding sliceWidget
    # from which we can get the interactorStyle so we can simulate events
    layoutManager = slicer.app.layoutManager()
    sliceWidget = layoutManager.sliceWidget('head')
    style = sliceWidget.sliceView().interactorStyle().GetInteractor()

    for scale in (False,True):
      for size in (100,400):
        # create a reveal cursor to test
        reveal = LayerReveal(width=size,height=size,scale=scale)
        reveal.processEvent(style, "EnterEvent")
        steps = 300
        for step in range(0,steps):
          t = step//float(steps)
          px = int(t * sliceWidget.width)
          py = int(t * sliceWidget.height)
          style.SetEventPosition(px,py)
          reveal.processEvent(style, "MouseMoveEvent")
        reveal.processEvent(style, "LeaveEvent")
        reveal.cleanup()
        self.delayDisplay(f'Scale {scale}, size {size}')


    self.delayDisplay('Should have just seen reveal cursor move through head view')

    self.delayDisplay('Test passed!')
