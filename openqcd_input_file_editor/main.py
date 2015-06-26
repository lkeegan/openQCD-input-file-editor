"""
Input file editor for openQCD
https://github.com/lkeegan/openQCD-input-file-editor
http://luscher.web.cern.ch/luscher/openQCD

Requires Python 2.7 and PyQt4

# NOTES:
# Currently assumes Action 0 is the gauge action - need to add code
# to deal with other situations when loading an input file, maybe
# the easiest is just to first change the action indices in the file?

# The gui is imported from gui.py, which in turn is generated
# from gui.ui with the command pyuic4
# The file gui.ui can be edited using designer-qt4
# Only routines that are directly invoked by user actions
# are included in this file - all others are imported
# from consistency.py and utils.py

# In general, each parameter in the input file
# is represented by a pyqt widget, named accordingly.
# The name goes like "section___option", where section
# and option are separated by 4 underscores, and any
# spaces in the section name are replaced with an underscore
# For example, in the section "[Run name]" there is an
# option "name". This is displayed/edited in the
# pyqtQLineEdit widget in the gui named "Run_name____name"
# Whenever the contents of this (or any widget) change,
# the relevant section and option are determined based
# on this formatting of the widget name, and the parameter
# in the input file is updated
# If the widget is disabled, then the corresponding
# parameter is removed from the input file
"""

from PyQt4 import QtCore
from PyQt4 import QtGui
from PyQt4 import Qt
from gui import Ui_Form
import StringIO
import ConfigParser

import consistency
import utils


class StrictIntValidator(Qt.QIntValidator):
    """
    Subclass of Qt.QIntValidator for validating user input as integer
    """
    def __init__(self, bottom, top, parent=None):
        Qt.QIntValidator.__init__(self, bottom, top, parent)

    def validate(self, input_value, pos):
        """
        Do not treat empty values or "." as valid integers
        """
        state, pos = Qt.QIntValidator.validate(self, input_value, pos)
        if input_value.isEmpty() or input_value == '.':
            return Qt.QValidator.Invalid, pos
        if state != Qt.QValidator.Acceptable:
            return Qt.QValidator.Invalid, pos
        return Qt.QValidator.Acceptable, pos


