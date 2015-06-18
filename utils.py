# Input file editor for openQCD
# Utils module

from PyQt4 import QtGui
import ConfigParser
import StringIO

def splitField(field, form):
   #takes a widget, returns section and variable name based on the widget object name of the form:
   #section____variable
   #with special cases for things like Solvers, where the index is inserted into the section name
   sec=str(field.objectName().split("____")[0]).replace("_"," ")
   var=str(field.objectName().split("____")[1])
   #correct ' <-> prime
   if var=="cGprime":
      var="cG'"
   elif var=="cFprime":
      var="cF'"
   elif var=="phiprime":
      var="phi'"
   #add index if in Solvers
   if sec=="Solver":
      index=int(form.ui.lblSolverIndex.text())
      sec=sec+" "+str(index)
   #add index if in Rational
   if sec=="Rational":
      index=int(form.ui.lblRATIndex.text())
      sec=sec+" "+str(index)
   #add index if in Action
   if sec=="Action":
      index=int(form.ui.lblActionIndex.text())
      sec=sec+" "+str(index)
   if sec=="Force":
      index=int(form.ui.lblActionIndex.text())
      sec=sec+" "+str(index)
   return sec, var

def getVarTxt(field, form):
   #Get and display contents of a txt field from config
   sec, var = splitField(field, form)
   if form.config.has_option(sec,var):
      field.setText(form.config.get(sec,var))
      return True
   else:
      return False

def setVarTxt(field, form):
   #Set variable in config to value in txt field
   sec, var = splitField(field, form)
   if field.isEnabled()==True:
      if not form.config.has_section(sec):
         form.config.add_section(sec)
      form.config.set(sec,var,field.text())
   else:
      if form.config.has_option(sec,var):
         form.config.remove_option(sec,var)

def setVarList(field,  form):
   #Set variable in config to contents of list
   sec, var = splitField(field, form)
   if not form.config.has_section(sec):
      form.config.add_section(sec)
   str=""
   for index in range(field.count()):
      str = str + " " + field.item(index).text()
   form.config.set(sec,var,str)

def getVarCmb(field, form):
   #Set contents of combobox to value in config (match on first word)
   sec, var = splitField(field, form)
   #special cases for multiple widget fields in action:
   split_vars=["imuX0","imuX1","ispX0","ispX1","iratX0","iratX1","iratX2"]
   if var in split_vars:
      if field.isEnabled():
         if form.config.has_option(sec,var.split("X")[0]):
            for row in range(field.count()):
               try:
                  if str(field.itemText(row)).split()[0]==str(form.config.get(sec,var.split("X")[0])).split()[int(var.split("X")[1])]:
                     field.setCurrentIndex(row)
                     return True
               except:
                  print "ERR getVarCmb", splitField(field, form),  str(field.itemText(row)).split(),  str(form.config.get(sec,var.split("X")[0])).split()[int(var.split("X")[1])]
      return False
   #generic code for the rest of the fields
   else:
      if form.config.has_option(sec,var):
         for row in range(field.count()):
            if str(field.itemText(row)).split()[0]==form.config.get(sec,var):
               field.setCurrentIndex(row)
               return True
      return False

def setVarCmb(field, form):
   #Set variable in config to (first word of) combobox selection
   sec, var = splitField(field, form)
   #special cases for multiple widget fields in action:
   if var=="imuX0" or var=="imuX1":
      var="imu"
      if form.ui.Action____imuX0.isEnabled():
         if form.ui.Action____imuX1.isEnabled():
            txt=str(form.ui.Action____imuX0.currentIndex())+" "+str(form.ui.Action____imuX1.currentIndex())
         else:
            txt=str(form.ui.Action____imuX0.currentIndex())
         if not form.config.has_section(sec):
            form.config.add_section(sec)
         form.config.set(sec,var,txt)
      else:
         if form.config.has_option(sec,var):
            form.config.remove_option(sec,var)
   elif var=="ispX0" or var=="ispX1":
      var="isp"
      if form.ui.Action____ispX0.isEnabled():
         if form.ui.Action____ispX1.isEnabled():
            txt=str(form.ui.Action____ispX0.currentIndex())+" "+str(form.ui.Action____ispX1.currentIndex())
         else:
            txt=str(form.ui.Action____ispX0.currentIndex())
         if not form.config.has_section(sec):
            form.config.add_section(sec)
         form.config.set(sec,var,txt)
      else:
         if form.config.has_option(sec,var):
            form.config.remove_option(sec,var)
   elif var=="iratX0" or var=="iratX1" or var=="iratX2":
      var="irat"
      if form.ui.Action____iratX0.isEnabled():
         txt=str(form.ui.Action____iratX0.currentText())+" "+str(form.ui.Action____iratX1.currentText())+" "+str(form.ui.Action____iratX2.currentText())
         if not form.config.has_section(sec):
            form.config.add_section(sec)
         form.config.set(sec,var,txt)
      else:
         if form.config.has_option(sec,var):
            form.config.remove_option(sec,var)
   elif var=="im0":
      if form.ui.Action____im0.isEnabled():
         txt=str(form.ui.Action____im0.currentIndex())
         if not form.config.has_section(sec):
            form.config.add_section(sec)
         form.config.set(sec,var,txt)
      else:
         if form.config.has_option(sec,var):
            form.config.remove_option(sec,var)
   #generic code for the rest of the fields
   else:
      if field.isEnabled()==True:
         if not form.config.has_section(sec):
            form.config.add_section(sec)
         try:
            form.config.set(sec,var,str(field.currentText()).split()[0])
         except IndexError:
            print "setVarCmb index error", field.objectName(), str(field.currentText()).split()
      else:
         if form.config.has_option(sec,var):
            form.config.remove_option(sec,var)

