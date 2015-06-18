#!/usr/bin/env python

# Input file editor for openQCD
# Python 2.7 and PyQt4

#NOTES:
# Currently assumes Action 0 is the gauge action - need to add code to deal with other situations when loading an input file, maybe the easiest is just to first change the action indices in the file?

# The gui is imported from gui.py, which in turn is generated from gui.ui with the command pyuic4
# The file gui.ui can be edited using designer-qt4
# Only routines that are directly invoked by user actions are included in this file - all others are imported from consistency.py and utils.py

# In general, each parameter in the input file is represented by a pyqt widget, named accordingly.
# The name goes like "section___option", where section and option are separated by 4 underscores, and any spaces in the section name are replaced with an underscore
# For example, in the section "[Run name]" there is an option "name". This is displayed/edited in the pyqtQLineEdit widget in the gui named "Run_name____name"
# Whenever the contents of this (or any widget) change, the relevant section and option are determined based on this formatting of the widget name, and the parameter in the input file is updated
# If the widget is disabled, then the corresponding parameter is removed from the input file

#import os
#import subprocess
import sys
import webbrowser 
from PyQt4 import QtCore, QtGui, Qt
from gui import Ui_Form
import StringIO
import ConfigParser

import consistency
import utils

#Class for validating user input as integer
class MyIntValidator(Qt.QIntValidator):
   def __init__(self, bottom, top, parent = None):
      Qt.QIntValidator.__init__(self, bottom, top, parent)

   def validate(self, input, pos):
      state, pos = Qt.QIntValidator.validate(self, input, pos)
      if input.isEmpty() or input == '.':
         return Qt.QValidator.Invalid, pos
      if state != Qt.QValidator.Acceptable:
         return Qt.QValidator.Invalid, pos
      return Qt.QValidator.Acceptable, pos

