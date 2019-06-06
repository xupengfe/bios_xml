#!/usr/bin/env python2.7
__author__ = 'ashinde'
import sys as _sys
import ctypes as _ctypes
from ctypes import *
import cliaccessutil as _cliutil
import time as _time
import binascii as _binascii
import types as _types
########### Code to run @ import time ##############
import os as _os

basepath = _os.getcwd()
SvHifPath = _os.sep.join([_os.path.abspath(_os.path.dirname(__file__)), "SvHif"])
if (_sys.maxsize == 0x7fffffffffffffff):
	HifDllFile=_os.sep.join([SvHifPath, "SvHifWrapper64Bit.dll"])
else:
	HifDllFile=_os.sep.join([SvHifPath, "SvHifWrapper.dll"])
#print HifDllFile
HifDll = _ctypes.CDLL(HifDllFile)

try:
	import common.toolbox as _tools
except ImportError:
	import tools.toolbox as _tools

_log = _tools.getLogger()
_log.setFile("itpiicli.log",dynamic=True)
_log.setFileFormat("simple")
_log.setFileLevel("info")
_log.setConsoleLevel("result")

class svhifAccess(_cliutil.cliaccess):
	def __init__(self):
		super(svhifAccess,self).__init__("svhif")
		self.__dict__["_SvHifStatus"] = 0
		self.__dict__["_SvHifInitLvl"] = 0

	def haltcpu(self, delay=0):
		_time.sleep(delay)
		return 0

	def runcpu(self):
		return 0

	def InitInterface(self):
		self._SvHifInitLvl = self._SvHifInitLvl + 1
		if (self._SvHifStatus == 0):
			_os.chdir(SvHifPath)		# TODO: We cannot do this. The CWD should not be changed
			HifDll.Init()
			HifDll.OpenInterface()
			self._SvHifStatus = 1
		return 0

	def CloseInterface(self):
		if (self._SvHifStatus):
			if (self._SvHifInitLvl):
				self._SvHifInitLvl = self._SvHifInitLvl - 1
			if (self._SvHifInitLvl == 0):
				HifDll.CloseInterface()
				_os.chdir(basepath)		# TODO: We cannot do this. 
				self._SvHifStatus = 0
		return 0

	def warmreset(self):
		HifDll.WriteIo8(0xCF9, 0x06)

	def coldreset(self):
		HifDll.WriteIo8(0xCF9, 0x0E)

	def memBlock(self, address, size):
		result = create_string_buffer('\000' * (size-1))
		HifDll.ReadMemBlock (result, 1, size, address )
		return str(bytearray(result))

	def memsave(self, filename, address, size):
		tmpBuf=self.memBlock(address,size)
		out_file = open(filename, "wb") # opening for writing
		out_file.write(tmpBuf)
		out_file.close()

	def memread(self, address, size):
		buf = create_string_buffer('\000' * (size-1))
		HifDll.ReadMemBlock (buf, 1, size, address )
		return int(_binascii.hexlify(buf.raw[::-1]), 16)

	def memwrite(self, address, size, value):
		buf = create_string_buffer('\000' * (size-1))
		buf.raw = _binascii.unhexlify((hex(value).rstrip("L")[2:]).zfill(size*2))[::-1]
		HifDll.WriteMemBlock(buf, 1, size, address)

	def load_data(self, filename, address):
		in_file = open(filename, "rb") # opening for [r]eading as [b]inary
		data = in_file.read() # if you only wanted to read 512 bytes, do .read(512)
		in_file.close()
		HifDll.WriteMemBlock(data, 1, len(data), address) # list of size entries of 1 Byte

	def readIO(self, address, size):
		return HifDll.ReadIo8(address)

	def writeIO(self, address, size, value):
		HifDll.WriteIo8(address, value)

	def triggerSMI(self, SmiVal):
		self.writeIO(0xB2, 1, SmiVal)

	def ReadMSR(self, Ap, MSR_Addr):
		return 0

	def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
		return 0

	def ReadSmbase(self):
		return 0
