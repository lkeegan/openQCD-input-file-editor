"""
Input file editor for openQCD
https://github.com/lkeegan/openQCD-input-file-editor
http://luscher.web.cern.ch/luscher/openQCD

Module containing most of the functions
"""

from PyQt4 import QtGui
import ConfigParser
import StringIO
import webbrowser


def _split_field(field, form):
    """
    Take a widget `field`, return section, variable name
    based on the widget object name having the form:
    section____variable
    with special cases for things like Solvers,
    where the index is inserted into the section name
    """
    sec = str(field.objectName().split("____")[0]).replace("_", " ")
    var = str(field.objectName().split("____")[1])
    # correct ' <-> prime
    if var == "cGprime":
        var = "cG'"
    elif var == "cFprime":
        var = "cF'"
    elif var == "phiprime":
        var = "phi'"
    # add index if in Solvers
    if sec == "Solver":
        index = int(form.ui.lblSolverIndex.text())
        sec = sec + " " + str(index)
    # add index if in Rational
    if sec == "Rational":
        index = int(form.ui.lblRATIndex.text())
        sec = sec + " " + str(index)
    # add index if in Action
    if sec == "Action":
        index = int(form.ui.lblActionIndex.text())
        sec = sec + " " + str(index)
    if sec == "Force":
        index = int(form.ui.lblActionIndex.text())
        sec = sec + " " + str(index)
    return sec, var


def get_var_txt(field, form):
    """
    Get text for `field` from config and display in text widget `field`.
    Return True if text found in config, otherwise return False.
    """
    sec, var = _split_field(field, form)
    if form.config.has_option(sec, var):
        field.setText(form.config.get(sec, var))
        return True
    else:
        return False


def set_var_txt(field, form):
    """
    Set text in config to the contents of text widget `field`
    """
    sec, var = _split_field(field, form)
    if field.isEnabled() is True:
        if not form.config.has_section(sec):
            form.config.add_section(sec)
        form.config.set(sec, var, field.text())
    else:
        if form.config.has_option(sec, var):
            form.config.remove_option(sec, var)


def set_var_list(field, form):
    """
    Set text in config to the contents of list widget `field`
    """
    sec, var = _split_field(field, form)
    if not form.config.has_section(sec):
        form.config.add_section(sec)
    tmpstr = ""
    for index in range(field.count()):
        tmpstr = tmpstr + " " + field.item(index).text()
    form.config.set(sec, var, tmpstr)


def get_var_cmb(field, form):
    """
    Get text for `field` from config and display in combobox widget `field`.
    Text matched on first word.
    Return True if text found in config, otherwise return False.
    """
    sec, var = _split_field(field, form)
    # special cases for multiple widget fields
    split_vars = [
        "imuX0", "imuX1",
        "ispX0", "ispX1",
        "iratX0", "iratX1", "iratX2"
        ]
    if var in split_vars:
        if field.isEnabled():
            if form.config.has_option(sec, var.split("X")[0]):
                for row in range(field.count()):
                    try:
                        str_cmb = str(field.itemText(row)).split()
                        tmp_cnfg = str(form.config.get(sec, var.split("X")[0]))
                        str_cnfg = tmp_cnfg.split()[int(var.split("X")[1])]
                        if str_cmb[0] == str_cnfg:
                            field.setCurrentIndex(row)
                            return True
                    except:
                        print("ERR get_var_cmb",
                              _split_field(field, form), str_cmb, str_cnfg)
        return False
    # generic code for the rest of the fields
    else:
        if form.config.has_option(sec, var):
            for row in range(field.count()):
                str_cmb = str(field.itemText(row)).split()
                str_cnfg = form.config.get(sec, var)
                if str_cmb[0] == str_cnfg:
                    field.setCurrentIndex(row)
                    return True
        return False


