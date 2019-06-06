#!/usr/bin/env python2.7
__author__ = 'ashinde'
from . import cliaccessutil as _cliutil
import binascii as _binascii
import types as _types

########### Code to run @ import time ##############
import sys, os
refPath = os.path.abspath(os.path.dirname(__file__))
RwExe = os.sep.join([refPath, "win", "Rw.exe"])
TmpDataFile = os.sep.join([refPath, "win", "TmpData.bin"])
ResOutFile = os.sep.join([refPath, "win", "ResOut.txt"])

class winrweAccess(_cliutil.cliaccess):
	def __init__(self):
		super(winrweAccess,self).__init__("winrwe")

	def haltcpu(self, delay=0):
		return 0

	def runcpu(self):
		return 0

	def InitInterface(self):
		return 0

	def CloseInterface(self):
		return 0

	def warmreset(self):
		os.system('%s /Nologo /Min /Command="O 0xCF9 0x06; RwExit"' %RwExe)

	def coldreset(self):
		os.system('%s /Nologo /Min /Command="O 0xCF9 0x0E; RwExit"' %RwExe)

	def memBlock(self, address, size):
		os.system('%s /Nologo /Min /Command="SAVE %s Memory 0x%X 0x%X; RwExit"' %(RwExe, TmpDataFile, address, size))
		TmpFile = open(TmpDataFile, "rb")
		DataBuff = TmpFile.read()
		TmpFile.close()
		return DataBuff

	def memsave(self, filename, address, size):
		os.system('%s /Nologo /Min /Command="SAVE %s Memory 0x%X 0x%X; RwExit"' %(RwExe, filename, address, size))

	def memread(self, address, size):
		os.system('%s /Nologo /Min /Command="SAVE %s Memory 0x%X 0x%X; RwExit"' %(RwExe, TmpDataFile, address, size))
		TmpFile = open(TmpDataFile, "rb")
		DataBuff = TmpFile.read()
		TmpFile.close()
		return int(_binascii.hexlify(DataBuff[0:size][::-1]), 16)

	def memwrite(self, address, size, value):
		if (size == 1):
			os.system('%s /Nologo /Min /Command="W 0x%X 0x%X; RwExit"' %(RwExe, address, value))
		elif (size == 2):
			os.system('%s /Nologo /Min /Command="W16 0x%X 0x%X; RwExit"' %(RwExe, address, value))
		elif (size == 4):
			os.system('%s /Nologo /Min /Command="W32 0x%X 0x%X; RwExit"' %(RwExe, address, value))
		elif (size == 8):
			os.system('%s /Nologo /Min /Command="W32 0x%X 0x%X; W32 0x%X 0x%X; RwExit"' %(RwExe, address, (value & 0xFFFFFFFF), (address+4), (value >> 32)))

	def load_data(self, filename, address):
		os.system('%s /Nologo /Min /Command="LOAD %s Memory 0x%X; RwExit"' %(RwExe, filename, address))

	def readIO(self, address, size):
		if (size == 1):
			os.system('%s /Nologo /Min /LogFile=%s /Command="I 0x%X; RwExit"' %(RwExe, ResOutFile, address))
		elif (size == 2):
			os.system('%s /Nologo /Min /LogFile=%s /Command="I16 0x%X; RwExit"' %(RwExe, ResOutFile, address))
		elif (size == 4):
			os.system('%s /Nologo /Min /LogFile=%s /Command="I32 0x%X; RwExit"' %(RwExe, ResOutFile, address))
		TmpFile = open(ResOutFile, "r")
		Result = TmpFile.read()
		TmpFile.close()
		tmpstr = Result.split('=')
		if(tmpstr[0].strip() == "In Port 0x%X" %address):
			return int(tmpstr[1].strip(), 16)
		else:
			return 0

	def writeIO(self, address, size, value):
		if (size == 1):
			os.system('%s /Nologo /Min /Command="O 0x%X 0x%X; RwExit"' %(RwExe, address, value))
		elif (size == 2):
			os.system('%s /Nologo /Min /Command="O16 0x%X 0x%X; RwExit"' %(RwExe, address, value))
		elif (size == 4):
			os.system('%s /Nologo /Min /Command="O32 0x%X 0x%X; RwExit"' %(RwExe, address, value))

	def triggerSMI(self, SmiVal):
		os.system('%s /Nologo /Min /Command="O 0x%X 0x%X; RwExit"' %(RwExe, 0xB2, SmiVal))

	def ReadMSR(self, Ap, MSR_Addr):
		return 0

	def WriteMSR(self, Ap, MSR_Addr, MSR_Val):
		return 0

	def ReadSmbase(self):
		return 0
