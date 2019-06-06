#!/usr/bin/env python2.6
__author__ = 'ashinde'
import os, time, re, glob
import xml.etree.ElementTree as ET
import XmlCliLib as lib
import XmlCli as cli

Count = 1
XmlCliBaseDir = os.path.dirname(os.path.dirname(lib.PlatformConfigXml))
QaBaseDir = os.sep.join([XmlCliBaseDir, "QA"])
OutPath = os.sep.join([XmlCliBaseDir, "QA\Out"])
try:
	BIOS_Flash_File = glob.glob(os.sep.join([QaBaseDir, "*.bin"]))[0]
except:
	BIOS_Flash_File = r"DummyBios.bin"
Full_CpuSv_PC_Xml = os.sep.join([OutPath, "Full_CpuSv_PC.xml"])
Full_SVOS_PC_Xml = os.sep.join([OutPath, "Full_SVOS_PC.xml"])
BIOS_Knobs_Xml = os.sep.join([OutPath, "BiosKnobs.xml"])
Full_Default_PC_Xml = os.sep.join([OutPath, "Full_Default_PC.xml"])
AP_XML_FILE = os.sep.join([OutPath, "Full_PC_AP.xml"])
RO_XML_FILE = os.sep.join([OutPath, "Full_PC_RO.xml"])
RM_XML_FILE = os.sep.join([OutPath, "Full_PC_RM.xml"])
LD_XML_FILE = os.sep.join([OutPath, "Full_PC_LD.xml"])
XML_HDR_FILE = os.sep.join([OutPath, "XmlHeader.xml"])
Putty_CpuSv_reg = os.sep.join([QaBaseDir, "Putty_CpuSv.reg"])
Putty_SVOS_reg = os.sep.join([QaBaseDir, "Putty_SVOS.reg"])
Putty_Misc_reg = os.sep.join([QaBaseDir, "Putty_Misc.reg"])
AllKnobs = os.sep.join([OutPath, "AllKnobs.ini"])
Result_File = os.sep.join([OutPath, "DefaultResult.csv"])
BIOS_Fetch_file= os.sep.join([OutPath, "DefaultBios.bin"])
CpuSv_INI_FILE= os.sep.join([QaBaseDir, "BiosKnobs_CpuSv.ini"])
CpuSv_ITAasHIF_INI= os.sep.join([QaBaseDir, "BiosKnobs_CpuSvItpAsHif.ini"])
SVOS_INI_FILE= os.sep.join([QaBaseDir, "BiosKnobs_SVOS.ini"])
BiosKnobs_BIN_FILE = os.sep.join([OutPath, "biosKnobsdata.bin"])
BiosKnobs_Res_BIN_FILE = os.sep.join([OutPath, "KnobsRespBuff.bin"])
BootTime = 300

# This function will validate patch loaded by reading MSR 0x8B
def Test_Patch():
	global Count
	Patch_Val = lib.ReadMSR(0x8B)
	XmlType = GetType(0)
	if (Patch_Val !=0):
		PrintToFile(" %d, Test Patch Value , PASS, %s, Patch Value is valid" %(Count, XmlType), 1)
	else :
		PrintToFile(" %d, Test Patch Value , FAIL, %s, Patch Value is invalid " %(Count, XmlType), 1)
	return

# This function will clear all CMOS locations and check if knob values got replicated accordingly 
def Test_CMOS_Clear():
	global Count, Full_Default_PC_Xml
	lib.InitInterface()
	lib.clearcmos()
	lib.CloseInterface()
	lib.coldreset()
	Status = Loop_For_Boot()
	XmlType = GetType(0)
	if (Status == False ):
		PrintToFile(" %d, Test clear CMOS, FAIL, %s, Cold Reset resulted in BIOS hang " %(Count, XmlType), 1)
		return
	Status = cli.savexml(Full_Default_PC_Xml)
	XmlType = GetType(Full_Default_PC_Xml)
	Status_Prs = PrsXml(Full_Default_PC_Xml,"loaddefaults")	# Flag LoadDefaults will compare Current Value and Default value of Knobs 
	if (Status_Prs == True):
		PrintToFile(" %d, Test clear CMOS , PASS, %s, Clearing CMOS locations passed" %(Count ,XmlType ), 1)
	else:
		PrintToFile(" %d, Test Clear CMOS , FAIL, %s, Clearing CMOS locations failed" %(Count, XmlType), 1)
	return

# This function will test SMBASE Value at PostCode 0xF5 , 0xF6 and SVOS
def Test_SMBASE_Value():
	global Count
	SmBase = lib.ReadSmbase()
	lib.InitInterface()
	XmlType = GetType(0)
	CheckPoint = lib.readIO(0x80,1)
	if (CheckPoint == 0xF6):
		if (SmBase == 0x30000 ):
			PrintToFile(" %d, Test SMBASE Value at Checkpoint 0x%X, PASS, %s, SMbase value is 0x%X " %((Count), CheckPoint, XmlType, SmBase), 1)
		else :
			PrintToFile(" %d, Test SMBASE Value at Checkpoint 0x%X, FAIL, %s, SMbase value is 0x%X" %((Count),  CheckPoint, XmlType, SmBase), 1)
	else:
		if ((SmBase != 0x30000) and ( SmBase != 0)):
			PrintToFile(" %d, Test SMBASE Value at Checkpoint 0x%X, PASS, %s, SMbase value is 0x%X" %((Count), CheckPoint, XmlType,SmBase), 1)
		else :
			PrintToFile(" %d, Test SMBASE Value at Checkpoint 0x%X, FAIL, %s, SMbase value is 0x%X" %((Count), CheckPoint, XmlType, SmBase), 1)
	lib.CloseInterface()
	return

