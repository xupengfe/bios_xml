#!/usr/bin/env python2.7
__author__ = 'ashinde'
from . import cliaccessutil as _cliutil
import binascii as _binascii
import types as _types

########### Code to run @ import time ##############

class svosAccess(_cliutil.cliaccess):
	def __init__(self):
		super(svosAccess,self).__init__("svos")
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
		endaddr = address + size
		tmpaddr = address & 0xFFFFF000
		if((endaddr-tmpaddr) < 0x1000):
			result = self._base.memblock(address, 1, size)
		else:
			BlockSize =( ((address + size) & 0xFFFFF000) - address)
			remainderblockSize = size - BlockSize
			result=self._base.memblock(address, 1, BlockSize)
			result2=self._base.memblock(address + BlockSize, 1, remainderblockSize)
			result.extend(result2)
		return str(bytearray(result))

	def memsave(self, filename, address, size):
		tmpBuf=self.memBlock(address,size)
		out_file = open(filename, "wb") # opening for writing
		out_file.write(tmpBuf)
		out_file.close()

	def memread(self, address, size):
		Value=0
		for count in range (0, size):
			Value = Value + (self._base.mem(address+count, 1) << (count*8))
		return Value

	def memwrite(self, address, size, value):
		for count in range (0, size):
			Val = (value >> (count*8)) & 0xFF
			self._base.mem(address+count, 1, Val) 

	def load_data(self, filename, address):
		in_file = open(filename, "rb") # opening for [r]eading as [b]inary
		data = in_file.read() # if you only wanted to read 512 bytes, do .read(512)
		in_file.close()
		self._base.memblock(address, 1, map(lambda x: int(_binascii.hexlify(x),16), list(data))) # list of size entries of 1 Byte

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
