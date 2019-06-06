#!/usr/bin/env python2.7
__author__ = 'ashinde'
from . import cliaccessutil as _cliutil
import time as _time
import binascii as _binascii
import types as _types
import os as _os

########### Code to run @ import time ##############
try:
	import common.toolbox as _tools
except ImportError:
	import tools.toolbox as _tools

_log = _tools.getLogger("itpxmlcli")
_log.setFile("itpxmlcli.log",dynamic=True)
_log.setFileFormat("simple")
_log.setFileLevel("info")
_log.setConsoleLevel("result")

ComItpApiExe = _os.sep.join([_os.path.abspath(_os.path.dirname(__file__)), "SvLegItp\\LegItpComExe.exe"])
LegItpTestOut = _os.sep.join([_os.path.abspath(_os.path.dirname(__file__)), "SvLegItp\\testout.txt"])
def fetchLegItpResult(self, InTxtFile):
	InTxt=open(InTxtFile)
	InTxtList=InTxt.readlines()
	InTxt.close()
	return InTxtList[1].strip().upper()

class itpAccess(_cliutil.cliaccess):
	def __init__(self):
		super(itpAccess,self).__init__("itp")
		self.__dict__["level_Dal"] = 0
		self.__dict__["IsRunning"] = 0x00       # initialize IsRunnning [bitmap] global variable to False for all bits

	def haltcpu(self, delay=0):
		_time.sleep(delay)
		_os.system(r"%s cmd %s \" isrunning \" " %(ComItpApiExe, LegItpTestOut))
		IsLegItpRunning = int(fetchLegItpResult(self, LegItpTestOut) == "TRUE" )
		if(IsLegItpRunning):
			_os.system(r"%s cmd %s \" halt \" " %(ComItpApiExe, "0"))
		return 0

	def runcpu(self):
		_os.system(r"%s cmd %s \" isrunning \" " %(ComItpApiExe, LegItpTestOut))
		IsLegItpRunning = int(fetchLegItpResult(self, LegItpTestOut) == "TRUE" )
		if(IsLegItpRunning):
			DummyVar = 1
		else:
			_os.system(r"%s cmd %s \" go \" " %(ComItpApiExe, "0"))
		return 0

	def InitInterface(self):
		_os.system(r"%s cmd %s \" isrunning \" " %(ComItpApiExe, LegItpTestOut))
		IsLegItpRunning = int(fetchLegItpResult(self, LegItpTestOut) == "TRUE" )
		self.IsRunning = (self.IsRunning & (~(0x1 << self.level_Dal) & 0xFF)) + ((IsLegItpRunning & 0x1) << self.level_Dal )
		self.haltcpu()
		self.level_Dal = self.level_Dal + 1
		return 0

	def CloseInterface(self):
		if ( (self.IsRunning >> (self.level_Dal-1)) & 0x1 ):
			self.runcpu()
		else:
			self.haltcpu()
		self.level_Dal = self.level_Dal - 1
		return 0

	def warmreset(self):
		_os.system(r"%s cmd %s \" reset target \" " %(ComItpApiExe, "0"))

	def coldreset(self):
		_os.system(r"%s cmd %s \" pulsepwrgood \" " %(ComItpApiExe, "0"))

	def memBlock(self, address, size):
		endaddr = address + size
		tmpaddr = address & 0xFFFFF000
		if((endaddr-tmpaddr) < 0x1000):
			_os.system(r"%s cmd %s \" upload %s (0x%X)p length (0x%X) overwrite \" " %(ComItpApiExe, "0", LegItpTestOut, address, size))
			in_file = open(LegItpTestOut, "rb")
			databuffer = in_file.read()
			in_file.close()
		else:
			StartBlkSize = (0x1000 - (address & 0xFFF))
			LegItpPath = _os.path.dirname(LegItpTestOut)
			TmpItpScriptFile = _os.sep.join([LegItpPath, "temp\\TmpItpScript.inc"])
			itpScript_file = open(TmpItpScriptFile, "wb")
			itpScript_file.write("upload %s\\temp\\MemDump_%d%s (0x%X)p length (0x%X) overwrite \r\n"  %(LegItpPath, (0), ".txt", address, StartBlkSize))
			address = (address + StartBlkSize)
			LastBlkSize = (endaddr & 0xFFF)
			MidFourKBlks = (((endaddr & 0xFFFFF000) - address) / 0x1000 )
			for blkcnt in range(0x0,(MidFourKBlks),1):
				itpScript_file.write("upload %s\\temp\\MemDump_%d%s (0x%X)p length (0x%X) overwrite \r\n"  %(LegItpPath, (blkcnt+1), ".txt", address, 0x1000))
				address = (address + 0x1000)
			if (LastBlkSize != 0):
				itpScript_file.write("upload %s\\temp\\MemDump_%d%s (0x%X)p length (0x%X) overwrite \r\n"  %(LegItpPath, (MidFourKBlks+1), ".txt", address, LastBlkSize))
				address = (address + LastBlkSize)
			itpScript_file.close()
			_os.system(r"%s script %s" %(ComItpApiExe, TmpItpScriptFile))
			ComBineFilesBat = _os.sep.join([LegItpPath, "CombineFiles.bat"])
			FinalDumpFile = _os.sep.join([LegItpPath, "temp\\MemDumpFinal.bin"])
			_os.system(r"%s %s %s %d" %(ComBineFilesBat, _os.path.dirname(FinalDumpFile), FinalDumpFile, (MidFourKBlks+1) ) )
			in_file = open(FinalDumpFile, "rb")
			databuffer = in_file.read()
			in_file.close()
		return databuffer

	def memsave(self, filename, address, size):
		tmpBuf = self.memBlock(address,size)
		out_file = open(filename, "wb") # opening for writing
		out_file.write(tmpBuf)
		out_file.close()

	def memread(self, address, size):
		if (size == 8):
			_os.system(r"%s cmd %s \" printf(\"0x%%X%%X\n\", ord4 (0x%X+4)p, ord4 (0x%X)p) \" " %(ComItpApiExe, LegItpTestOut, address, address))
		else:
			_os.system(r"%s cmd %s \" printf(\"0x%%X\n\", ord%d (0x%X)p) \" " %(ComItpApiExe, LegItpTestOut, size, address))
		return int(fetchLegItpResult(self, LegItpTestOut), 16)

	def memwrite(self, address, size, value):
		_os.system(r"%s cmd %s \" ord%d (0x%X)p = 0x%X \" " %(ComItpApiExe, "0", size, address, value))

	def load_data(self, filename, address):
		_os.system(r"%s cmd %s \" load %s at (0x%X)p \" " %(ComItpApiExe, "0", filename, address))

	def readIO(self, address, size):
		if (size == 1):
			_os.system(r"%s cmd %s \" port(0x%X) \" " %(ComItpApiExe, LegItpTestOut, address))
		elif (size == 2):
			_os.system(r"%s cmd %s \" wport(0x%X) \" " %(ComItpApiExe, LegItpTestOut, address))
		elif (size == 4):
			_os.system(r"%s cmd %s \" dport(0x%X) \" " %(ComItpApiExe, LegItpTestOut, address))
		else:
			return 0
		return int(fetchLegItpResult(self, LegItpTestOut), 16)

	def writeIO(self, address, size, value):
		if (size == 1):
			_os.system(r"%s cmd %s \" port(0x%X) = 0x%X \" " %(ComItpApiExe, "0", address, value))
		elif (size == 2):
			_os.system(r"%s cmd %s \" wport(0x%X) = 0x%X \" " %(ComItpApiExe, "0", address, value))
		elif (size == 4):
			_os.system(r"%s cmd %s \" dport(0x%X) = 0x%X \" " %(ComItpApiExe, "0", address, value))

	def triggerSMI(self, SmiVal):
		self.haltcpu()
		self.writeIO(0xB2, 1, SmiVal)
		self.runcpu()

	def ReadMSR(self, Ap, MSR_Addr):
		return self.itp.threads[Ap].msr(MSR_Addr)

	def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
		return self.itp.threads[Ap].msr(MSR_Addr, MSR_Val)

	def ReadSmbase(self):
		self.haltcpu()
		return self.thread.msr(0x171)
