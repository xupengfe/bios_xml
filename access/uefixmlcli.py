#!/usr/bin/env python2.7
__author__ = 'ashinde'
from . import cliaccessutil as _cliutil
import binascii as _binascii
import types as _types
import ctypes as _ctypes
from ctypes import *
import CCBHWApi as HwApi
import CCBBaseTypes as bt

########### Code to run @ import time ##############

class uefiAccess(_cliutil.cliaccess):
	def __init__(self):
		super(uefiAccess,self).__init__("uefi")
		self.__dict__["_HwApiStatus"] = 0
		self.__dict__["_HwApiInitLvl"] = 0

	def haltcpu(self, delay=0):
		return 0

	def runcpu(self):
		return 0

	def InitInterface(self):
		self._HwApiInitLvl = self._HwApiInitLvl + 1
		if (self._HwApiStatus == 0):
			RetStatus = HwApi.HWAPIInitialize()
			self._HwApiStatus = 1
			if (RetStatus != 1):
				return 1
		return 0

	def CloseInterface(self):
		if (self._HwApiStatus):
			if (self._HwApiInitLvl):
				self._HwApiInitLvl = self._HwApiInitLvl - 1
			if (self._HwApiInitLvl == 0):
				RetStatus = HwApi.HWAPITerminate()
				self._HwApiStatus = 0
				if (RetStatus != 1):
					return 1
		return 0

	def warmreset(self):
		de = bytearray(1)
		de[0]=0x06
		Status = HwApi.WritePort(0xCF9, 1, de)
		if (Status != 1):	# Retry
			HwApi.WritePort(0xCF9, 1, de)

	def coldreset(self):
		de = bytearray(1)
		de[0] = 0x0E
		Status = HwApi.WritePort(0xCF9, 1, de)
		if (Status != 1):	# Retry
			HwApi.WritePort(0xCF9, 1, de)

	def memBlock(self, address, size):
		DataEleObj=bytearray(size);
		Status = HwApi.ReadMMIO(address,0x0000,size,DataEleObj)
		if (Status != 1):	# Retry
			Status = HwApi.ReadMMIO(address,0x0000,size,DataEleObj)
		data = str(DataEleObj)
		return data

	def memsave(self, filename, address, size):
		tmpBuf=self.memBlock(address,size)
		out_file = open(filename, "wb") # opening for writing
		out_file.write(tmpBuf)
		out_file.close()

	def memread(self, address, size):
		DataEleObj=bytearray(size);
		Status = HwApi.ReadMMIO(address,0x0000,size,DataEleObj)
		if (Status != 1):	# Retry
			Status = HwApi.ReadMMIO(address,0x0000,size,DataEleObj)
		if size == 1:
			data = DataEleObj[0]
		elif size == 2:
			data = DataEleObj[0] | DataEleObj[1] << 8
		elif size == 4:
			data = DataEleObj[0] | DataEleObj[1] << 8 | DataEleObj[2] << 16 | DataEleObj[3] << 24
		else:
			data = DataEleObj[0] | DataEleObj[1] << 8 | DataEleObj[2] << 16 | DataEleObj[3] << 24 | DataEleObj[4] << 32 | DataEleObj[5] << 40 | DataEleObj[6] << 48 | DataEleObj[7] << 56
		return data

	def memwrite(self, address, size, value):
		# assumption here is that the memwrite is always used to write max 8 bytes of data
		datalist=[(value & 0xFF), ((value >> 8) & 0xFF), ((value >> 16) & 0xFF), ((value >> 24) & 0xFF), ((value >> 32) & 0xFF), ((value >> 40) & 0xFF), ((value >> 48) & 0xFF), ((value >> 56) & 0xFF)] [0:size]
		databytes=bytearray(datalist)
		Status = HwApi.WriteMMIO(address, 0x0000, size, databytes)
		if (Status != 1):	# Retry
			HwApi.WriteMMIO(address, 0x0000, size, databytes)

	def load_data(self, filename, address):
		in_file = open(filename, "rb") # opening for [r]eading as [b]inary
		data = in_file.read()
		in_file.close()
		Size = len(data)
		databytes = bytearray(data)
		Status = HwApi.WriteMMIO(address, 0x0000, Size, databytes)
		if (Status != 1):	# Retry
			HwApi.WriteMMIO(address, databytes)

	def readIO(self, address, size):
		de = bytearray(size)
		Status = HwApi.ReadPort(address, size, de)
		if (Status != 1):	# Retry
			HwApi.ReadPort(address, size, de)
		data = 0
		if size == 1:
			data = de[0]
		elif size == 2:
			data = de[0] | de[1] << 8
		elif size == 4:
			data = de[0] | de[1] << 8 | de[2] << 16 | de[3] << 24
		return data

	def writeIO(self, address, size, value):
		de = bytearray(size)
		if size == 1:
			de[0] = value & 0xFF
		elif size == 2:
			de[0] = value & 0xFF 
			de[1] = (value >> 8) & 0xFF
		elif size == 4:
			de[0] = value & 0xFF 
			de[1] = (value >> 8) & 0xFF
			de[2] = (value >> 16) & 0xFF
			de[3] = (value >> 24) & 0xFF
		Status = HwApi.WritePort(address, size, de)
		if (Status != 1):	# Retry
			HwApi.WritePort(address, size, de)

	def triggerSMI(self, SmiVal):
		self.writeIO(0xB2, 1, SmiVal)

	def ReadMSR(self, Ap, MSR_Addr):
		MsrInfo = bt.MSRInfoBlock()
		MsrInfo.CPU = Ap
		MsrInfo.MSR = MSR_Addr
		Status = HwApi.ReadMSR(MsrInfo)
		if (Status != 1):	# Retry
			HwApi.ReadMSR(MsrInfo)
		return int(((MsrInfo.HiContent & 0xFFFFFFFF) << 32) | (MsrInfo.LoContent & 0xFFFFFFFF))

	def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
		MsrInfo = bt.MSRInfoBlock()
		MsrInfo.CPU = Ap
		MsrInfo.MSR = MSR_Addr
		MsrInfo.HiContent = (MSR_Val >> 32) & 0xFFFFFFFF
		MsrInfo.LoContent = (MSR_Val & 0xFFFFFFFF)
		Status = HwApi.WriteMSR(MsrInfo)
		if (Status != 1):	# Retry
			HwApi.WriteMSR(MsrInfo)
		return 0

	def ReadSmbase(self):
		return 0
