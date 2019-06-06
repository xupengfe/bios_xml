#!/usr/bin/env python2.7
__author__ = 'ashinde'
from . import cliaccessutil as _cliutil
import binascii as _binascii
import types as _types
import ctypes as _ctypes
from ctypes import *

########### Code to run @ import time ##############
HwApiDll = _ctypes.CDLL(r"C:\Python27\Lib\site-packages\ssa\HWAPIDLL.dll")

class winssaAccess(_cliutil.cliaccess):
	def __init__(self):
		super(winssaAccess,self).__init__("winssa")
		self.__dict__["_winssaStatus"] = 0
		self.__dict__["_winssaInitLvl"] = 0

	def haltcpu(self, delay=0):
		return 0

	def runcpu(self):
		return 0

	def InitInterface(self):
		self._winssaInitLvl = self._winssaInitLvl + 1
		if (self._winssaStatus == 0):
			RetStatus = HwApiDll.pyHWAPIInitialize()
			self._winssaStatus = 1
			if (RetStatus != 1):
				return 1
		return 0

	def CloseInterface(self):
		if (self._winssaStatus):
			if (self._winssaInitLvl):
				self._winssaInitLvl = self._winssaInitLvl - 1
			if (self._winssaInitLvl == 0):
				RetStatus = HwApiDll.pyHWAPITerminate()
				self._winssaStatus = 0
				if (RetStatus != 1):
					return 1
		return 0

	def warmreset(self):
		Tmpbuf = ['\x01', '\x00', '\x00', '\x00', '\x06']
		Status = HwApiDll.pyWritePort(0xCF9, Tmpbuf)
		if (Status != 1):	# Retry
			HwApiDll.pyWritePort(0xCF9, Tmpbuf)

	def coldreset(self):
		Tmpbuf = ['\x01', '\x00', '\x00', '\x00', '\x0E']
		Status = HwApiDll.pyWritePort(0xCF9, Tmpbuf)
		if (Status != 1):	# Retry
			HwApiDll.pyWritePort(0xCF9, Tmpbuf)

	def memBlock(self, address, size):
		Tmpbuf = create_string_buffer('\000' * (4+size-1))	# initialize the Read Buffer
		Tmpbuf[0:4] = [chr(size & 0xFF), chr((size >> 8) & 0xFF), chr((size >> 16) & 0xFF), chr((size >> 24) & 0xFF)]    # initialize the read size
		if address < 0x1000:
			offset = 0
			addr = address
		else:
			offset = address & 0x0000000000000FFF
			addr = address & 0xFFFFFFFFFFFFF000
		Status = HwApiDll.pyPCIMMIORead(addr, offset, Tmpbuf)
		if (Status != 1):	# Retry
			HwApiDll.pyPCIMMIORead(addr, offset, Tmpbuf)
		return Tmpbuf[4:(4+size)]

	def memsave(self, filename, address, size):
		tmpBuf=self.memBlock(address,size)
		out_file = open(filename, "wb") # opening for writing
		out_file.write(tmpBuf)
		out_file.close()

	def memread(self, address, size):
		Tmpbuf = create_string_buffer('\000' * (4+size-1))	# initialize the Read Buffer
		Tmpbuf[0:4] = [chr(size & 0xFF), chr((size >> 8) & 0xFF), chr((size >> 16) & 0xFF), chr((size >> 24) & 0xFF)]    # initialize the read size
		if address < 0x1000:
			offset = 0
			addr = address
		else:
			offset = address & 0x0000000000000FFF
			addr = address & 0xFFFFFFFFFFFFF000
		Status = HwApiDll.pyPCIMMIORead(addr, offset, Tmpbuf)
		if (Status != 1):	# Retry
			HwApiDll.pyPCIMMIORead(addr, offset, Tmpbuf)
		return int(_binascii.hexlify(Tmpbuf.raw[4:(4+size)][::-1]), 16)

	def memwrite(self, address, size, value):
		Tmpbuf = create_string_buffer('\000' * (4+size-1))	# initialize the Write Buffer
		Tmpbuf[0:4] = [chr(size & 0xFF), chr((size >> 8) & 0xFF), chr((size >> 16) & 0xFF), chr((size >> 24) & 0xFF)]    # initialize the read size
		Tmpbuf[4:(4+size)] = [chr(value & 0xFF), chr((value >> 8) & 0xFF), chr((value >> 16) & 0xFF), chr((value >> 24) & 0xFF), chr((value >> 32) & 0xFF), chr((value >> 40) & 0xFF), chr((value >> 48) & 0xFF), chr((value >> 56) & 0xFF)] [0:size]   # initialize the write Value
		if address < 0x1000:
			offset = 0
			addr = address
		else:
			offset = address & 0x0000000000000FFF
			addr = address & 0xFFFFFFFFFFFFF000
		Status = HwApiDll.pyPCIMMIOWrite(addr, offset, Tmpbuf)
		if (Status != 1):	# Retry
			HwApiDll.pyPCIMMIOWrite(addr, offset, Tmpbuf)

	def load_data(self, filename, address):
		in_file = open(filename, "rb") # opening for [r]eading as [b]inary
		data = in_file.read()
		in_file.close()
		Size = len(data)
		Tmpbuf = [chr(Size & 0xFF), chr((Size >> 8) & 0xFF), chr((Size >> 16) & 0xFF), chr((Size >> 24) & 0xFF)]    # initialize the read size
		Loadbuf = str(bytearray(Tmpbuf)) + data
		if address < 0x1000:
			offset = 0
			addr = address
		else:
			offset = address & 0x0000000000000FFF
			addr = address & 0xFFFFFFFFFFFFF000
		Status = HwApiDll.pyPCIMMIOWrite(addr, offset, Loadbuf)
		if (Status != 1):	# Retry
			HwApiDll.pyPCIMMIOWrite(addr, offset, Loadbuf)

	def readIO(self, address, size):
		Tmpbuf = create_string_buffer('\000' * (4+size-1))	# initialize the Read Buffer
		Tmpbuf[0:4] = [chr(size & 0xFF), chr((size >> 8) & 0xFF), chr((size >> 16) & 0xFF), chr((size >> 24) & 0xFF)]    # initialize the read size
		Status = HwApiDll.pyReadPort(address, Tmpbuf)
		if (Status != 1):	# Retry
			HwApiDll.pyReadPort(address, Tmpbuf)
		return int(_binascii.hexlify(Tmpbuf.raw[4:(4+size)][::-1]), 16)

	def writeIO(self, address, size, value):
		Tmpbuf = create_string_buffer('\000' * (4+size-1))	# initialize the Write Buffer
		Tmpbuf[0:4] = [chr(size & 0xFF), chr((size >> 8) & 0xFF), chr((size >> 16) & 0xFF), chr((size >> 24) & 0xFF)]    # initialize the read size
		Tmpbuf[4:(4+size)] = [chr(value & 0xFF), chr((value >> 8) & 0xFF), chr((value >> 16) & 0xFF), chr((value >> 24) & 0xFF)] [0:size]   # initialize the write Value
		Status = HwApiDll.pyWritePort(address, Tmpbuf)
		if (Status != 1):	# Retry
			HwApiDll.pyWritePort(address, Tmpbuf)

	def triggerSMI(self, SmiVal):
		self.writeIO(0xB2, 1, SmiVal)

	def ReadMSR(self, Ap, MSR_Addr):
		Tmpbuf = create_string_buffer('\000' * (20-1))	# initialize the Write Buffer
		Tmpbuf[4:8] = [chr(Ap & 0xFF), chr(0), chr(0), chr(0)]  # initialize the AP Index
		Tmpbuf[8:12] = [chr(MSR_Addr & 0xFF), chr((MSR_Addr >> 8) & 0xFF), chr((MSR_Addr >> 16) & 0xFF), chr((MSR_Addr >> 24) & 0xFF)]   # initialize the MSR
		Status = HwApiDll.pyReadMSR(Tmpbuf)
		if (Status != 1):	# Retry
			HwApiDll.pyReadMSR(Tmpbuf)
		return int(_binascii.hexlify((Tmpbuf.raw[16:20]+Tmpbuf.raw[12:16])[::-1]), 16)

	def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
		Tmpbuf = create_string_buffer('\000' * (20-1))	# initialize the Write Buffer
		Tmpbuf[4:8] = [chr(Ap & 0xFF), chr(0), chr(0), chr(0)]  # initialize the AP Index
		Tmpbuf[8:12] = [chr(MSR_Addr & 0xFF), chr((MSR_Addr >> 8) & 0xFF), chr((MSR_Addr >> 16) & 0xFF), chr((MSR_Addr >> 24) & 0xFF)]   # initialize the MSR
		Tmpbuf[12:16] = [chr((MSR_Val >> 32) & 0xFF), chr((MSR_Val >> 40) & 0xFF), chr((MSR_Val >> 48) & 0xFF), chr((MSR_Val >> 56) & 0xFF)]   # initialize the MSR Val (High)
		Tmpbuf[16:20] = [chr(MSR_Val & 0xFF), chr((MSR_Val >> 8) & 0xFF), chr((MSR_Val >> 16) & 0xFF), chr((MSR_Val >> 24) & 0xFF)]   # initialize the MSR Val (Low)
		Status = HwApiDll.pyWriteMSR(Tmpbuf)
		if (Status != 1):	# Retry
			HwApiDll.pyWriteMSR(Tmpbuf)
		return 0

	def ReadSmbase(self):
		return 0