def set_var_cmb(field, form):
    """
    Set text in config to the (first word) of combobox widget `field`
    """
    sec, var = _split_field(field, form)
    # special cases for multiple widget fields in action:
    if var == "imuX0" or var == "imuX1":
        var = "imu"
        if form.ui.Action____imuX0.isEnabled():
            txt = str(form.ui.Action____imuX0.currentIndex())
            if form.ui.Action____imuX1.isEnabled():
                txt += " " + str(form.ui.Action____imuX1.currentIndex())
            if not form.config.has_section(sec):
                form.config.add_section(sec)
            form.config.set(sec, var, txt)
        else:
            if form.config.has_option(sec, var):
                form.config.remove_option(sec, var)
    elif var == "ispX0" or var == "ispX1":
        var = "isp"
        if form.ui.Action____ispX0.isEnabled():
            txt = str(form.ui.Action____ispX0.currentIndex())
            if form.ui.Action____ispX1.isEnabled():
                txt += " " + str(form.ui.Action____ispX1.currentIndex())
            if not form.config.has_section(sec):
                form.config.add_section(sec)
            form.config.set(sec, var, txt)
        else:
            if form.config.has_option(sec, var):
                form.config.remove_option(sec, var)
    elif var == "iratX0" or var == "iratX1" or var == "iratX2":
        var = "irat"
        if form.ui.Action____iratX0.isEnabled():
            txt = str(form.ui.Action____iratX0.currentText()) + " " + \
                str(form.ui.Action____iratX1.currentText()) + " " + \
                str(form.ui.Action____iratX2.currentText())
            if not form.config.has_section(sec):
                form.config.add_section(sec)
            form.config.set(sec, var, txt)
        else:
            if form.config.has_option(sec, var):
                form.config.remove_option(sec, var)
    elif var == "im0":
        if form.ui.Action____im0.isEnabled():
            txt = str(form.ui.Action____im0.currentIndex())
            if not form.config.has_section(sec):
                form.config.add_section(sec)
            form.config.set(sec, var, txt)
        else:
            if form.config.has_option(sec, var):
                form.config.remove_option(sec, var)
    # generic code for the rest of the fields
    else:
        if field.isEnabled() is True:
            if not form.config.has_section(sec):
                form.config.add_section(sec)
            try:
                form.config.set(sec, var, str(field.currentText()).split()[0])
            except IndexError:
                print("set_var_cmb index error",
                      field.objectName(), str(field.currentText()).split())
        else:
            if form.config.has_option(sec, var):
                form.config.remove_option(sec, var)


def get_index(list_wid):
    """
    Returns first number of currently selected
    text in supplied list widget, eg from
    3 [ascsdf] sdf sdf
    would return the integer 3
    """
    try:
        str_index = str(list_wid.item(list_wid.currentIndex().row()).text())
        return int(str_index.split()[0])
    except:
        print("ERROR get_index", list_wid.objectName())


def make_valid_index(list_wid):
    """
    Returns a valid new index for the given list widget `list_wid`
    """
    lowest_allowed = 0
    if str(list_wid.objectName()) == "listActions":
        # reserve action index 0 for gauge action
        lowest_allowed = 1
    # find and return lowest available valid index
    for i in range(lowest_allowed, 31):
        valid = True
        for row in range(0, list_wid.count()):
            if int(str(list_wid.item(row).text()).split()[0]) == i:
                valid = False
        if valid is True:
            return i


def populate_action_fields(form):
    """
    Populate action fields based on values of other fields
    """
    form.ui.Action____imuX0.clear()
    form.ui.Action____imuX1.clear()
    for k in str(form.ui.HMC_parameters____mu.text()).split():
        form.ui.Action____imuX0.addItem(k)
        form.ui.Action____imuX1.addItem(k)
    form.ui.Action____im0.clear()
    for k in str(form.ui.Lattice_parameters____kappa.text()).split():
        form.ui.Action____im0.addItem(k)
    form.ui.Action____ispX0.clear()
    form.ui.Action____ispX1.clear()
    form.ui.Force____isp.clear()
    for i in range(0, form.ui.listSolvers.count()):
        txt = str(form.ui.listSolvers.item(i).text())
        form.ui.Action____ispX0.addItem(txt)
        form.ui.Action____ispX1.addItem(txt)
        form.ui.Force____isp.addItem(txt)
    form.ui.Action____iratX0.clear()
    form.ui.Action____iratX1.clear()
    form.ui.Action____iratX2.clear()
    for i in range(0, form.ui.listRAT.count()):
        txt = str(form.ui.listRAT.item(i).text())
        form.ui.Action____iratX0.addItem(txt)
    for i in range(0, int(form.ui.Rational____degree.text())):
        form.ui.Action____iratX1.addItem(str(i))
        form.ui.Action____iratX2.addItem(str(i))


def populate_md_integration_levels(form):
    """
    Populate MD integration levels based on values of other fields
    """
    list_actions = [0]
    for row in range(0, form.ui.listActions.count()):
        num_action = int(str(form.ui.listActions.item(row).text()).split()[0])
        list_actions.append(num_action)
    list_md_actions = []
    # loop over each integration level,
    # remove any actions that are not in list of actions
    for list_wid in form.ui.tabMDint.findChildren(QtGui.QListWidget):
        for dummy_loop_var in range(list_wid.count()):
            for row in range(list_wid.count()):
                md_action = int(str(list_wid.item(row).text()).split()[0])
                if md_action in list_actions:
                    if md_action not in list_md_actions:
                        list_md_actions.append(md_action)
                else:
                    list_wid.takeItem(row)
                    break
    # loop over all actions, if not in the list,
    # add to first integration level
    first_md_action_list = form.ui.tabMDint.findChildren(QtGui.QListWidget)[0]
    for action in list_actions:
        if action not in list_md_actions:
            first_md_action_list.addItem(str(action))


