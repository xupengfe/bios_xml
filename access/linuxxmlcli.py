#!/usr/bin/env python2.7
__author__ = 'ashinde'
from . import cliaccessutil as _cliutil
import binascii as _binascii
import types as _types
import Linux.linux_mem_port as lmp

########### Code to run @ import time ##############

class linuxAccess(_cliutil.cliaccess):
	def __init__(self):
		super(linuxAccess,self).__init__("linux")

	def haltcpu(self, delay=0):
		return 0

	def runcpu(self):
		return 0

	def InitInterface(self):
		return 0

	def CloseInterface(self):
		return 0

	def warmreset(self):
		lmp.io(0xCF9, 1, 0x06)

	def coldreset(self):
		lmp.io(0xCF9, 1, 0x0E)

	def memBlock(self, address, size):
		endaddr = address + size
		tmpaddr = address & 0xFFFFF000
		result1 = []
		if((endaddr-tmpaddr) <= 0x1000):
			result = lmp.memBlock(address, size)
			result1.extend(result)
		else:
			FirstEndPageAddr = (address + 0xFFF) & 0xFFFFF000
			if(FirstEndPageAddr > address):
				result=lmp.memBlock(address, (FirstEndPageAddr-address))
				result1.extend(result)
			blkCount = 0
			BlockSize = (endaddr - FirstEndPageAddr)
			for blkCount in range (0, (BlockSize/0x1000)):
				result=lmp.memBlock(FirstEndPageAddr+(blkCount*0x1000), 0x1000)
				result1.extend(result)
			if(BlockSize%0x1000):
				result=lmp.memBlock(FirstEndPageAddr+((blkCount+1)*0x1000), (BlockSize%0x1000))
				result1.extend(result)
		return str(bytearray(result1))

	def memsave(self, filename, address, size):
		tmpBuf=self.memBlock(address,size)
		out_file = open(filename, "wb") # opening for writing
		out_file.write(tmpBuf)
		out_file.close()

	def memread(self, address, size):
		return lmp.mem(address, size) # list of size entries of 1 Byte

	def memwrite(self, address, size, value):
		lmp.mem(address, size, value) # list of size entries of 1 Byte

	def load_data(self, filename, address):
		in_file = open(filename, "rb") # opening for [r]eading as [b]inary
		data = in_file.read() # if you only wanted to read 512 bytes, do .read(512)
		size = len(data)
		in_file.close()
		lmp.memBlock(address, size, data) # list of size entries of 1 Byte

	def readIO(self, address, size):
		return lmp.io(address, size)

	def writeIO(self, address, size, value):
		lmp.io(address, size, value)

	def triggerSMI(self, SmiVal):
		lmp.io(0xB2, 1, SmiVal)

	def ReadMSR(self, Ap, MSR_Addr):
		return 0

	def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
		return 0

	def ReadSmbase(self):
		return 0
