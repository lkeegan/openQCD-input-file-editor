#!/usr/bin/env python
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

import sys
from PyQt4 import QtGui

import openqcd_input_file_editor as op

if __name__ == "__main__":
    Q = QtGui.QApplication(sys.argv)
    A = op.main.MainGUI()
    A.show()
    sys.exit(Q.exec_())
