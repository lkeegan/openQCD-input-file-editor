# Input file editor for openQCD
# Consistency checks module

def isIntegerMultiple(field,unitfield,message):
   #If field is not integer multiple of unitfield, make field RED with tooltip error message
   try:
      remainder=int(field.text())%int(unitfield.text())
   except:
      showConsistency(field, message, False)
      return 1
   if remainder>0:
      showConsistency(field, message, False)
      return 1
   else:
      showConsistency(field, message, True)
      return 0

def isPositiveDouble(field,message):
   #If field is not a positive double, make field RED with tooltip error message
   try:
      if float(field.text()) > 0:
         showConsistency(field, message, True)
         return 0
      else:
         raise ValueError
   except ValueError:
      showConsistency(field, message, False)
      return 1

def isListOfPositiveDoubles(field,message):
   #If field is not a positive double, make field RED with tooltip error message
   field.setText(str(field.text()).replace(","," "))
   for txt in str(field.text()).split():
      try:
         if float(txt) >= 0:
            showConsistency(field, message, True)
         else:
            raise ValueError
      except ValueError:
         showConsistency(field, message, False)
         return 1
   return 0
   
def isListOfNPositiveInts(field,n,message):
   #If field is not a list of n positive integers, make field RED with tooltip error message
   field.setText(str(field.text()).replace(","," "))      
   try:
      if len(str(field.text()).split()) <> 4:
         raise ValueError               
      for txt in str(field.text()).split():
         if float(txt)%int(txt) == 0:
            showConsistency(field, message, True)
         else:
            raise ValueError
   except ValueError:
      showConsistency(field, message, False)
      return 1
   return 0
   
def showConsistency(field, message, isconsistent):
   #if inconsistent==False, make text field RED with tooltip error message, otherwise normal colour&no tooltip message
   if isconsistent==True:
      field.setStyleSheet("")
      field.setToolTip("")
   else:
      field.setStyleSheet("QLineEdit { background-color : red;}")
      field.setToolTip(message)            