def Test_Cold_Reset():
	global Count
	lib.coldreset()
	Status = Loop_For_Boot()
	XmlType = GetType(0)
	if (Status == False ):
		PrintToFile(" %d, Test Cold Reset, FAIL, %s, Cold Reset resulted in BIOS hang " %(Count, XmlType), 1)
	else:
		PrintToFile(" %d, Test Cold Reset, PASS, %s, Cold reset executed successfully" %(Count, XmlType), 1)
	return

def Test_Warm_Reset():
	global Count
	lib.warmreset()
	Status = Loop_For_Boot()
	XmlType = GetType(0)
	if (Status == False ):
		PrintToFile(" %d, Test Warm Reset, FAIL, %s, Warm Reset resulted in BIOS hang " %(Count, XmlType), 1)
	else:
		PrintToFile(" %d, Test Warm Reset, PASS, %s, Warm reset executed successfully" %(Count, XmlType), 1)
	return

#Test if Mailbox Address is valid or not
def Test_MailBox_Addr():
	global Count
	lib.InitInterface()
	Test_Patch()
	DRAM_MbAddr = lib.GetDramMbAddr()
	XmlType = GetType(0)
	lib.CloseInterface()
	if((DRAM_MbAddr == 0) or (DRAM_MbAddr == 0xffffffff)):
		PrintToFile(" %d, Test Shared Mailbox Address = 0x%X, FAIL, %s, Mailbox address is invalid" %(Count, DRAM_MbAddr, XmlType), 1)
	PrintToFile(" %d, Test Shared Mailbox Address = 0x%X, PASS, %s, Mailbox address is valid" %(Count, DRAM_MbAddr, XmlType), 1)
	return

def Test_Legcy_MB_Addr(ItpAsHif):
	global Count
	lib.InitInterface()
	DRAM_MbAddr = lib.GetDramMbAddr()
	DramSharedMBbuf = lib.memBlock(DRAM_MbAddr,0x200)
	LegMailboxAddrOffset = lib.readLegMailboxAddrOffset(DramSharedMBbuf)
	XmlType = GetType(0)
	lib.CloseInterface()
	if(ItpAsHif):
		LegMailboxAddr = (DRAM_MbAddr + LegMailboxAddrOffset);          # set Legacy mailbox address pointing to DRAM, since its ITP as HIF
	else:
		LegMailboxAddr = lib.ReadBuffer(DramSharedMBbuf, + (LegMailboxAddrOffset + 0x4C), 4, lib.HEX)+ LegMailboxAddrOffset   # Read SvHif Cards Legacy Mailbox address from Dram Shared Mailbox
	if ( (LegMailboxAddr == 0) or (LegMailboxAddr == 0xFFFFFFFF) ):
		PrintToFile("%d, Test Legacy Mailbox Address if ItpAsHif %d , FAIL, %s, Legacy mailbox address is invalid = 0x%X" % (Count , ItpAsHif , XmlType ,LegMailboxAddr), 1)
	PrintToFile("%d, Test Legacy Mailbox Address if ItpAsHif %d , PASS, %s, Legacy mailbox address is valid =  = 0x%X" % (Count , ItpAsHif , XmlType, LegMailboxAddr), 1)
	return

def Test_XML_Validity(XmlFile):
	global Count
	lib.InitInterface()
	DRAM_MbAddr = lib.GetDramMbAddr()
	DramSharedMBbuf = lib.memBlock(DRAM_MbAddr,0x200)
	(XmlAddr,XmlSize)  = lib.readxmldetails(DramSharedMBbuf)
	Status = lib.isxmlvalid(XmlAddr,XmlSize)
	XmlType = GetType(0)
	if(Status == True):
		PrintToFile("%d, Check if XML is valid , PASS, %s, XML is valid" % (Count, XmlType), 1)
	else:
		PrintToFile("%d, Check if XML is valid , FAIL, %s, XML is invalid" % (Count, XmlType), 1)
	Status = cli.savexml(XmlFile)
	XmlType = GetType(XmlFile)
	if(Status == 0):
		PrintToFile("%d, Save Platform Config XML file  , PASS, %s ,Saved full PlatformConfig.xml and can be found at %s" % (Count, XmlType, XmlFile), 1)
	else:
		PrintToFile("%d, Save Platform Config XML file  , FAIL, Invalid XML Type, Failed to download XML" % (Count), 1)
	lib.CloseInterface()
	return

def Test_Fetch_BIOS(filename, BlkOffset, BiosSize):
	global Count
	Status = cli.FetchSpi(filename, BlkOffset, BiosSize)
	XmlType = GetType(0)
	if (Status == 0):
		PrintToFile("%d, Test fetching BIOS Binary  , PASS, %s, BIOS fetched successfully and can be found at %s " % (Count, XmlType, filename), 1)
	else:
		PrintToFile("%d, Test fetching BIOS Binary  , FAIL, %s, Failed to fetch BIOS " % (Count, XmlType), 1)
	return