#Main GUI class
class MainGUI(QtGui.QWidget):
   def __init__(self, parent=None):
      #GUI Initialisation
      QtGui.QWidget.__init__(self, parent)
      self.ui = Ui_Form()
      self.ui.setupUi(self)
      
      #Config initialisation
      #store all parameters in self.config
      self.config = ConfigParser.RawConfigParser()
      #preserve case of parameters
      self.config.optionxform = str

      #setup basic consistency checks, e.g beta must be a positive double, RNG seed must be a positive integer, etc.
      #list of text fields that have to be positive doubles
      self.listDoubleFields=[self.ui.Lattice_parameters____beta,self.ui.Trajectory_length____tau,self.ui.Wilson_flow____eps,self.ui.Solver____res, self.ui.Deflation_subspace_generation____kappa, self.ui.Deflation_subspace_generation____mu, self.ui.Deflation_projection____res, self.ui.Deflation_update_scheme____dtau,  self.ui.Boundary_conditions____cF,   self.ui.Boundary_conditions____cG,   self.ui.Boundary_conditions____cFprime,   self.ui.Boundary_conditions____cGprime]
      #list of text fields that have to be positive integers
      self.listIntegerFields=[self.ui.Random_number_generator____seed,self.ui.MD_trajectories____nth, self.ui.MD_trajectories____ntr,self.ui.MD_trajectories____dtr_log, self.ui.MD_trajectories____dtr_ms, self.ui.MD_trajectories____dtr_cnfg, self.ui.Wilson_flow____nstep, self.ui.Wilson_flow____dnms, self.ui.Solver____nmx, self.ui.Solver____nkv, self.ui.Solver____nmr, self.ui.Solver____ncy, self.ui.Force____ncr, self.ui.Rational____degree, self.ui.Deflation_subspace____Ns, self.ui.Deflation_subspace_generation____ninv, self.ui.Deflation_subspace_generation____nmr, self.ui.Deflation_subspace_generation____ncy, self.ui.Deflation_projection____nkv, self.ui.Deflation_projection____nmx, self.ui.Deflation_update_scheme____nsm]
      #list of text fields that have to be a list of positive doubles
      self.listListDoubleFields=[self.ui.Lattice_parameters____kappa,self.ui.HMC_parameters____mu, self.ui.Rational____range,   self.ui.Boundary_conditions____phi,   self.ui.Boundary_conditions____phiprime]

      #Force these input fields to be integers
      for field in self.listIntegerFields:
         field.setValidator(MyIntValidator(1, 100000000, field))

      #link user actions (e.g. editing text in a widget) to code (e.g. updating appropriate parameter in input file)
      self.initSignalsAndSlots()

      #make a default minimal initial input file
      self.MDIntLevels=0
      self.changecmbBCS()
      utils.setVarALL(self)
      self.config.add_section("Action 0")
      self.config.set("Action 0","action","ACG")
      self.addIntLevel()
      utils.populateMDInt(self)

   def initSignalsAndSlots(self):
      #link user actions (e.g. editing text in a widget) to code (e.g. updating appropriate parameter in input file)
      
      #User clicks a button
      self.ui.btnSave.clicked.connect(self.writeInputFile)
      self.ui.btnOpen.clicked.connect(self.readInputFile)
      self.ui.btnHelp.clicked.connect(self.help)
      self.ui.btnAddIntLevel.clicked.connect(self.addIntLevel)
      self.ui.btnRemoveIntLevel.clicked.connect(self.removeIntLevel)
      self.ui.btnAddSolver.clicked.connect(self.addSolver)
      self.ui.btnRemoveSolver.clicked.connect(self.removeSolver)
      self.ui.btnAddRAT.clicked.connect(self.addRAT)
      self.ui.btnRemoveRAT.clicked.connect(self.removeRAT)
      self.ui.btnAddAction.clicked.connect(self.addAction)
      self.ui.btnRemoveAction.clicked.connect(self.removeAction)

      #User (or code) changes tab
      self.ui.tabMain.currentChanged.connect(self.changeTab)
      #User changes any text field
      for txt in self.findChildren(QtGui.QLineEdit):
         txt.editingFinished.connect(self.changeText)
      #User changes any combobox selection
      for txt in self.findChildren(QtGui.QComboBox):
         txt.activated.connect(self.changeCombo)
      #User toggles a radiobutton
      for rad in self.findChildren(QtGui.QRadioButton):
         rad.toggled.connect(self.changeRadio)
      
      #User (or code) changes a specific combobox selection
      self.ui.Boundary_conditions____type.currentIndexChanged.connect(self.changecmbBCS)
      self.ui.Solver____solver.currentIndexChanged.connect(self.changecmbSolver)
      self.ui.Action____action.currentIndexChanged.connect(self.changecmbAction)

      #User (or code) chooses an item in a list
      self.ui.listSolvers.itemSelectionChanged.connect(self.selectSolver)
      self.ui.listRAT.itemSelectionChanged.connect(self.selectRAT)
      self.ui.listActions.itemSelectionChanged.connect(self.selectAction)

   def changeTab(self,index):
      #When tab is changed, update fields if required
      if self.ui.tabMain.tabText(index)=="Action":
         utils.populateActionFields(self)
         self.ui.listActions.setCurrentRow(self.ui.listActions.count()-1)
      elif self.ui.tabMain.tabText(index)=="MD Integration":
         utils.populateMDInt(self)
      elif self.ui.tabMain.tabText(index)=="Input File Preview":
         self.ui.txtInputFile.setPlainText(utils.generateInputFile(self))
      
   def changecmbBCS(self):
      #enable/disable relevant fields
      if self.ui.Boundary_conditions____type.currentIndex()==0:
         #open
         self.ui.Boundary_conditions____cG.setEnabled(True)
         self.ui.Boundary_conditions____cF.setEnabled(True)
         self.ui.Boundary_conditions____phi.setEnabled(False)
         self.ui.Boundary_conditions____cGprime.setEnabled(False)
         self.ui.Boundary_conditions____cFprime.setEnabled(False)
         self.ui.Boundary_conditions____phiprime.setEnabled(False)
      elif self.ui.Boundary_conditions____type.currentIndex()==1:        
         #sf
         self.ui.Boundary_conditions____cG.setEnabled(True)
         self.ui.Boundary_conditions____cF.setEnabled(True)
         self.ui.Boundary_conditions____phi.setEnabled(True)
         self.ui.Boundary_conditions____cGprime.setEnabled(False)
         self.ui.Boundary_conditions____cFprime.setEnabled(False)
         self.ui.Boundary_conditions____phiprime.setEnabled(True)
      elif self.ui.Boundary_conditions____type.currentIndex()==2:
         #open-sf
         self.ui.Boundary_conditions____cG.setEnabled(True)
         self.ui.Boundary_conditions____cF.setEnabled(True)
         self.ui.Boundary_conditions____phi.setEnabled(False)
         self.ui.Boundary_conditions____cGprime.setEnabled(True)
         self.ui.Boundary_conditions____cFprime.setEnabled(True)
         self.ui.Boundary_conditions____phiprime.setEnabled(True)
      elif self.ui.Boundary_conditions____type.currentIndex()==3:
         #periodic
         self.ui.Boundary_conditions____cG.setEnabled(False)
         self.ui.Boundary_conditions____cF.setEnabled(False)
         self.ui.Boundary_conditions____phi.setEnabled(False)
         self.ui.Boundary_conditions____cGprime.setEnabled(False)
         self.ui.Boundary_conditions____cFprime.setEnabled(False)
         self.ui.Boundary_conditions____phiprime.setEnabled(False)
      #update affected fields in config
      utils.setVarTxt(self.ui.Boundary_conditions____cG, self)
      utils.setVarTxt(self.ui.Boundary_conditions____cF, self)
      utils.setVarTxt(self.ui.Boundary_conditions____phi, self)
      utils.setVarTxt(self.ui.Boundary_conditions____cGprime, self)
      utils.setVarTxt(self.ui.Boundary_conditions____cFprime, self)
      utils.setVarTxt(self.ui.Boundary_conditions____phiprime, self)
      
   def changecmbSolver(self):
      #Enable/disable appropriate options based on combobox indices
      if self.ui.Solver____solver.currentIndex()==0 or self.ui.Solver____solver.currentIndex()==1:
         self.ui.Solver____nkv.setEnabled(False)
         self.ui.Solver____isolv.setEnabled(False)
         self.ui.Solver____nmr.setEnabled(False)
         self.ui.Solver____ncy.setEnabled(False)
      else:
         self.ui.Solver____nkv.setEnabled(True)
         self.ui.Solver____isolv.setEnabled(True)
         self.ui.Solver____nmr.setEnabled(True)
         self.ui.Solver____ncy.setEnabled(True)
      utils.setVarTxt(self.ui.Solver____nkv, self)
      utils.setVarCmb(self.ui.Solver____isolv, self)
      utils.setVarTxt(self.ui.Solver____nmr, self)
      utils.setVarTxt(self.ui.Solver____ncy, self)
      #update solver description in listbox
      if self.ui.listSolvers.count()>0:
         index=int(self.ui.lblSolverIndex.text())
         self.ui.listSolvers.item(self.ui.listSolvers.currentRow()).setText(str(index)+" ["+str(self.ui.Solver____solver.currentText())+"]")
         utils.setVarCmb(self.ui.Solver____solver, self)

      #Check if we need SAP (i.e. have some SAP solvers)
      weNeedSAP=False
      if self.ui.Solver____solver.currentIndex() in [2, 3]:
         weNeedSAP=True
      else:
         for index in range(self.ui.listSolvers.count()):
            if "SAP" in str(self.ui.listSolvers.item(index).text()):
               weNeedSAP=True
      if weNeedSAP and not self.ui.SAP____bs.isEnabled():
         self.ui.SAP____bs.setEnabled(True)
         utils.setVarTxt(self.ui.SAP____bs, self)
      elif not weNeedSAP and self.ui.SAP____bs.isEnabled():
         self.ui.SAP____bs.setEnabled(False)
         self.config.remove_section("SAP")

      #Check if we need deflation (i.e. have some DFL solvers)
      weNeedDFL=False
      if self.ui.Solver____solver.currentIndex()==3:
         weNeedDFL=True
      else:
         for index in range(self.ui.listSolvers.count()):
            if "DFL" in str(self.ui.listSolvers.item(index).text()):
               weNeedDFL=True
      if weNeedDFL and not self.ui.groupDFLsubspace.isEnabled():
         self.ui.groupDFLsubspace.setEnabled(True)
         self.ui.groupDFLprojection.setEnabled(True)
         self.ui.groupDFLupdate.setEnabled(True)
         for txt in self.ui.tabDeflation.findChildren(QtGui.QLineEdit):
            utils.setVarTxt(txt, self)
      elif not weNeedDFL and self.ui.groupDFLsubspace.isEnabled():
         self.ui.groupDFLsubspace.setEnabled(False)
         self.ui.groupDFLprojection.setEnabled(False)
         self.ui.groupDFLupdate.setEnabled(False)
         self.config.remove_section("Deflation subspace")
         self.config.remove_section("Deflation subspace generation")
         self.config.remove_section("Deflation projection")
         self.config.remove_section("Deflation update scheme")

   def changecmbAction(self):
      if self.ui.Action____action.currentIndex()==4 or self.ui.Action____action.currentIndex()==5:
         self.ui.Action____imuX0.setEnabled(False)
         self.ui.Action____imuX1.setEnabled(False)
         self.ui.Action____ispX1.setEnabled(False)
         self.ui.Action____iratX0.setEnabled(True)
         self.ui.Action____iratX1.setEnabled(True)
         self.ui.Action____iratX2.setEnabled(True)
      else:
         self.ui.Action____iratX0.setEnabled(False)
         self.ui.Action____iratX1.setEnabled(False)
         self.ui.Action____iratX2.setEnabled(False)
         if self.ui.Action____action.currentIndex()==0 or self.ui.Action____action.currentIndex()==2:
            self.ui.Action____imuX0.setEnabled(True)
            self.ui.Action____imuX1.setEnabled(False)
            self.ui.Action____ispX1.setEnabled(False)
         else:
            self.ui.Action____imuX0.setEnabled(True)
            self.ui.Action____imuX1.setEnabled(True)
            self.ui.Action____ispX1.setEnabled(True)
      if self.ui.listActions.count() > 0:
         index=str(int(self.ui.lblActionIndex.text()))
         #update force parameters
         self.config.set("Force "+index, "force",  "FRF"+str(self.ui.Action____action.currentText())[3:])
         #update actiondescription in listbox
         self.ui.listActions.item(self.ui.listActions.currentRow()).setText(index+" ["+str(self.ui.Action____action.currentText())+"]")
         utils.setVarCmb(self.ui.Action____action, self)
   def changecmbMDint(self):
      #Update variables in config using data in combobox field
      cmb = self.sender()
      utils.setVarCmb(cmb, self)
      level = int(self.ui.gridLayout.getItemPosition(self.ui.gridLayout.indexOf(self.sender()))[1])
      if cmb.currentIndex()==1:
         #show lambda field
         self.ui.gridLayout.itemAtPosition(2,level).widget().setEnabled(True)
      else:
         #hide lambda field
         self.ui.gridLayout.itemAtPosition(2,level).widget().setEnabled(False)
      utils.setVarTxt(self.ui.gridLayout.itemAtPosition(2,level).widget(), self)
   def changeRadio(self):
      self.ui.txtInputFile.setPlainText(utils.generateInputFile(self))
   def selectSolver(self):
      if self.ui.listSolvers.isEnabled():
         utils.getSolver(utils.getIndex(self.ui.listSolvers), self)
   def selectRAT(self):
      if self.ui.listRAT.isEnabled():
         utils.getRAT(utils.getIndex(self.ui.listRAT), self)

   def selectAction(self):
      if self.ui.listActions.isEnabled():
         utils.getAction(utils.getIndex(self.ui.listActions), self)
   def addSolver(self,index=99,sectionExists=False):
      #If sectionExists is True, then adds an existing (in the config) solver with the supplied index.
      #If not then makes a new solver with a new index
      self.ui.groupSolver.setEnabled(True)
      self.ui.btnRemoveSolver.setEnabled(True)
      self.ui.listSolvers.setEnabled(True)
      #If we are not given an index, then generate one and write a default set of params to that config section
      if not sectionExists:
         index = utils.makeValidIndex(self.ui.listSolvers)
         sec="Solver "+str(index)
         self.config.add_section(sec)
         self.config.set(sec,"solver","CGNE")
         self.config.set(sec,"nmx","1024")
         self.config.set(sec,"res","1.e-10")
      self.ui.listSolvers.addItem(str(index))
      self.ui.listSolvers.setCurrentRow(self.ui.listSolvers.count()-1)
      utils.getSolver(index, self)   

   def addRAT(self,index=99,sectionExists=False):
      #If sectionExists is True, then adds an existing (in the config) solver with the supplied index.
      #If not then makes a new solver with a new index
      self.ui.groupRAT.setEnabled(True)
      self.ui.btnRemoveRAT.setEnabled(True)
      self.ui.listRAT.setEnabled(True)
      #If we are not given an index, then generate one and write a default set of params to that config section
      if not sectionExists:
         index = utils.makeValidIndex(self.ui.listRAT)
         sec="Rational "+str(index)
         self.config.add_section(sec)
         self.config.set(sec,"degree","9")
         self.config.set(sec,"range","0.03 6.10")
      self.ui.listRAT.addItem(str(index))
      self.ui.listRAT.setCurrentRow(self.ui.listRAT.count()-1)
      utils.getRAT(index, self)

   def addAction(self,index=99,sectionExists=False):
      #If sectionExists is True, then adds an existing (in the config) solver with the supplied index.
      #If not then makes a new solver with a new index
      self.ui.groupAction.setEnabled(True)
      self.ui.btnRemoveAction.setEnabled(True)
      self.ui.listActions.setEnabled(True)
      #ignore gauge action
      sec="Action "+str(index)
      if self.config.has_option(sec,"action") and self.config.get(sec,"action")=="ACG":
         self.gaugeActionIndex=index
         #TODO: deal with this case properly (i.e. convert it to index zero and update others accordingly)
         return
      #If we are not given an index, then generate one and write a default set of params to that config section
      if not sectionExists:
         index = utils.makeValidIndex(self.ui.listActions)
         sec="Action "+str(index)
         self.config.add_section(sec)
         #add default action to config
         self.config.set(sec, "action",  "ACF_TM1")
         self.config.set(sec, "ipf",  "0")
         self.config.set(sec, "im0",  "0")
         self.config.set(sec, "imu",  "0")
         self.config.set(sec, "isp",  "0")
