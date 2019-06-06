#!/usr/bin/env python2.7
__author__ = 'ashinde'
from . import cliaccessutil as _cliutil
import binascii as _binascii
import types as _types

########### Code to run @ import time ##############

class simicsAccess(_cliutil.cliaccess):
	def __init__(self):
		super(simicsAccess,self).__init__("simics")
		import common.baseaccess as _access
		self.__dict__["_base"]=_access.getglobalbase()

	def haltcpu(self, delay=0):
		return 0

	def runcpu(self):
		return 0

	def InitInterface(self):
		return 0

	def CloseInterface(self):
		return 0

	def warmreset(self):
		self._base.io(0xCF9, 1, 0x06)

	def coldreset(self):
		self._base.io(0xCF9, 1, 0x0E)

	def memBlock(self, address, size):
		result = ''
		for blksize in range(0 , size/0x400):
			tempresult = self._base.memblock(address+(blksize*0x400), 0x400)
			result += _binascii.unhexlify(hex(tempresult).strip('L')[2::].zfill(2*0x400))[::-1]
		if size % 0x400 != 0x0:
			tempresult = self._base.memblock(address + (size/0x400)*0x400, size % 0x400)
			result += _binascii.unhexlify(hex(tempresult).strip('L')[2::].zfill(2*(size % 0x400)))[::-1]
		return result

	def memsave(self, filename, address, size):
		tmpBuf=self.memBlock(address,size)
		out_file = open(filename, "wb") # opening for writing
		out_file.write(tmpBuf)
		out_file.close()

	def memread(self, address, size):
		return self._base.mem(address, size) # list of size entries of 1 Byte

	def memwrite(self, address, size, value):
		self._base.mem(address, size, value) # list of size entries of 1 Byte

	def load_data(self, filename, address):
		in_file = open(filename, "rb") # opening for [r]eading as [b]inary
		data = in_file.read() # if you only wanted to read 512 bytes, do .read(512)
		in_file.close()
		temp = int(_binascii.hexlify(data[::-1]) , 16)
		self._base.memblock(address, len(list(data)), [temp])

	def readIO(self, address, size):
		return self._base.io(address, size)

	def writeIO(self, address, size, value):
		self._base.io(address, size, value)

	def triggerSMI(self, SmiVal):
		self.writeIO(0xB2, 1, SmiVal)

	def ReadMSR(self, Ap, MSR_Addr):
		return self._base.msr(MSR_Addr)

	def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
		return self._base.msr(MSR_Addr, MSR_Val)

	def ReadSmbase(self):
		return self._base.msr(0x171)
