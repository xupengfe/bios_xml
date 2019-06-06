__author__ = 'ashinde'
import sys, os
XmlCliPath   = os.path.abspath(os.path.dirname(__file__))     # os.getcwd()
XmlCliQaPath = os.sep.join([XmlCliPath, "QA"])
sys.path.append(XmlCliPath)
sys.path.append(XmlCliQaPath)
import XmlCliLib as lib
import XmlCli as cli
import XmlCliQa as Qa

def main():
	if (len(sys.argv) < 2):
		print "\nERROR: at least one argument required\n\n"
		Status = 1
	else:
		Operation = sys.argv[1].lower()
		#  Reads the current values of BIOS knobs and 
		#  compares them against the target values in the
		#  provided INI file
		if (Operation == "readknobs"):
			#  If argument passed with "readknobs", it is a string
			#  representing the knobs to be checked
			if (len(sys.argv) > 2):
				Status = cli.CvReadKnobs(KnobStr=sys.argv[2])
			else:
				Status = cli.CvReadKnobs()
		#  Loads default values for all BIOS knobs
		if (Operation == "loaddefaults"):
			Status = cli.CvLoadDefaults()
		if (Operation == "progknobs"):
			#  If argument passed with "progknobs", it is a string
			#  representing the knobs to be changed
			if (len(sys.argv) > 2):
				Status = cli.CvProgKnobs(KnobStr=sys.argv[2])
			else:
				Status = cli.CvProgKnobs()
		#  Restores BIOS knobs to default values and then
		#  modifies select knobs as specified
		if (Operation == "restoremodify"):
			#  If argument passed with "restoremodify", it is a string
			#  representing the knobs to be checked
			if (len(sys.argv) > 2):
				Status = cli.CvRestoreModifyKnobs(KnobStr=sys.argv[2])
			else:
				Status = cli.CvRestoreModifyKnobs()
		if (Operation == "XmlCliqa"):
			Status = Qa.TestAllScripts()
		if (Operation == "savexml"):
			Status = lib.SaveXml()
		#  Flashes new BIOS image to EEPROM
		if (Operation == "progbios"):
			if (len(sys.argv) < 3):
				print "\n'progbios' command requires additional argument(s):  Filename\n\n'"
				Status = 1
			else:
				Status = cli.cliProgBIOS(sys.argv[2], 0)
	return Status

if __name__ == '__main__':
	Status = main()
	print "%s returning with value %d" % (sys.argv[0], Status)
	sys.exit(Status)