def Test_Flash_BIOS(filename, Region):
	global Count
	Status = cli.cliProgBIOS(filename, Region)
	if(Status == 1):
		lib.coldreset()
		Status = Loop_For_Boot()
		XmlType = GetType(0)
		if (Status == False):
			PrintToFile("%d, Test Flashing Complete BIOS Binary  , FAIL, %s, Flashing BIOS binary failed and resulted into hang after reset " % (Count, XmlType), 1)
		Status = cli.cliProgBIOS(filename, Region)
	XmlType = GetType(0)
	if(Status == 0):
		PrintToFile("%d, Test Flashing Complete BIOS Binary  , PASS, %s, Flashing BIOS binary passed" % (Count, XmlType), 1)
	else:
		PrintToFile("%d, Test Flashing Complete BIOS Binary  , FAIL, %s, Flashing BIOS binary failed " % (Count,XmlType), 1)
	lib.coldreset()
        return

def Test_ProgKnobs(Command):
	global Count, AP_XML_FILE, BiosKnobs_BIN_FILE, BiosKnobs_Res_BIN_FILE
	Status = cli.cliProcessKnobs(lib.PlatformConfigXml, lib.KnobsIniFile, Command, 0, 1, 0)
	XmlType = GetType(0)
	if (Status == 1):
		PrintToFile("%d, Test Program  Knobs  , FAIL, %s , Append Knobs Failed " % (Count, XmlType), 1)
		return
	Status = cli.cliProcessKnobs(lib.PlatformConfigXml, lib.KnobsIniFile, lib.CLI_KNOB_READ_ONLY, 0, 1, BiosKnobs_Res_BIN_FILE)
	if (Status == 1):
		PrintToFile("%d, Test Program Knobs  , FAIL, %s, Restore Modify Knobs Failed" % (Count, XmlType), 1)
		return
	InputFile = open(BiosKnobs_BIN_FILE, 'rb')
	InputFilePart = InputFile.read()
	InputFile.close()
	OutputFile = open(BiosKnobs_Res_BIN_FILE, 'rb')
	OutputFilePart = OutputFile.read()
	OutputFile.close()
	offset1 = 4
	offset2 = 0
	check = 0
	NumberOfEntries = lib.ReadBuffer(InputFilePart, 0 , 4, lib.HEX)
	while(NumberOfEntries != 0):
		Input_Knob_Size = lib.ReadBuffer(InputFilePart, offset1+3 , 1, lib.HEX)
		Output_Knob_Size = lib.ReadBuffer(OutputFilePart, offset2+9 , 1, lib.HEX)
		InputValue = lib.ReadBuffer(InputFilePart, offset1+4 , Input_Knob_Size, lib.HEX)
		OutputValue = lib.ReadBuffer(OutputFilePart, offset2+10+Output_Knob_Size , Output_Knob_Size, lib.HEX)
		if(InputValue != OutputValue):
			check = check+1
			break
		offset1 = offset1+4+Input_Knob_Size   # Current offset + Knob Value offset +Knob size
		offset2 = offset2+10+(Output_Knob_Size*2) # Current offset + Knob value offset (in this case it will have both default and current) + Knob size
		NumberOfEntries = NumberOfEntries-1
	if (check > 0):
		PrintToFile("%d, Test Program Knobs  , FAIL, %s, Updating knobs failed to load requested values" % (Count, XmlType), 1)
		return
	else:
		PrintToFile("%d, Test Program Knobs  , PASS, %s, Updating Knobs passed " % (Count, XmlType), 1)
	lib.coldreset()
	Status = Loop_For_Boot()
	if (Status == False):
		PrintToFile("%d, Test Program Knobs  , FAIL, %s, Updating knobs resulted into BIOS hang " % (Count, XmlType), 1)
		return
	if (Command == lib.CLI_KNOB_APPEND):
		Status =  cli.savexml(AP_XML_FILE)
		XmlType = GetType(AP_XML_FILE)
		if (Status == 1):
			PrintToFile("%d, Test Program Knobs  , FAIL, %s, Failed to save XML after programming Knobs (AP)  " % (Count, XmlType), 1)
			return
		Status_Prs = PrsXml(AP_XML_FILE,"updateknobs")
	else:
		Status =  cli.savexml(RM_XML_FILE)
		XmlType = GetType(RM_XML_FILE)
		if (Status == 1):
			PrintToFile("%d, Test Program Knobs  , FAIL, %s, Failed to save XML after programming Knobs (RM)  " % (Count, XmlType), 1)
			return
		Status_Prs = PrsXml(RM_XML_FILE,"updateknobs")
	if (Status_Prs == False ):
		PrintToFile("%d, Test Program Knobs after reset , FAIL, %s, Test programming knobs after reset failed" % (Count, XmlType), 1)
	else:
		PrintToFile("%d, Test Program Knobs after reset  , PASS, %s, Test programming knobs after reset passed" % (Count, XmlType), 1)
	return

