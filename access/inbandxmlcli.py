#!/usr/bin/enve python2.7
__author__ = 'Hongqi Tian'
from . import cliaccessutil as _cliutil
import binascii as _binascii
from common import baseaccess as _baseaccess

########### Code to run @ import time ##############  

class inbandAccess(_cliutil.cliaccess):
	def __init__(self):
		super(inbandAccess, self).__init__("tssa")
		#self.__dict__["_inband"] = None
		if _baseaccess.getaccess() == "tssa":
			#self._inband = _baseaccess.getglobalbase()
			self.__dict__["_inband"] = _baseaccess.getglobalbase()
		else:
			self._inband = None

	def haltcpu(self, delay=0):
		return 0

	def runcpu(self):
		return 0

	def InitInterface(self):
		return 0

	def CloseInterface(self):
		return 0

	def warmreset(self):
		self._inband.io(0xCF9, 1, 0x06)

	def coldreset(self):
		self._inband.io(0xCF9, 1, 0x0E)

	def memBlock(self, address, size):
		if(size <= 0x1000):
			result = self._inband.memblock(address, 1, size)
		else:
			Remainder = size % 0x1000
			FourKBlks = size / 0x1000
			result = self._inband.memblock(address, 1, 0x1000)
			for blkcnt in range(0x1, FourKBlks, 1):
				result = result + self._inband.memblock(address + blkcnt * 0x1000, 1, 0x1000)
			if (Remainder > 0):
				result = result + self._inband.memblock(address + size - Remainder, 1, Remainder)
		return str(bytearray(result)) 

	def memread(self, address, size):
		return self._inband.mem(address, size)

	def memwrite(self, address, size, value):
		self._inband.mem(address, size, value)

	def memsave(self, filename, address, size):
		tempBuf = self.memBlock(address, size)
		tempBuf = str(bytearray(tempBuf))
		with open(filename, "wb") as out_file:
			out_file.write(tempBuf)

	def load_data(self, filename, address):
		with open(filename, "rb") as in_file:
			data = in_file.read()
		self._inband.memblock(address, 1, map(lambda x: int(_binascii.hexlify(x), 16), list(data))) 

	def readIO(self, address, size):
		return self._inband.io(address, size)

	def writeIO(self, address, size, value):
		self._inband.io(address, size, value)

	def triggerSMI(self, SmiVal):
		self.writeIO(0xB2, 1, SmiVal)

	def ReadMSR(self, Ap, MSR_Addr):
		return self._inband.msr(MSR_Addr)

	def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
		return self._inband.msr(MSR_Addr, MSR_Val)

	def ReadSmbase(self):
		return self._inband.msr(0x171)