class MainGUI(QtGui.QWidget):
    """
    Main GUI class
    """
    def __init__(self, parent=None):
        # GUI Initialisation
        QtGui.QWidget.__init__(self, parent)
        self.ui = Ui_Form()
        self.ui.setupUi(self)

        # Config initialisation
        # store all parameters in self.config
        self.config = ConfigParser.RawConfigParser()
        # preserve case of parameters
        self.config.optionxform = str

        # setup basic consistency checks,
        # e.g beta must be a positive double,
        # RNG seed must be a positive integer, etc.
        # list of text fields that have to be positive doubles
        self.list_dbl_fields = [self.ui.Lattice_parameters____beta,
                                self.ui.HMC_parameters____tau,
                                self.ui.Wilson_flow____eps,
                                self.ui.Solver____res,
                                self.ui.Deflation_subspace_generation____kappa,
                                self.ui.Deflation_subspace_generation____mu,
                                self.ui.Deflation_projection____res,
                                self.ui.Deflation_update_scheme____dtau,
                                self.ui.Boundary_conditions____cF,
                                self.ui.Boundary_conditions____cG,
                                self.ui.Boundary_conditions____cFprime,
                                self.ui.Boundary_conditions____cGprime]
        # list of text fields that have to be positive integers
        self.list_int_fields = [self.ui.Random_number_generator____seed,
                                self.ui.MD_trajectories____nth,
                                self.ui.MD_trajectories____ntr,
                                self.ui.MD_trajectories____dtr_log,
                                self.ui.MD_trajectories____dtr_ms,
                                self.ui.MD_trajectories____dtr_cnfg,
                                self.ui.Wilson_flow____nstep,
                                self.ui.Wilson_flow____dnms,
                                self.ui.Solver____nmx,
                                self.ui.Solver____nkv,
                                self.ui.Solver____nmr,
                                self.ui.Solver____ncy,
                                self.ui.Force____ncr,
                                self.ui.Rational____degree,
                                self.ui.Deflation_subspace____Ns,
                                self.ui.Deflation_subspace_generation____ninv,
                                self.ui.Deflation_subspace_generation____nmr,
                                self.ui.Deflation_subspace_generation____ncy,
                                self.ui.Deflation_projection____nkv,
                                self.ui.Deflation_projection____nmx,
                                self.ui.Deflation_update_scheme____nsm]
        # list of text fields that have to be a list of positive doubles
        self.list_dbl_fields_list = [self.ui.Lattice_parameters____kappa,
                                     self.ui.HMC_parameters____mu,
                                     self.ui.Rational____range]

        # Force these input fields to be integers
        for field in self.list_int_fields:
            field.setValidator(StrictIntValidator(1, 100000000, field))

        # link user actions (e.g. editing text in a widget) to code
        # (e.g. updating appropriate parameter in input file)
        self.init_signals_and_slots()

        # make a default minimal initial input file
        self.md_int_levels = 0
        self.gauge_action_index = 0
        self.change_cmb_bcs()
        utils.set_var_all(self)
        self.config.add_section("Action 0")
        self.config.set("Action 0", "action", "ACG")
        self.add_int_level()
        utils.populate_md_integration_levels(self)

    def init_signals_and_slots(self):
        """
        Connect the widgets in the GUI to functions
        """
        # User clicks a button
        self.ui.btnSave.clicked.connect(self.write_input_file)
        self.ui.btnOpen.clicked.connect(self.read_input_file)
        self.ui.btnHelp.clicked.connect(utils.help)
        self.ui.btnAddIntLevel.clicked.connect(self.add_int_level)
        self.ui.btnRemoveIntLevel.clicked.connect(self.remove_int_level)
        self.ui.btnAddSolver.clicked.connect(self.add_solver)
        self.ui.btnRemoveSolver.clicked.connect(self.remove_solver)
        self.ui.btnAddRAT.clicked.connect(self.add_rational_app)
        self.ui.btnRemoveRAT.clicked.connect(self.remove_rational_app)
        self.ui.btnAddAction.clicked.connect(self.add_action)
        self.ui.btnRemoveAction.clicked.connect(self.remove_action)
        # User (or code) changes tab
        self.ui.tabMain.currentChanged.connect(self.change_tab)
        # User changes any text field
        for txt in self.findChildren(QtGui.QLineEdit):
            txt.editingFinished.connect(self.change_text)
        # User changes any combobox selection
        for txt in self.findChildren(QtGui.QComboBox):
            txt.activated.connect(self.change_combo)
        # User toggles a radiobutton
        for rad in self.findChildren(QtGui.QRadioButton):
            rad.toggled.connect(self.change_radio)

        # User (or code) changes a specific combobox selection
        cmb = self.ui.Boundary_conditions____type
        cmb.currentIndexChanged.connect(self.change_cmb_bcs)
        cmb = self.ui.Solver____solver
        cmb.currentIndexChanged.connect(self.change_cmb_solver)
        cmb = self.ui.Action____action
        cmb.currentIndexChanged.connect(self.change_cmb_action)

        # User (or code) chooses an item in a list
        self.ui.listSolvers.itemSelectionChanged.connect(self.select_solver)
        self.ui.listRAT.itemSelectionChanged.connect(self.select_rational_app)
        self.ui.listActions.itemSelectionChanged.connect(self.select_action)

    def change_tab(self, index):
        """
        When tab is changed, update fields if required
        """
        if self.ui.tabMain.tabText(index) == "Action":
            utils.populate_action_fields(self)
            self.ui.listActions.setCurrentRow(self.ui.listActions.count() - 1)
        elif self.ui.tabMain.tabText(index) == "MD Integration":
            utils.populate_md_integration_levels(self)
        elif self.ui.tabMain.tabText(index) == "Input File Preview":
            self.ui.txtInputFile.setPlainText(utils.generate_input_file(self))

    def change_cmb_bcs(self):
        """
        Enable/disable relevant fields for current choice of bcs
        """
        if self.ui.Boundary_conditions____type.currentIndex() == 0:
            # open
            self.ui.Boundary_conditions____cG.setEnabled(True)
            self.ui.Boundary_conditions____cF.setEnabled(True)
            self.ui.Boundary_conditions____phi.setEnabled(False)
            self.ui.Boundary_conditions____cGprime.setEnabled(False)
            self.ui.Boundary_conditions____cFprime.setEnabled(False)
            self.ui.Boundary_conditions____phiprime.setEnabled(False)
        elif self.ui.Boundary_conditions____type.currentIndex() == 1:
            # sf
            self.ui.Boundary_conditions____cG.setEnabled(True)
            self.ui.Boundary_conditions____cF.setEnabled(True)
            self.ui.Boundary_conditions____phi.setEnabled(True)
            self.ui.Boundary_conditions____cGprime.setEnabled(False)
            self.ui.Boundary_conditions____cFprime.setEnabled(False)
            self.ui.Boundary_conditions____phiprime.setEnabled(True)
        elif self.ui.Boundary_conditions____type.currentIndex() == 2:
            # open-sf
            self.ui.Boundary_conditions____cG.setEnabled(True)
            self.ui.Boundary_conditions____cF.setEnabled(True)
            self.ui.Boundary_conditions____phi.setEnabled(False)
            self.ui.Boundary_conditions____cGprime.setEnabled(True)
            self.ui.Boundary_conditions____cFprime.setEnabled(True)
            self.ui.Boundary_conditions____phiprime.setEnabled(True)
        elif self.ui.Boundary_conditions____type.currentIndex() == 3:
            # periodic
            self.ui.Boundary_conditions____cG.setEnabled(False)
            self.ui.Boundary_conditions____cF.setEnabled(False)
            self.ui.Boundary_conditions____phi.setEnabled(False)
            self.ui.Boundary_conditions____cGprime.setEnabled(False)
            self.ui.Boundary_conditions____cFprime.setEnabled(False)
            self.ui.Boundary_conditions____phiprime.setEnabled(False)
        # update affected fields in config
        utils.set_var_txt(self.ui.Boundary_conditions____cG, self)
        utils.set_var_txt(self.ui.Boundary_conditions____cF, self)
        utils.set_var_txt(self.ui.Boundary_conditions____phi, self)
        utils.set_var_txt(self.ui.Boundary_conditions____cGprime, self)
        utils.set_var_txt(self.ui.Boundary_conditions____cFprime, self)
        utils.set_var_txt(self.ui.Boundary_conditions____phiprime, self)

    def change_cmb_solver(self):
        """
        Enable/disable relevant fields for current choice of solver
        """
        if self.ui.Solver____solver.currentIndex() in [0, 1]:
            self.ui.Solver____nkv.setEnabled(False)
            self.ui.Solver____isolv.setEnabled(False)
            self.ui.Solver____nmr.setEnabled(False)
            self.ui.Solver____ncy.setEnabled(False)
        else:
            self.ui.Solver____nkv.setEnabled(True)
            self.ui.Solver____isolv.setEnabled(True)
            self.ui.Solver____nmr.setEnabled(True)
            self.ui.Solver____ncy.setEnabled(True)
        utils.set_var_txt(self.ui.Solver____nkv, self)
        utils.set_var_cmb(self.ui.Solver____isolv, self)
        utils.set_var_txt(self.ui.Solver____nmr, self)
        utils.set_var_txt(self.ui.Solver____ncy, self)
        # update solver description in listbox
        if self.ui.listSolvers.count() > 0:
            index = int(self.ui.lblSolverIndex.text())
            tmp_w = self.ui.listSolvers.item(self.ui.listSolvers.currentRow())
            tmp_s = str(self.ui.Solver____solver.currentText())
            tmp_text = str(index) + " [" + tmp_s + "]"
            tmp_w.setText(tmp_text)
            utils.set_var_cmb(self.ui.Solver____solver, self)

        # Check if we need SAP (i.e. have some SAP solvers)
        we_need_sap = False
        if self.ui.Solver____solver.currentIndex() in [2, 3]:
            we_need_sap = True
        else:
            for index in range(self.ui.listSolvers.count()):
                if "SAP" in str(self.ui.listSolvers.item(index).text()):
                    we_need_sap = True
        if we_need_sap and not self.ui.SAP____bs.isEnabled():
            self.ui.SAP____bs.setEnabled(True)
            utils.set_var_txt(self.ui.SAP____bs, self)
        elif not we_need_sap and self.ui.SAP____bs.isEnabled():
            self.ui.SAP____bs.setEnabled(False)
            self.config.remove_section("SAP")

        # Check if we need deflation (i.e. have some DFL solvers)
        we_need_dfl = False
        if self.ui.Solver____solver.currentIndex() == 3:
            we_need_dfl = True
        else:
            for index in range(self.ui.listSolvers.count()):
                if "DFL" in str(self.ui.listSolvers.item(index).text()):
                    we_need_dfl = True
        if we_need_dfl and not self.ui.groupDFLsubspace.isEnabled():
            self.ui.groupDFLsubspace.setEnabled(True)
            self.ui.groupDFLprojection.setEnabled(True)
            self.ui.groupDFLupdate.setEnabled(True)
            for txt in self.ui.tabDeflation.findChildren(QtGui.QLineEdit):
                utils.set_var_txt(txt, self)
        elif not we_need_dfl and self.ui.groupDFLsubspace.isEnabled():
            self.ui.groupDFLsubspace.setEnabled(False)
            self.ui.groupDFLprojection.setEnabled(False)
            self.ui.groupDFLupdate.setEnabled(False)
            self.config.remove_section("Deflation subspace")
            self.config.remove_section("Deflation subspace generation")
            self.config.remove_section("Deflation projection")
            self.config.remove_section("Deflation update scheme")

    def change_cmb_action(self):
        """
        Enable/disable relevant fields for current choice of action
        """
        if self.ui.Action____action.currentIndex() in [4, 5]:
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
            if self.ui.Action____action.currentIndex() in [0, 2]:
                self.ui.Action____imuX0.setEnabled(True)
                self.ui.Action____imuX1.setEnabled(False)
                self.ui.Action____ispX1.setEnabled(False)
            else:
                self.ui.Action____imuX0.setEnabled(True)
                self.ui.Action____imuX1.setEnabled(True)
                self.ui.Action____ispX1.setEnabled(True)
        if self.ui.listActions.count() > 0:
            index = str(int(self.ui.lblActionIndex.text()))
            txt_force = str(self.ui.Action____action.currentText())
            # update force parameters
            self.config.set("Force " + index, "force", "FRF" + txt_force[3:])
            # update action description in listbox
            tmp_w = self.ui.listActions.item(self.ui.listActions.currentRow())
            tmp_w.setText(index + " [" + txt_force + "]")
            utils.set_var_cmb(self.ui.Action____action, self)

    def change_cmb_md_int(self):
        """
        Update MD integration in config using combobox fields
        """
        cmb = self.sender()
        utils.set_var_cmb(cmb, self)
        grid = self.ui.gridLayout
        level = int(grid.getItemPosition(grid.indexOf(self.sender()))[1])
        if cmb.currentIndex() == 1:
            # show lambda field
            grid.itemAtPosition(2, level).widget().setEnabled(True)
        else:
            # hide lambda field
            grid.itemAtPosition(2, level).widget().setEnabled(False)
        utils.set_var_txt(grid.itemAtPosition(2, level).widget(), self)

    def change_radio(self):
        """
        Regenerate input file when user chooses a different ordering
        """
        self.ui.txtInputFile.setPlainText(utils.generate_input_file(self))

    def select_solver(self):
        """
        When user clicks on a solver, display the data
        """
        if self.ui.listSolvers.isEnabled():
            utils.get_solver(self)

    def select_rational_app(self):
        """
        When user clicks on a rational approx, display the data
        """
        if self.ui.listRAT.isEnabled():
            utils.get_rational_app(self)

    def select_action(self):
        """
        When user clicks on an action, display the data
        """
        if self.ui.listActions.isEnabled():
            utils.get_action(utils.get_index(self.ui.listActions), self)

    def add_solver(self, index=99, section_exists=False):
        """
        If section_exists is True, then adds an existing
        (in the config) solver with the supplied index.
        If not then makes a new solver with a new index
        """
        self.ui.groupSolver.setEnabled(True)
        self.ui.btnRemoveSolver.setEnabled(True)
        self.ui.listSolvers.setEnabled(True)
        # If we are not given an index, then generate one
        # and write a default set of params to that config section
        if not section_exists:
            index = utils.make_valid_index(self.ui.listSolvers)
            sec = "Solver " + str(index)
            self.config.add_section(sec)
            self.config.set(sec, "solver", "CGNE")
            self.config.set(sec, "nmx", "1024")
            self.config.set(sec, "res", "1.e-10")
        self.ui.listSolvers.addItem(str(index))
        self.ui.listSolvers.setCurrentRow(self.ui.listSolvers.count() - 1)
        utils.get_solver(self)

    def add_rational_app(self, index=99, section_exists=False):
        """
        If section_exists is True, then adds an existing
        (in the config) rational approx with the supplied index.
        If not then makes a new solver with a new index
        """
        self.ui.groupRAT.setEnabled(True)
        self.ui.btnRemoveRAT.setEnabled(True)
        self.ui.listRAT.setEnabled(True)
        # If we are not given an index, then generate one and
        # write a default set of params to that config section
        if not section_exists:
            index = utils.make_valid_index(self.ui.listRAT)
            sec = "Rational " + str(index)
            self.config.add_section(sec)
            self.config.set(sec, "degree", "9")
            self.config.set(sec, "range", "0.03 6.10")
        self.ui.listRAT.addItem(str(index))
        self.ui.listRAT.setCurrentRow(self.ui.listRAT.count() - 1)
        utils.get_rational_app(self)

    def add_action(self, index=99, section_exists=False):
        """
        If section_exists is True, then adds an existing
        (in the config) action with the supplied index.
        If not then makes a new solver with a new index
        """
        self.ui.groupAction.setEnabled(True)
        self.ui.btnRemoveAction.setEnabled(True)
        self.ui.listActions.setEnabled(True)
        # ignore gauge action
        sec = "Action " + str(index)
        if (self.config.has_option(sec, "action")
                and self.config.get(sec, "action") == "ACG"):
            self.gauge_action_index = index
            # TODO: deal with this case properly
            # (i.e. convert it to index zero and update others accordingly)
            return
        # If we are not given an index, then generate one and
        # write a default set of params to that config section
        if not section_exists:
            index = utils.make_valid_index(self.ui.listActions)
            sec = "Action " + str(index)
            self.config.add_section(sec)
            # add default action to config
            self.config.set(sec, "action", "ACF_TM1")
            self.config.set(sec, "ipf", "0")
            self.config.set(sec, "im0", "0")
            self.config.set(sec, "imu", "0")
            self.config.set(sec, "isp", "0")
            sec = "Force " + str(index)
            self.config.add_section(sec)
            # add corresponding force to config
            self.config.set(sec, "force", "FRF_TM1")
            self.config.set(sec, "isp", "0")
            self.config.set(sec, "ncr", "1")
        self.ui.listActions.addItem(str(index))
        self.ui.listActions.setCurrentRow(self.ui.listActions.count() - 1)
        utils.get_action(index, self)

    def add_int_level(self):
        """
        Add integration level
        """
        self.md_int_levels += 1
        if self.md_int_levels > 0:
            self.ui.btnRemoveIntLevel.setEnabled(True)
        str_level = "Level_" + str(self.md_int_levels - 1)
        label = QtGui.QLabel(self.ui.tabMDint)
        label.setText(str_level.replace("_", " "))
        self.ui.gridLayout.addWidget(label, 0, self.md_int_levels, 1, 1)
        txt = QtGui.QLineEdit(self.ui.tabMDint)
        txt.setObjectName(str_level + "____lambda")
        self.list_dbl_fields.append(txt)
        txt.editingFinished.connect(self.change_text)
        self.ui.gridLayout.addWidget(txt, 2, self.md_int_levels, 1, 1)
        if utils.get_var_txt(txt, self) is False:
            txt.setText("0.19")
            utils.set_var_txt(txt, self)
        txt = QtGui.QLineEdit(self.ui.tabMDint)
        txt.setValidator(StrictIntValidator(1, 100000000, txt))
        txt.setObjectName("Level_" + str(self.md_int_levels - 1) + "____nstep")
        txt.editingFinished.connect(self.change_text)
        self.ui.gridLayout.addWidget(txt, 3, self.md_int_levels, 1, 1)
        if utils.get_var_txt(txt, self) is False:
            txt.setText("1")
            utils.set_var_txt(txt, self)
        cmb = QtGui.QComboBox(self.ui.tabMDint)
        cmb.setObjectName(str_level + "____integrator")
        cmb.addItem("LPFR [Leapfrog]")
        cmb.addItem("OMF2 [2nd Order OMF]")
        cmb.addItem("OMF4 [4th Order OMF]")
        cmb.currentIndexChanged.connect(self.change_cmb_md_int)
        self.ui.gridLayout.addWidget(cmb, 1, self.md_int_levels, 1, 1)
        if utils.get_var_cmb(cmb, self) is False:
            cmb.setCurrentIndex(2)
        lst = QtGui.QListWidget(self.ui.tabMDint)
        lst.setDragEnabled(True)
        lst.setSortingEnabled(True)
        lst.setDragDropMode(QtGui.QAbstractItemView.DragDrop)
        lst.setDefaultDropAction(QtCore.Qt.MoveAction)
        lst.setObjectName(str_level + "____forces")
        str_level_config = "Level " + str(self.md_int_levels - 1)
        if self.config.has_option(str_level_config, "forces"):
            str_forces = str(self.config.get(str_level_config, "forces"))
            for i in str_forces.split():
                lst.addItem(i)
        self.ui.gridLayout.addWidget(lst, 4, self.md_int_levels, 1, 1)

    def remove_solver(self):
        """
        Remove currently selected solver
        """
        index = utils.get_index(self.ui.listSolvers)
        if self.ui.listSolvers.count() < 2:
            self.ui.btnRemoveSolver.setEnabled(False)
            self.ui.groupSolver.setEnabled(False)
            self.ui.listSolvers.setEnabled(False)
        self.ui.listSolvers.takeItem(self.ui.listSolvers.currentRow())
        self.config.remove_section("Solver " + str(index))
        if self.ui.listSolvers.count() > 0:
            self.ui.listSolvers.setCurrentRow(self.ui.listSolvers.count() - 1)

    def remove_rational_app(self):
        """
        Remove currently selected rational approx
        """
        index = utils.get_index(self.ui.listRAT)
        if self.ui.listRAT.count() < 2:
            self.ui.btnRemoveRAT.setEnabled(False)
            self.ui.groupRAT.setEnabled(False)
            self.ui.listRAT.setEnabled(False)
        self.ui.listRAT.takeItem(self.ui.listRAT.currentRow())
        self.config.remove_section("Rational " + str(index))
        if self.ui.listRAT.count() > 0:
            self.ui.listRAT.setCurrentRow(self.ui.listRAT.count() - 1)

    def remove_action(self):
        """
        Remove currently selected action
        """
        index = utils.get_index(self.ui.listActions)
        if self.ui.listActions.count() < 2:
            self.ui.btnRemoveRAT.setEnabled(False)
            self.ui.groupAction.setEnabled(False)
            self.ui.listActions.setEnabled(False)
        self.ui.listActions.takeItem(self.ui.listActions.currentRow())
        self.config.remove_section("Action " + str(index))
        self.config.remove_section("Force " + str(index))
        if self.ui.listActions.count() > 0:
            self.ui.listActions.setCurrentRow(self.ui.listActions.count() - 1)

    def remove_int_level(self):
        """
        Remove finest integration level
        """
        # Move any forces in level to be removed to next level
        if self.md_int_levels > 1:
            grid = self.ui.gridLayout
            w_old = grid.itemAtPosition(4, self.md_int_levels).widget()
            for i in range(w_old.count()):
                w_new = grid.itemAtPosition(4, self.md_int_levels - 1).widget()
                w_new.addItem(w_old.item(i).text())
        # Update config
        utils.set_var_all(self)
        # remove integration level from gui
        grid = self.ui.gridLayout
        for position in range(0, 5):
            wid = grid.itemAtPosition(position, self.md_int_levels).widget()
            grid.removeWidget(wid)
            wid.setParent(None)
        self.md_int_levels -= 1
        if self.md_int_levels == 1:
            self.ui.btnRemoveIntLevel.setEnabled(False)
        # Remove section from config
        self.config.remove_section("Level " + str(self.md_int_levels))

    def change_text(self):
        """
        Performs params consistency check &
        updates config from the text in the widget that called this function.
        """
        consistent = 0
        # unless this is called from a button (e.g. user opened a file)
        # then update the text field the user has just changed
        if not str(self.sender().objectName()).startswith("btn"):
            utils.set_var_txt(self.sender(), self)
        # do consistency checks
        t_err = "Must be a list of positive doubles (e.g. 2.123 5e-3 0.1243)"
        for txt in self.list_dbl_fields_list:
            consistent += consistency.is_list_of_positive_doubles(txt, t_err)
        t_err = "Must be a positive double (e.g. 0.165, or 1.3e-1)"
        for txt in self.list_dbl_fields:
            consistent += consistency.is_positive_double(txt, t_err)
        t_err = " must be an integer multiple of "
        consistent += consistency.is_integer_multiple(
            self.ui.Wilson_flow____nstep,
            self.ui.Wilson_flow____dnms,
            "Numer of integration steps" + t_err + "measurement frequency")
        consistent += consistency.is_integer_multiple(
            self.ui.MD_trajectories____dtr_ms,
            self.ui.MD_trajectories____dtr_log,
            "Measurement frequency" + t_err + "log freqency")
        consistent += consistency.is_integer_multiple(
            self.ui.MD_trajectories____dtr_cnfg,
            self.ui.MD_trajectories____dtr_ms,
            "Configuration save frequency" + t_err + "measurement freqency")
        t_err = " must be an integer multiple of configuration save freqency"
        consistent += consistency.is_integer_multiple(
            self.ui.MD_trajectories____nth,
            self.ui.MD_trajectories____dtr_cnfg,
            "Number of MD Thermalisation trajectories" + t_err)
        consistent += consistency.is_integer_multiple(
            self.ui.MD_trajectories____ntr,
            self.ui.MD_trajectories____dtr_cnfg,
            "Number of MD trajectories" + t_err)
        consistent += consistency.is_list_of_n_positive_integers(
            self.ui.SAP____bs,
            4,
            "Must be a list of 4 positive integers, e.g. 4 6 6 4")
        consistent += consistency.is_list_of_n_positive_integers(
            self.ui.Deflation_subspace____bs,
            4,
            "Must be a list of 4 positive integers, e.g. 4 6 6 4")
        consistent += consistency.is_list_of_n_doubles(
            self.ui.Boundary_conditions____phi,
            2,
            "Must be a list of 2 doubles, e.g. 0.13 -0.63")
        consistent += consistency.is_list_of_n_doubles(
            self.ui.Boundary_conditions____phiprime,
            2,
            "Must be a list of 2 doubles, e.g. 0.13 -0.63")
        if consistent > 0:
            self.ui.btnSave.setEnabled(False)
        else:
            self.ui.btnSave.setEnabled(True)

    def change_combo(self):
        """
        called when user changes a combobox - updates config
        """
        utils.set_var_cmb(self.sender(), self)

    def read_input_file(self):
        """
        Read existing input file from disk
        """
        # get filename from user
        fname = QtGui.QFileDialog.getOpenFileName(self, 'Open file', '~/')
        if fname:
            # clear all current parameters
            while self.md_int_levels > 0:
                self.remove_int_level()
            while self.ui.listSolvers.count() > 0:
                self.remove_solver()
            while self.ui.listRAT.count() > 0:
                self.remove_rational_app()
            while self.ui.listActions.count() > 0:
                self.remove_action()
            str_title = "[" + str(fname) + "] - openQCD Input File Editor"
            self.setWindowTitle(str_title)
            # crnew config
            self.config = ConfigParser.RawConfigParser()
            self.config.optionxform = str
            # read input file and insert '=' signs so that
            # config parser can read it
            newstring = ""
            with open(fname) as fil:
                for line in fil:
                    l_s = line.strip()
                    if not l_s or l_s[0] == "[" or l_s[0] == "#":
                        # leave unchanged blank lines,
                        # or those that start with "[" or "#"
                        newstring += line
                    else:
                        # insert "=" between first and second word
                        # in all other lines
                        l_s = l_s.split()
                        newstring += l_s[0] + " = " + ' '.join(l_s[1:]) + '\n'
            self.config.readfp(StringIO.StringIO(newstring))
            # update all widgets
            utils.get_var_all(self)
            for i in range(0, 31):
                if self.config.has_section("Level " + str(i)):
                    self.add_int_level()
                if self.config.has_section("Solver " + str(i)):
                    self.add_solver(index=i, section_exists=True)
                if self.config.has_section("Rational " + str(i)):
                    self.add_rational_app(index=i, section_exists=True)
                if self.config.has_section("Action " + str(i)):
                    self.add_action(index=i, section_exists=True)
            # update input file preview
            self.ui.txtInputFile.setPlainText(utils.generate_input_file(self))
            self.change_text()

    def write_input_file(self):
        """
        Generate input file and write to disk
        """
        fname = QtGui.QFileDialog.getSaveFileName(self, 'Save file', '~/')
        if fname:
            with open(fname, 'w') as fil:
                fil.write(utils.generate_input_file(self))