# this function needs to be modiied / not working for now for this we  need to parse xml and get current value of knob. compare that current value with value in response buffer
def Test_ReadKnobs(KnobIniFile, PrintResBuff):
	global Count
	Status = cli.cliProcessKnobs(RO_XML_FILE, KnobIniFile, lib.CLI_KNOB_READ_ONLY, 0, PrintResBuff, BiosKnobs_Res_BIN_FILE)
	XmlType = GetType(RO_XML_FILE)
	if (Status == 1):
		PrintToFile("%d, Test Read Only Knobs   , FAIL, %s, ReadKnobs() failed" % (Count, XmlType), 1)
		return False
	Status_Prs = PrsXml(RO_XML_FILE,"ReadOnly")
	if (Status_Prs == False ):
		PrintToFile("%d, Test Read Only Knobs , FAIL, %s, ReadKnobs failed after comparing values from XML with values from Response buffer" % (Count, XmlType), 1)
	else:
		PrintToFile("%d, Test Read Only Knobs , PASS, %s, ReadKnobs() executed successfully " % (Count, XmlType), 1)
	return Status_Prs

def Test_LoadDefaults():
	global Count
	Status_LD = cli.CvLoadDefaults()
	XmlType = GetType(0)
	if (Status_LD != 0):
		PrintToFile("%d, Test Loading default Knobs  , FAIL, %s, Loading knobs to default values failed " % (Count, XmlType), 1)
		return
	lib.coldreset()
	Status = Loop_For_Boot()
	XmlType = GetType(0)
	if (Status == False):
		PrintToFile("%d, Test Loading default Knobs  , FAIL, %s, Restart after loading knobs to default values failed" % (Count, XmlType), 1)
		return 
	Status = cli.savexml(LD_XML_FILE)
	if ( Status == 1):
		PrintToFile("%d, Test Loading default Knobs  , FAIL, Invalid XML Type ,LoadDefaults() failed to save XML after applying knobs " % (Count), 1)
		return
	XmlType = GetType(LD_XML_FILE)
	Status_Prs = PrsXml(LD_XML_FILE,"loaddefaults")
	if (Status_Prs == True):
		PrintToFile("%d, Test Loading default Knobs  , PASS, %s, Restart after loading knobs to default values passed" % (Count, XmlType), 1)
	else :
		PrintToFile("%d, Test Loading default Knobs  , FAIL, %s, Restart after loading knobs to default values failed" % (Count, XmlType), 1)
	return Status_Prs

# For this main CLI function needs to be changed ( create output bin file )
def Test_GangesProgKnobs(ItpAsHif, xmlfile, inifile):
	global Count
	#print "TestGangesProgKnobs"
	Status = cli.gangesProgKnobs(ItpAsHif, xmlfile, inifile)
	XmlType = GetType(xmlfile)
	if (Status == 1 ):
		PrintToFile("%d, Test Ganges Program  Knobs  , FAIL, %s, GangesProgKnobs() failed to write specified knobs to Nvar " % (Count, XmlType), 1)
		return
	PrintToFile("%d, Test Ganges Program  Knobs , PASS, %s, GangesProgKnobs() passed to update requested knob values" % (Count, XmlType), 1)
	lib.coldreset()
	Status = Loop_For_Boot()
	XmlType = GetType(0)
	if (Status == False):
		PrintToFile("%d, Test Ganges Program  Knobs  , FAIL, %s, GangesProgKnobs() failed to reboot after applying knobs " % (Count, XmlType), 1)
		return 
	Status =  cli.savexml(Full_CpuSv_PC_Xml)
	XmlType = GetType(Full_CpuSv_PC_Xml)
	if (Status == 1):
		PrintToFile("%d, Test Ganges Program  Knobs  , FAIL, %s, GangesProgKnobs() failed to save XML after applying knobs " % (Count, XmlType), 1)
		return
	Status_Prs = PrsXml(Full_CpuSv_PC_Xml,"updateknobs")
	if (Status_Prs == False ):
		PrintToFile("%d, Test Ganges Program  Knobs after reset , FAIL, %s, GangesProgKnobs() failed to modify requested knobs after restart " % (Count, XmlType), 1)
	else:
	  PrintToFile("%d, Test Ganges Program Knobs after reset  , PASS, %s, GangesProgKnobs() passed to modify knobs after resetting" % (Count, XmlType), 1)
	return

def Loop_For_Boot():
	Temp_Var = 1
	LoopCount = 0
	ResetRecNum = 0
	time.sleep(BootTime)
	while (1):
		time.sleep(30)
		LoopCount = LoopCount +1
		lib.InitInterface()
		DRAM_MbAddr = lib.GetDramMbAddr()
		if (DRAM_MbAddr != 0):
			DramSharedMBbuf = lib.memBlock(DRAM_MbAddr,0x200)
			(XmlAddr,XmlSize)  = lib.readxmldetails(DramSharedMBbuf)
			Status = lib.isxmlvalid(XmlAddr,XmlSize)
			if (Status == True):
				lib.CloseInterface()
				return True
		if (LoopCount > 20):
			if (ResetRecNum > 2):
				lib.CloseInterface()
				return False
			if (ResetRecNum == 2):
				lib.clearcmos()
			ResetRecNum = ResetRecNum + 1
			LoopCount = 0
			lib.CloseInterface()
			lib.coldreset()
			continue
		lib.CloseInterface()
	return False