def getIndex(listWidget):
   #returns first number of currently selected text in supplied list widget, eg from
   # 3 [ascsdf] sdf sdf
   #would return the integer 3
    try:
        return int(str(listWidget.item(listWidget.currentIndex().row()).text()).split()[0])
    except:
        print "ERROR getIndex",  listWidget.objectName()

def makeValidIndex(listWidget):
   #generates a valid new index for the given list
   lowest_allowed=0
   if str(listWidget.objectName())=="listActions":
      #reserve action index 0 for gauge action
      lowest_allowed=1
   #find and return lowest available valid index
   for i in range(lowest_allowed,31):
      valid=True
      for row in range(0,listWidget.count()):
         if int(str(listWidget.item(row).text()).split()[0])==i:
            valid=False
      if valid==True:
         return i
         
def isValidIndex(listWidget, index):
   #if index is valid, returns True, otherwise returns False
   #otherwise, generates a valid one, and returns index, False
   lowest_allowed=0
   if str(listWidget.objectName())=="listActions":
      #reserve action index 0 for gauge action
      lowest_allowed=1
   #check if supplied index is..
   valid=True
   #within allowed range
   if int(index)<lowest_allowed or int(index)>31:
      valid=False
   #not already used
   for row in range(0,listWidget.count()):
      if int(str(listWidget.item(row).text()).split()[0])==int(index):
         valid=False
   return valid

def populateActionFields(form):
   #populate Action combofields
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
#   form.listSolvers=[]
   for i in range(0,form.ui.listSolvers.count()):
      txt=str(form.ui.listSolvers.item(i).text())
      form.ui.Action____ispX0.addItem(txt)
      form.ui.Action____ispX1.addItem(txt)
      form.ui.Force____isp.addItem(txt)
#      form.listSolvers.append(int(txt.split()[0]))
   form.ui.Action____iratX0.clear()
   form.ui.Action____iratX1.clear()
   form.ui.Action____iratX2.clear()
#   form.listRAT=[]
   for i in range(0,form.ui.listRAT.count()):
      txt=str(form.ui.listRAT.item(i).text())
      form.ui.Action____iratX0.addItem(txt)
#      form.listRAT.append(int(txt.split()[0]))
   for i in range(0,int(form.ui.Rational____degree.text())):
      form.ui.Action____iratX1.addItem(str(i))
      form.ui.Action____iratX2.addItem(str(i))

def populateMDInt(form):
   #get list of all actions
   list_actions=[0]
   for row in range(0,form.ui.listActions.count()):
      list_actions.append(int(str(form.ui.listActions.item(row).text()).split()[0]))
   list_MDactions=[]
   #loop over each integration level, remove any actions that are not in list of actions
   for list in form.ui.tabMDint.findChildren(QtGui.QListWidget):
      for dummy_loop_var in range(list.count()):
         for row in range(list.count()):
            MDaction = int(str(list.item(row).text()).split()[0])
            if MDaction in list_actions:
               if MDaction not in list_MDactions:
                  list_MDactions.append(MDaction)
            else:
               list.takeItem(row)
               break
   #loop over all actions, if not in the list, add to first integration level