#         self.config.set(sec, "ncr",  "1")
         sec="Force "+str(index)
         self.config.add_section(sec)
         #add corresponding force to config
         self.config.set(sec, "force",  "FRF_TM1")
         self.config.set(sec, "isp",  "0")
         self.config.set(sec, "ncr",  "1")
      self.ui.listActions.addItem(str(index))
      self.ui.listActions.setCurrentRow(self.ui.listActions.count()-1)
      utils.getAction(index, self)

   def addIntLevel(self, index=99,sectionExists=False):
      self.MDIntLevels+=1
      if self.MDIntLevels > 0:
         self.ui.btnRemoveIntLevel.setEnabled(True)
      strLevel = "Level_"+str(self.MDIntLevels-1)
      label = QtGui.QLabel(self.ui.tabMDint)
      label.setText(strLevel.replace("_"," "))
      self.ui.gridLayout.addWidget(label, 0, self.MDIntLevels, 1, 1)
      txt = QtGui.QLineEdit(self.ui.tabMDint)
      txt.setObjectName(strLevel+"____lambda")
      self.listDoubleFields.append(txt)
      txt.editingFinished.connect(self.changeText)
      self.ui.gridLayout.addWidget(txt, 2, self.MDIntLevels, 1, 1)
      if utils.getVarTxt(txt, self) == False:
         txt.setText("0.19")
         utils.setVarTxt(txt, self)
      txt = QtGui.QLineEdit(self.ui.tabMDint)
      txt.setValidator(MyIntValidator(1, 100000000, txt))
      txt.setObjectName("Level_"+str(self.MDIntLevels-1)+"____nstep")
      txt.editingFinished.connect(self.changeText)
      self.ui.gridLayout.addWidget(txt, 3, self.MDIntLevels, 1, 1)
      if utils.getVarTxt(txt, self) == False:
         txt.setText("1")
         utils.setVarTxt(txt, self)
      cmb = QtGui.QComboBox(self.ui.tabMDint)
      cmb.setObjectName(strLevel+"____integrator")
      cmb.addItem("LPFR [Leapfrog]")
      cmb.addItem("OMF2 [2nd Order OMF]")
      cmb.addItem("OMF4 [4th Order OMF]")
      cmb.currentIndexChanged.connect(self.changecmbMDint)
      self.ui.gridLayout.addWidget(cmb, 1, self.MDIntLevels, 1, 1)
      if utils.getVarCmb(cmb, self)==False:
         cmb.setCurrentIndex(2)
      list = QtGui.QListWidget(self.ui.tabMDint)
      list.setDragEnabled(True)
      list.setSortingEnabled(True)
      list.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
      list.setDefaultDropAction(QtCore.Qt.MoveAction)
      list.setObjectName(strLevel+"____forces")
      var="ncr"
      if self.config.has_option("Level "+str(self.MDIntLevels-1),"forces"):
         s = str(self.config.get("Level "+str(self.MDIntLevels-1),"forces"))
         for i in s.split():
            list.addItem(i)
      self.ui.gridLayout.addWidget(list, 4, self.MDIntLevels, 1, 1)


   def removeSolver(self):
      index=utils.getIndex(self.ui.listSolvers)
      if self.ui.listSolvers.count() < 2:
         self.ui.btnRemoveSolver.setEnabled(False)
         self.ui.groupSolver.setEnabled(False)
         self.ui.listSolvers.setEnabled(False)
      self.ui.listSolvers.takeItem(self.ui.listSolvers.currentRow())
      self.config.remove_section("Solver "+str(index))
      if self.ui.listSolvers.count() > 0:
         self.ui.listSolvers.setCurrentRow(self.ui.listSolvers.count()-1)

   def removeRAT(self):
      index=utils.getIndex(self.ui.listRAT)
      if self.ui.listRAT.count() < 2:
         self.ui.btnRemoveRAT.setEnabled(False)
         self.ui.groupRAT.setEnabled(False)
         self.ui.listRAT.setEnabled(False)
      self.ui.listRAT.takeItem(self.ui.listRAT.currentRow())
      self.config.remove_section("Rational "+str(index))
      if self.ui.listRAT.count() > 0:
         self.ui.listRAT.setCurrentRow(self.ui.listRAT.count()-1)      

   def removeAction(self):
      index=utils.getIndex(self.ui.listActions)
      if self.ui.listActions.count() < 2:
         self.ui.btnRemoveAction.setEnabled(False)
         self.ui.groupAction.setEnabled(False)
         self.ui.listActions.setEnabled(False)
      self.ui.listActions.takeItem(self.ui.listActions.currentRow())
      self.config.remove_section("Action "+str(index))
      self.config.remove_section("Force "+str(index))
      if self.ui.listActions.count() > 0:
         self.ui.listActions.setCurrentRow(self.ui.listActions.count()-1)      


   def removeIntLevel(self):
      #Move any forces in level to be removed to next level
      if self.MDIntLevels > 1:
         wid = self.ui.gridLayout.itemAtPosition(4,self.MDIntLevels).widget()
         for i in range(wid.count()):
            self.ui.gridLayout.itemAtPosition(4,self.MDIntLevels-1).widget().addItem(wid.item(i).text())
      #Update config
      utils.setVarALL(self)
      #remove integration level from gui
      for x in range(0,5):
         wid = self.ui.gridLayout.itemAtPosition(x,self.MDIntLevels).widget()
         self.ui.gridLayout.removeWidget(wid)
         wid.setParent(None)
      self.MDIntLevels-=1
      if self.MDIntLevels==1:
         self.ui.btnRemoveIntLevel.setEnabled(False)
      #Remove section from config
      self.config.remove_section("Level "+str(self.MDIntLevels))

   def changeText(self):
      #called when user changes a text field - performs params consistency check & updates edited text field in config
      consistent=0
      utils.setVarTxt(self.sender(), self)
      for txt in self.listListDoubleFields:
         consistent+=consistency.isListOfPositiveDoubles(txt, "Must be a list of positive doubles (e.g. 2.123 5e-3 0.1243)")
      for txt in self.listDoubleFields:
         consistent+=consistency.isPositiveDouble(txt, "Must be a positive double (e.g. 0.165, or 1.3e-1)")
      consistent+=consistency.isIntegerMultiple(self.ui.Wilson_flow____nstep,self.ui.Wilson_flow____dnms,"Numer of integration steps must be an integer multiple of the measurement frequency")
      consistent+=consistency.isIntegerMultiple(self.ui.MD_trajectories____dtr_ms,self.ui.MD_trajectories____dtr_log,"Measurement frequency must be an integer multiple of log freqency")
      consistent+=consistency.isIntegerMultiple(self.ui.MD_trajectories____dtr_cnfg,self.ui.MD_trajectories____dtr_ms,"Configuration save frequency must be an integer multiple of measurement freqency")
      consistent+=consistency.isIntegerMultiple(self.ui.MD_trajectories____nth,self.ui.MD_trajectories____dtr_cnfg,"Number of thermalisation MD trajectories must be an integer multiple of configuration save freqency")
      consistent+=consistency.isIntegerMultiple(self.ui.MD_trajectories____ntr,self.ui.MD_trajectories____dtr_cnfg,"Number of MD trajectories must be an integer multiple of configuration save freqency")
      consistent+=consistency.isListOfNPositiveInts(self.ui.SAP____bs,4,"Must be a list of 4 positive integers, e.g. 4 6 6 4")
      consistent+=consistency.isListOfNPositiveInts(self.ui.Deflation_subspace____bs,4,"Must be a list of 4 positive integers, e.g. 4 6 6 4")
      if consistent>0:
         self.ui.btnSave.setEnabled(False)
      else:
         self.ui.btnSave.setEnabled(True)
         
   def changeCombo(self):
      #called when user changes a combobox - updates edited field 
      utils.setVarCmb(self.sender(), self)

   def readInputFile(self):
      #get filename from user
      fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '~/default.in')
      if fname:
         #clear all current parameters
         while self.MDIntLevels > 0:
            self.removeIntLevel()
         while self.ui.listSolvers.count()>0:
            self.removeSolver()
         while self.ui.listRAT.count()>0:
            self.removeRAT()
         while self.ui.listActions.count()>0:
            self.removeAction()
         strTitle = "["+str(fname) + "] - openQCD Input File Editor"
         self.setWindowTitle(strTitle)
         #create new config
         self.config = ConfigParser.RawConfigParser()
         self.config.optionxform = str
         #read in put file, and insert '=' signs so that config parser can read it
         newstring=""
         with open(fname) as f:
            for line in f:
               ll = line.strip()
               if not ll or ll[0]=="[" or ll[0]=="#": 
                  #leave unchanged blank lines, or those that start with "[" or "#"
                  newstring+=line
               else:
                  #insert "=" between first and second word in all other lines
                  ll=ll.split()
                  newstring+=ll[0]+" = "+' '.join(ll[1:])+'\n'
         self.config.readfp(StringIO.StringIO(newstring))
         #update all widgets
         utils.getVarALL(self)
         for i in range(0,31):
            if self.config.has_section("Level "+str(i)):
               self.addIntLevel(index=i, sectionExists=True)
            if self.config.has_section("Solver "+str(i)):
               self.addSolver(index=i, sectionExists=True)
            if self.config.has_section("Rational "+str(i)):
               self.addRAT(index=i, sectionExists=True)
            if self.config.has_section("Action "+str(i)):
               self.addAction(index=i, sectionExists=True)
         #update input file preview
         self.ui.txtInputFile.setPlainText(utils.generateInputFile(self))

   def writeInputFile(self):
      fname = QtGui.QFileDialog.getSaveFileName(self, 'Save file', '~/default.in')
      if fname:
         with open(fname, 'w') as f:
            f.write(utils.generateInputFile(self))
            
   def help(self):
      #load pdf documentation file with system default program
      fname="parms.pdf"
      webbrowser.open(fname)
#      if sys.platform.startswith('darwin'):
#         ret = subprocess.call(['open', fname])
#      elif sys.platform.startswith('win'):
#         ret = os.startfile(os.path.normpath(fname))
#      else:
#         ret = subprocess.call(['xdg-open', fname])

if __name__ == "__main__":
  app = QtGui.QApplication(sys.argv)
  myapp = MainGUI()
  myapp.show()
  sys.exit(app.exec_())