def PrintToFile(String, TestResult=0):
	global Result_File, Count
	if (TestResult):
		Count = Count + 1
	Result = open(Result_File,'a')
	Result.write("\n%s" %(String))
	print "\n---------------------------------------------------------------------"
	print "%s" %(String)
	print "---------------------------------------------------------------------\n"
	Result.close()
	return

# Global variable
tree=None
# User defined Function
#-----------------------
def nstrip(strg,nonetype=''):
	if strg is not None:
		return(strg.strip())
	else:
		return(nonetype)

def GetCurrBootTime():
	global BootTime
	from components import ComponentManager
	sv=ComponentManager(["socket"])
	print "Default Boot Time is set to %d" %BootTime
	StartTime = time.time()
	lib.coldreset()
	time.sleep(30)
	sv.refresh()
	for index in range (0, 100):
		time.sleep(5)
		PostCode = (sv.socket0.uncore0.biosnonstickyscratchpad7 >> 16)
		if( (PostCode == 0x57CE) or (PostCode == 0xF500) ):
			BootTime = (time.time() - StartTime) + 30	# 30 seconds of buffer
			print "Current Boot Time is set to %d" %BootTime
			time.sleep(30)
			return True
	print "we didn't seem to Successfully Boot"
	return False

def Test_Clear_Knobs():
	global Count, AllKnobs, BIOS_Knobs_Xml, RO_XML_FILE
	lib.fetchHdrNknob(BIOS_Knobs_Xml)
	Status_Prs = PrsXml(BIOS_Knobs_Xml, "clearknobs")
	XmlType = GetType(BIOS_Knobs_Xml)
	if (Status_Prs == False):
		PrintToFile("%d, Test Prog All Knobs to 0, FAIL, %s, Parsing XML to clear all knobs to Value 0 failed" % (Count, XmlType), 1)
		return
	XmlType= GetType(BIOS_Knobs_Xml)
	Status = cli.cliProcessKnobs(BIOS_Knobs_Xml, AllKnobs, lib.CLI_KNOB_APPEND, 0, 0, BiosKnobs_Res_BIN_FILE)	# disable printing res buff table for all the knobs.
	if (Status != 0):
		PrintToFile("%d, Test Prog All Knobs to 0, FAIL, %s, Clearing all knobs to Value 0 failed" % (Count, XmlType), 1)
		return
	lib.fetchHdrNknob(RO_XML_FILE)
	Test_ReadKnobs(AllKnobs, 0)	# disable printing res buff table for all the knobs.
	XmlType = GetType(RO_XML_FILE)

	ResBuffFile = open(BiosKnobs_Res_BIN_FILE, "rb")
	ResBuffFilePart = ResBuffFile.read()
	ResBuffFile.close()
	SizeOfResBuff = len(ResBuffFilePart)
	ResBuffPtr = 0
	ErrorFlag = 0
	while(ResBuffPtr < SizeOfResBuff):
		KnobSize = lib.ReadBuffer(ResBuffFilePart, ResBuffPtr+9 , 1, lib.HEX)
		Curr_Res_buffer_Val =  lib.ReadBuffer(ResBuffFilePart, ResBuffPtr+10+KnobSize , KnobSize, lib.HEX)
		if (Curr_Res_buffer_Val != 0):
			ErrorFlag = ErrorFlag + 1
		ResBuffPtr = ResBuffPtr+10+(KnobSize*2) 		# Current offset + Knob value offset (in this case it will have both default and current) + Knob size
	if (ErrorFlag == 0):
		PrintToFile("%d, Test Prog All Knobs to 0, PASS, %s, Response buffer Test shows all knobs are set to vlaue 0" % (Count, XmlType), 1)
	else:
		PrintToFile("%d, Test Prog All Knobs to 0, FAIL, %s, Response buffer indicates that %d knobs were not set to vlaue 0" % (Count, XmlType, ErrorFlag), 1)
	Status_Prs = PrsXml(RO_XML_FILE, "clearallknobs")
	cli.cliProcessKnobs(BIOS_Knobs_Xml, AllKnobs, lib.CLI_KNOB_LOAD_DEFAULTS, 0, 0, BiosKnobs_Res_BIN_FILE)
	if (Status_Prs == False):
		PrintToFile("%d, Test Prog All Knobs to 0, FAIL, %s, XML CurrentVal shows atleast one knob is not set to vlaue 0" % (Count,XmlType), 1)
	else:
		PrintToFile("%d, Test Prog All Knobs to 0, PASS, %s, XML CurrentVal shows all knobs are set to vlaue 0" % (Count, XmlType), 1)
	return