#      for row in range(0,form.ui.listActions.count()):
#         action = int(str(form.ui.listActions.item(row).text()).split()[0])
   for action in list_actions:
      if action not in list_MDactions:
         form.ui.tabMDint.findChildren(QtGui.QListWidget)[0].addItem(str(action))

def generateInputFile(form):
   #Generate string containing input file based on data in config
   
   #add HMC parameters to config that are implied by the other parameters.
   strA=[] #list of actions
   for lst in form.ui.tabMDint.findChildren(QtGui.QListWidget):
      setVarList(lst, form)
      for index in range(lst.count()):
         strA.append(int(lst.item(index).text()))
   npf=len(strA)-1
   strA = [str(x) for x in sorted(strA)]
   form.config.set("HMC parameters","actions", ' '.join(strA))
   form.config.set("HMC parameters","npf", str(npf))
   form.config.set("HMC parameters","nlv", str(len(form.ui.tabMDint.findChildren(QtGui.QListWidget))))
   
   #Sorting of sections
   SortedConfig = ConfigParser.RawConfigParser()
   SortedConfig.optionxform = str
   if form.ui.radioSortDefault.isChecked():
      #default ordering
      defaultOrder=["Run", "Directories", "Lattice",  "Boundary",  "Random",  "HMC",  "MD",  "Level",  "Rational", "Action",  "Force",  "Solver",  "SAP",  "Deflation",  "Wilson"]
      for l in defaultOrder:
         for sec in sorted(form.config.sections()):
            if l in sec:
               SortedConfig.add_section(sec)
               for name, value in form.config.items(sec):
                  SortedConfig.set(sec, name, value)
      #add any sections not in default ordering list alphabetically to the end
      for sec in sorted(form.config.sections()):
         if sec not in SortedConfig.sections():
               SortedConfig.add_section(sec)
               for name, value in form.config.items(sec):
                  SortedConfig.set(sec, name, value)
   elif form.ui.radioSortAlpha.isChecked():
      #alphabetical ordering
      for sec in sorted(form.config.sections()):
         SortedConfig.add_section(sec)
         for name, value in form.config.items(sec):
            SortedConfig.set(sec, name, value)
   else:
      #no ordering
      for sec in form.config.sections():
         SortedConfig.add_section(sec)
         for name, value in form.config.items(sec):
            SortedConfig.set(sec, name, value)

   #generate input file in config parser format (i.e. with '=' signs)
   fakefile = StringIO.StringIO()
   SortedConfig.write(fakefile)

   #remove '=' appropriately and return as string
   newstring=""
   for line in fakefile.getvalue().splitlines():
      ll = line.strip()
      if not ll or ll[0]=="[" or ll[0]=="#": 
         #leave unchanged blank lines, or those that start with "[" or "#"
         newstring+=line+'\n'
      else:
         #remove "=" in all other lines
         newstring+=ll.replace("="," ")+'\n'
   return newstring

def getSolver(index, form):
   form.ui.lblSolverIndex.setText(str(getIndex(form.ui.listSolvers)))
   #first read from config what kind of solver it is
   getVarCmb(form.ui.Solver____solver, form)
   #then disable/enable comboboxes based on this
   form.changecmbSolver()
   #finally read from config all the fields
   for txt in form.ui.tabSolvers.findChildren(QtGui.QLineEdit):
      getVarTxt(txt, form)
   getVarCmb(form.ui.Solver____isolv, form)

def getRAT(index, form):
   form.ui.lblRATIndex.setText(str(getIndex(form.ui.listRAT)))
   for txt in form.ui.tabRAT.findChildren(QtGui.QLineEdit):
      getVarTxt(txt, form)

def getAction(index, form):
   #fill in possible values for the various comboboxes
   populateActionFields(form)
   form.ui.lblActionIndex.setText(str(index))
   #first read from config what kind of action it is
   getVarCmb(form.ui.Action____action, form)
   #then disable/enable comboboxes based on the action
   form.changecmbAction()
   #finally read from config all the enabled comboboxes
   #TODO: replace below with call to children on current tab instead of ALL
   getVarALL(form)

def getVarALL(form):
   #Populate all input fields using data in config
   for txt in form.findChildren(QtGui.QLineEdit):
      getVarTxt(txt, form)
   for cmb in form.findChildren(QtGui.QComboBox):
      getVarCmb(cmb, form)

def setVarALL(form):
   #Update all variables in config using data in input fields
   for txt in form.findChildren(QtGui.QLineEdit):
      setVarTxt(txt, form)
   for cmb in form.findChildren(QtGui.QComboBox):
      setVarCmb(cmb, form)