def generate_input_file(form):
    """
    Return string containing input file generated based on contents of config.
    First add HMC parameters to config that are not explicity
    stored in a widget but are implied by the other parameters.
    """
    str_actions = []
    list_action_levels = form.ui.tabMDint.findChildren(QtGui.QListWidget)
    nlv = len(list_action_levels)
    for lst in list_action_levels:
        set_var_list(lst, form)
        for index in range(lst.count()):
            str_actions.append(int(lst.item(index).text()))
    npf = len(str_actions) - 1
    str_actions = [str(x) for x in sorted(str_actions)]
    form.config.set("HMC parameters", "actions", ' '.join(str_actions))
    form.config.set("HMC parameters", "npf", str(npf))
    form.config.set("HMC parameters", "nlv", str(nlv))

    # Sorting of sections
    sorted_config = ConfigParser.RawConfigParser()
    sorted_config.optionxform = str
    if form.ui.radioSortDefault.isChecked():
        # default ordering
        default_order = ["Run", "Directories", "Lattice", "Boundary",
                         "Random", "HMC", "MD", "Level", "Rational",
                         "Action", "Force", "Solver", "SAP",
                         "Deflation", "Wilson"]
        for option in default_order:
            for sec in sorted(form.config.sections()):
                if option in sec:
                    sorted_config.add_section(sec)
                    for name, value in form.config.items(sec):
                        sorted_config.set(sec, name, value)
        # add any sections not in default ordering list
        # alphabetically to the end
        for sec in sorted(form.config.sections()):
            if sec not in sorted_config.sections():
                sorted_config.add_section(sec)
                for name, value in form.config.items(sec):
                    sorted_config.set(sec, name, value)
    elif form.ui.radioSortAlpha.isChecked():
        # alphabetical ordering
        for sec in sorted(form.config.sections()):
            sorted_config.add_section(sec)
            for name, value in form.config.items(sec):
                sorted_config.set(sec, name, value)
    else:
        # no ordering
        for sec in form.config.sections():
            sorted_config.add_section(sec)
            for name, value in form.config.items(sec):
                sorted_config.set(sec, name, value)

    # generate input file in config
    # parser format (i.e. with '=' signs)
    fakefile = StringIO.StringIO()
    sorted_config.write(fakefile)

    # remove '=' appropriately and return as string
    newstring = ""
    for line in fakefile.getvalue().splitlines():
        s_line = line.strip()
        if not s_line or s_line[0] == "[" or s_line[0] == "#":
            # leave unchanged blank lines,
            # or those that start with "[" or "#"
            newstring += line + '\n'
        else:
            # remove "=" in all other lines
            newstring += s_line.replace("=", " ") + '\n'
    return newstring


def get_solver(form):
    """
    Get data for currently selected solver and display.
    """
    form.ui.lblSolverIndex.setText(str(get_index(form.ui.listSolvers)))
    # first read from config what kind of solver it is
    get_var_cmb(form.ui.Solver____solver, form)
    # then disable/enable comboboxes based on this
    form.changecmbSolver()
    # finally read from config all the fields
    for txt in form.ui.tabSolvers.findChildren(QtGui.QLineEdit):
        get_var_txt(txt, form)
    get_var_cmb(form.ui.Solver____isolv, form)


def get_rational_app(form):
    """
    Get data for currently selected RAT and display.
    """
    form.ui.lblRATIndex.setText(str(get_index(form.ui.listRAT)))
    for txt in form.ui.tabRAT.findChildren(QtGui.QLineEdit):
        get_var_txt(txt, form)


def get_action(index, form):
    """
    Get data for currently selected action and display.
    """
    populate_action_fields(form)
    form.ui.lblActionIndex.setText(str(index))
    # first read from config what kind of action it is
    get_var_cmb(form.ui.Action____action, form)
    # then disable/enable comboboxes based on the action
    form.changecmbAction()
    # finally read from config all the enabled comboboxes
    # TODO: replace below with call to children on current tab instead of ALL
    get_var_all(form)


def get_var_all(form):
    """
    Update all widgets from config
    """
    for txt in form.findChildren(QtGui.QLineEdit):
        get_var_txt(txt, form)
    for cmb in form.findChildren(QtGui.QComboBox):
        get_var_cmb(cmb, form)


def set_var_all(form):
    """
    Update config from all widgets
    """
    for txt in form.findChildren(QtGui.QLineEdit):
        set_var_txt(txt, form)
    for cmb in form.findChildren(QtGui.QComboBox):
        set_var_cmb(cmb, form)


def help(self):
    """
    Show wiki page on github
    """
    url = "https://github.com/lkeegan/openQCD-input-file-editor/wiki"
    webbrowser.open(url)