def PrsXml(xmlfile, Flag):
	global tree, BiosKnobs_Res_BIN_FILE, AllKnobs
	knobTree={}
	Temp = 0
	Check = 1
	Flag = Flag.lower()
	tree = ET.parse(xmlfile)
	ErrorFlag = 0

	if (Flag == "clearknobs"):
		INI = open(AllKnobs, 'wb')
		INI.write("[BiosKnobs]\n")

	elif (Flag == "XmlType"):
		for Type in tree.getiterator(tag="GBT"):
			return Version.get('Type')

	for SetupKnobs in tree.getiterator(tag="biosknobs"):
		for BiosKnob in SetupKnobs.getchildren():
			SETUPTYPE = (nstrip(BiosKnob.get("setupType"))).upper()
			if SETUPTYPE in ["ONEOF", "CHECKBOX", "NUMRIC" ,"NUMERIC","STRING"]:
				CurrVal = int(nstrip(BiosKnob.get('CurrentVal')), 16)
				DefVal = int(nstrip(BiosKnob.get('default')), 16)
				CurKnobName = nstrip(BiosKnob.get('name'))
				if (Flag == "updateknobs"):
					IniFile = lib.KnobsIniFile
					inimap = getBiosini(IniFile)
					for ReqKnobName in inimap:
						if (ReqKnobName == CurKnobName ):
							ReqVal = int(inimap[ReqKnobName], 16)
							#print "Curr Val 0x%X, Def Value : 0x%X" %(CurrVal,DefVal)
							if(ReqVal != CurrVal):
								print "Knob %s  Req value 0x%X, Current XML Value 0x%X\n" %(CurKnobName, ReqVal, CurrVal)
								ErrorFlag = ErrorFlag + 1
				if ((Flag == "loaddefaults") and (CurrVal != DefVal)):
					print "Current value does not match with default value "
					print "Knob Name : %s Default value 0x%X,Current Value 0x%X\n" %(CurKnobName, CurrVal, DefVal)
					ErrorFlag = ErrorFlag + 1
				if (Flag == "ReadOnly"):
					ResBuffFile = open(BiosKnobs_Res_BIN_FILE, "rb")
					ResBuffFilePart = ResBuffFile.read()
					ResBuffFile.close()
					SizeOfResBuff = len(ResBuffFilePart)
					ResBuffPtr = 0
					VarId = int(nstrip(BiosKnob.get('varstoreIndex')), 16)
					KnobOffset = int(nstrip(BiosKnob.get('offset')), 16)
					while(ResBuffPtr < SizeOfResBuff):
						KnobSize = lib.ReadBuffer(ResBuffFilePart, ResBuffPtr+9 , 1, lib.HEX)
						VarId_Resbuf =  lib.ReadBuffer(ResBuffFilePart, ResBuffPtr+6, 1, lib.HEX)
						Offset_Resbuf = lib.ReadBuffer(ResBuffFilePart, ResBuffPtr+7, 2, lib.HEX)
						if( (KnobOffset == Offset_Resbuf) and (VarId == VarId_Resbuf) ):
							Def_Res_buffer_Val = lib.ReadBuffer(ResBuffFilePart, ResBuffPtr+10, KnobSize, lib.HEX)
							Curr_Res_buffer_Val =  lib.ReadBuffer(ResBuffFilePart, ResBuffPtr+10+KnobSize , KnobSize, lib.HEX)
							if ((Curr_Res_buffer_Val != CurrVal) or (Def_Res_buffer_Val != DefVal)):
								ErrorFlag = ErrorFlag + 1
							break
						ResBuffPtr = ResBuffPtr+10+(KnobSize*2) 		# Current offset + Knob value offset (in this case it will have both default and current) + Knob size
				if (Flag == "clearknobs"):
					INI.write("%s = 0x0 \n" %(CurKnobName))
				if (Flag == "clearallknobs"):
					if (CurrVal != 0):
						ErrorFlag = ErrorFlag + 1
						print "Knob Name : %s Default value 0x%X   Current Value 0x%X\n" %(CurKnobName, CurrVal, DefVal)
				if(ErrorFlag):
					break
			elif SETUPTYPE in ["LEGACY"]:
				continue
			else:
				print "Setup Type is unknown for biosName[%s] setupType[%s]. " %(nstrip(BiosKnob.get("name")),SETUPTYPE)
	if (Flag == "clearknobs"):
		INI.close()
	if(ErrorFlag):
		return False
	return True

def Test_Passing_Seed():
	SeedTimeOut = 0
	ErrorFlag = 0
	os.system('start /b /d "C:\SVShare\Satellite\Version" Satellite.exe')
	while(1):
		lib.InitInterface()
		CheckPoint = lib.readIO(0x80, 1)
		lib.CloseInterface()
		if (CheckPoint == 0x11):
			print " Waiting for OBJ "
			break 
	while (SeedTimeOut < 200):
		lib.InitInterface()
		CheckPoint = lib.readIO(0x80, 1)
		lib.CloseInterface()
		print CheckPoint
		if ((CheckPoint == 0x33) or (CheckPoint == 0x44)):
			if (CheckPoint == 0x33):
				ErrorFlag = ErrorFlag +1
			break
		time.sleep(1)
		SeedTimeOut = SeedTimeOut + 1
	cmd='''
powershell -command  "&{ Get-Process | ForEach-Object { if ($_.ProcessName -eq 'Satellite') { $_.Kill() }}}"
	'''
	os.system(cmd)

def GetType(XmlFile):
	global tree
	if(XmlFile == 0):
		lib.InitInterface()
		DRAM_MbAddr = lib.GetDramMbAddr() # Get DRam MAilbox Address.
		DramSharedMBbuf = lib.memBlock(DRAM_MbAddr,0x200) # Read/save parameter buffer
		if ((lib.ReadBuffer(DramSharedMBbuf, lib.SHAREDMB_SIG1_OFF, 4, lib.HEX) != lib.SHAREDMB_SIG1 )):
			print "Dram Shared Mailbox not Valid, hence exiting"
			lib.CloseInterface()
			return ''
		(XmlAddr,XmlSize)  = lib.readxmldetails(DramSharedMBbuf) # read GBTG XML address and Size
		if (XmlAddr == 0):
			print "Dram Shared Mailbox not Valid or XML not yet generated, hence exiting"
			lib.CloseInterface()
			return ''
		if(lib.isxmlvalid(XmlAddr,XmlSize)): # Check if XML is valid and generated in the target memory
			print "Target XML is valid, Downloading just the Header & knobs section from XML"
			tmpbuf = lib.memBlock(XmlAddr+0x0A,0x200)   # Read first 512 chars from XML base
			size = 0
			count = 0
			while(1):
				Val = lib.ReadBuffer(tmpbuf, size, 2, lib.ASCII) # mismatch, read Target header
				size +=1
				if(Val == "/>"):
					count +=1
				if(count == 3):
					break
				if(size >= 0x200):
					break
			size +=3
			KXML=open(XML_HDR_FILE,'w')
			KXML.write(lib.XML_START+"\r\n")
			KXML.write(lib.ReadBuffer(tmpbuf, 0, size, lib.ASCII))  # save target XML header to host
			KXML.write(lib.XML_END+"\r\n")
			KXML.close()
			XmlFile = XML_HDR_FILE
		lib.CloseInterface()
	tree = None
	if tree is None:
		tree = ET.parse(XmlFile)
	_BIOSTYPE=''
	for Type in tree.getiterator(tag="GBT"):
		_BIOSTYPE = Type.get('Type')
	return _BIOSTYPE

def getBiosini(fname):
	INI=open(fname)
	biosiniList=INI.readlines()
	INI.close()
	iniList={}
	knobStart=0
	i=0
	while i< len(biosiniList):
		line=biosiniList[i]
		if line.strip() == '[BiosKnobs]':
			knobStart=1
			i=i+1
			continue
		if knobStart==1:
			knobName=knobValue=''
			line=line.split(';')[0]
			if line.strip() <> '':
				(knobName,knobValue) = line.split('=')
				#print "knob name %s " %(knobName)
				iniList[knobName.strip()] = knobValue.strip()
		i=i+1
	return iniList

def CleanLogFile(fname, OutFilename):
	Out = open(OutFilename,'w')
	count = 0
	for line in open(fname,'r').readlines():
		if (count == 0):
			count = 1
			if (list(line)[0] == "\xFF") and (list(line)[1] == "\xFE"):
				print "Found BOM, Ignoring it"
				continue
		line = line.replace("\0", "")
		match = re.search("\[\s*\S*\s*\]\s*h\w*lt\s*command\s*break\s*at", line, re.IGNORECASE)
		if(match != None):
			continue
		match = re.search("\[\s*\S*\s*\]\s*h\w*lt\s*instruction\s*break\s*at", line, re.IGNORECASE)
		if(match != None):
			continue
		match = re.search("\[\s*\S*\s*\]\s*wait\s*for\s*sipi\s*loop\s*break\s*at", line, re.IGNORECASE)
		if(match != None):
			continue
		Out.write(line)
	Out.close()

def Miscelleneous_Test_Functions():
	global BIOS_Fetch_file, BIOS_Flash_File, Count
	PrintToFile (" Miscelleneous TESTS ")
	Test_Clear_Knobs()
	Test_Fetch_BIOS(BIOS_Fetch_file, 0x800000, 0x800000 )
	Test_Flash_BIOS(BIOS_Flash_File, 1)
	lib.coldreset()
	Status = Loop_For_Boot()
	XmlType = GetType(0)
	if (Status == False):
		PrintToFile("%d, Reset after BIOS Flash , FAIL, %s, Reboot Failed" % (Count, XmlType), 1)
		return
	#lib.coldreset()
	#Status = Loop_For_Boot()
	#XmlType = GetType(0)
	#if (Status == False):
	#	PrintToFile("%d, Reset after BIOS Flash , FAIL, %s, Reboot Failed" % (Count, XmlType), 1)
	#	return
	return

def XmlCli_Tests(FullXmlFile):
	Test_Cold_Reset()
	Test_Warm_Reset()
	Test_MailBox_Addr()
	Test_XML_Validity(FullXmlFile)
	Test_ReadKnobs(lib.KnobsIniFile, 1)
	Test_ProgKnobs(lib.CLI_KNOB_APPEND)
	Test_CMOS_Clear()
	return

def CpuSv_Test_Functions():
	global Count, BootTime
	lib.KnobsIniFile = CpuSv_INI_FILE
	lib.PlatformConfigXml = Full_CpuSv_PC_Xml
	Status = cli.cliProcessKnobs(Full_CpuSv_PC_Xml, CpuSv_INI_FILE, lib.CLI_KNOB_RESTORE_MODIFY, 0, 1, 0)
	BootTime = BootTime - 30	# note we had added 30 seconds to the boot time, CpuSv boot don't need this buffer.
	Test_Cold_Reset()
	XmlType = GetType(0)
	if (Status == 1):
		PrintToFile("%d, Prog BOOT to CpuSv flow, FAIL, %s , Append/Prog Knobs Failed " % (Count, XmlType), 1)
		return
	PrintToFile (" CpuSv TESTs ")
	Test_Legcy_MB_Addr(0)
	Test_Legcy_MB_Addr(1)
	Test_SMBASE_Value()
	Test_GangesProgKnobs(0, Full_CpuSv_PC_Xml, CpuSv_ITAasHIF_INI)	# with run with Kfir/Dishon as HIF
	Test_GangesProgKnobs(1, Full_CpuSv_PC_Xml, CpuSv_INI_FILE)		# now will run with ITP as HIF
	XmlType = GetType(0)
	Status = cli.gangesProgKnobs(0, Full_CpuSv_PC_Xml, CpuSv_INI_FILE)
	lib.InitInterface()
	CheckPoint = lib.readIO(0x80,1)
	if (Status == 1) or (CheckPoint != 0xF6):
		PrintToFile("%d, CpuSv Boot to 0xF6  , FAIL, %s, GangesProgKnobs() failed to Reach 0xF6 " % (Count, XmlType), 1)
		return
	PrintToFile("%d, CpuSv Boot to 0xF6  , PASS, %s, GangesProgKnobs() Now Reached 0xF6 " % (Count, XmlType), 1)
	Test_SMBASE_Value()
	lib.CloseInterface()
	XmlCli_Tests(Full_CpuSv_PC_Xml)
	BootTime = BootTime + 30	# revert back to orignally set Boot Time
	return

def SVOS_Test_Functions():
	global Full_SVOS_PC_Xml, SVOS_INI_FILE
	lib.KnobsIniFile = SVOS_INI_FILE
	lib.PlatformConfigXml = Full_SVOS_PC_Xml
	Status = cli.cliProcessKnobs(Full_SVOS_PC_Xml, SVOS_INI_FILE, lib.CLI_KNOB_RESTORE_MODIFY, 0, 1, 0)
	XmlType = GetType(0)
	if (Status == 1):
		PrintToFile("%d, Prog BOOT to OS flow, FAIL, %s , Append/Prog Knobs Failed " % (Count, XmlType), 1)
		return
	PrintToFile (" SVOS TESTs ")
	XmlCli_Tests(Full_SVOS_PC_Xml)
	Test_LoadDefaults()
	return

def TestAllScripts():
	global Result_File, BIOS_Fetch_file, Count
	Count = 1
	Status = GetCurrBootTime()
	if (Status == False):
		print " Test First Cold Reset resulted in BIOS hang, Aborting! "
		return
	(PltNm, BiosNm, Tstmp) = lib.getBiosDetails()
	FileName = BiosNm.replace('.','_')+'_TmStmp_'+Tstmp.replace('/','_').replace(' at ','_').replace(' Hrs','').replace(':','_')+'.csv'
	BIOS_FileName = BiosNm.replace('.','_')+'_TmStmp_'+Tstmp.replace('/','_').replace(' at ','_').replace(' Hrs','').replace(':','_')+'.bin'
	Result_File = os.sep.join([OutPath, FileName])
	BIOS_Fetch_file= os.sep.join([OutPath, BIOS_FileName])
	print "XmlCli QA results stored in %s" %(Result_File)
	PrintToFile("Platform, %s," %PltNm)
	PrintToFile("BIOS, %s," %BiosNm)
	PrintToFile("Build On, %s," %Tstmp)
	PrintToFile(", !! BIOS Basic Sanity Tests Start!! %s " % (time.ctime()))
	PrintToFile("Test Number , Test Name, Result, XML Type, Comments")
	cmd='''
	powershell -command  "&{ Get-Process | ForEach-Object { if ($_.ProcessName -eq 'putty') { $_.Kill() }}}"
	'''
	os.system(cmd)
	os.system('reg import  %s' %Putty_CpuSv_reg)
	os.system('start /b /d "C:\Program Files (x86)\PuTTY" putty.exe -load MySession')
	CpuSv_Test_Functions()
	cmd='''
	powershell -command  "&{ Get-Process | ForEach-Object { if ($_.ProcessName -eq 'putty') { $_.Kill() }}}"
	'''
	os.system(cmd)
	os.system('reg import  %s' %Putty_SVOS_reg)
	os.system('start /b /d "C:\Program Files (x86)\PuTTY" putty.exe -load MySession')
	SVOS_Test_Functions()
	cmd='''
	powershell -command  "&{ Get-Process | ForEach-Object { if ($_.ProcessName -eq 'putty') { $_.Kill() }}}"
	'''
	os.system(cmd)
	os.system('reg import  %s' %Putty_Misc_reg)
	os.system('start /b /d "C:\Program Files (x86)\PuTTY" putty.exe -load MySession')
	Miscelleneous_Test_Functions()
	PrintToFile(",!! BIOS Basic Sanity Tests End!! %s " % (time.ctime()))
	CleanLogFile(os.sep.join([OutPath, "QaLog.txt"]), os.sep.join([OutPath, "QaLogClean.txt"]))
